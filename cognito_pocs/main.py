from cgitb import reset
import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel, EmailStr, validator
from typing import Optional

config = {'COGNITO_POOL_ID': 'us-east-1_D9vqK4FpM', 'COGNITO_CLIENT_ID' : '4fo3t3u726t5vn97jglfi30cri'}
#config = {'COGNITO_POOL_ID': 'us-east-1_LxihYDvuO', 'COGNITO_CLIENT_ID' : '7hdito2a1fk2pbci2n8cmferhl'}

class Me(BaseModel):
    id: str
    nickname: str
    email: EmailStr
    new_access_token: Optional[str]
    access_token: Optional[str]
    refresh_token:Optional[str]

class UserAttribute(BaseModel):
    email: EmailStr
    attribute: str
    value: str

class UserAuthenticate(BaseModel):
    email: str
    password: str

class UserEmails(BaseModel):
    afc_email:str
    andresfelipe25_email: str
    afr_email: str

class NewUser(UserAuthenticate):
    nickname: str

class UserConfirmForgotPassword(BaseModel):
    email: str
    password: str
    confirm_code: str

class AuthenticateChallenge(BaseModel):
    name: Optional[str]
    email: Optional[str]
    password: Optional[str]
    session: Optional[str]
    class Config:
        schema_extra = {
            'example': {
                'email': 'user@integrichain.com',
                'password': 'Ichain@123',
                'session': 'the session value returned by the Login resource'
            }
        }


def admin_reset_password(user: UserAuthenticate):
    client.admin_reset_user_password(
        UserPoolId='us-east-1_96W9wQYyD',
        Username=user.email
    )

def forgot_password(user: UserAuthenticate):
    client.forgot_password(
        ClientId='2tkc5hlarek9mnfecigi627sa7',
        Username=user.email
    )

def confirm_forgot_password(user: UserConfirmForgotPassword):
    client.confirm_forgot_password(
        ClientId='2tkc5hlarek9mnfecigi627sa7',
        Username=user.email,
        ConfirmationCode=user.confirm_code,
        Password=user.password
    )

def new_user(user: NewUser):
    client.admin_create_user(
        UserPoolId=config['COGNITO_POOL_ID'],
        Username=user.email,
        TemporaryPassword=user.password,
        UserAttributes=[
            {
                'Name': 'nickname',
                'Value': user.nickname
            },
            {
                'Name': 'email',
                'Value': user.email
            },
            {
                'Name': 'email_verified',
                'Value': 'true'
            }
        ]
    )


def authenticate(user: UserAuthenticate):
    try:
        print(f'&&&&&&&&&&&&&&&&&&&{user}&&&&&&&&&&&&&&&')
        authenticate_response = {}
        authenticate_response = client.initiate_auth(
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': user.email,
                'PASSWORD': user.password
            },
            ClientId= config.get('COGNITO_CLIENT_ID')
        )
        return authenticate_response
    except Exception as ex:
        print(str(ex))
        raise ex




def authenticate_challenge(challenge: AuthenticateChallenge):
    authenticate_response = {}

    cognito_response = client.admin_respond_to_auth_challenge(
        UserPoolId=config['COGNITO_POOL_ID'],
        ClientId=config['COGNITO_CLIENT_ID'],
        ChallengeName= challenge.name,
        ChallengeResponses={'NEW_PASSWORD': challenge.password, 'USERNAME': challenge.email},
        Session=challenge.session
    )
    return cognito_response

def update_user_attributes(user: UserAttribute):
    return client.admin_update_user_attributes(
        UserPoolId='us-east-1_96W9wQYyD',
        Username=user.email,
        UserAttributes=[
            {
                'Name': user.attribute,
                'Value': user.value
            }
        ]
    )

def get_new_access_token(refresh_token: str):
    response = client.initiate_auth(
        ClientId=config['COGNITO_CLIENT_ID'],
        AuthFlow='REFRESH_TOKEN_AUTH',
        AuthParameters={
            'REFRESH_TOKEN': refresh_token
        }
    )

def get_user_info(access_token: str, refresh_token: str):
    user_id = None
    nickname = None
    email = None
    new_access_token = None
    try:
        response = client.get_user(AccessToken=access_token)
        print(f"USER INFO RAW RESPONSE: {response}")
    except ClientError as e:
        print(f'CLIENT ERROR: {str(e)}')
        if e.response.get('message') == 'Access Token has expired':
            print(f'AUTH ERROR: {str(e)}')
            print(f'GETTING NEW TOKEN ')
            new_access_token = get_new_access_token(refresh_token)
            print(f'NEW TOKEN  {new_access_token}')
            response = client.get_user(AccessToken=new_access_token)
        else:
            raise e
    try:
        user_id = response.get('Username')
        for item in response['UserAttributes']:
            if item['Name'] == 'nickname':
                nickname = item['Value']
            if item['Name'] == 'email':
                email = item['Value']

        user_info = get_user(user_id)
        print(user_info)
        return Me(id=user_id, nickname=nickname, email=email,access_token=access_token,refresh_token=refresh_token ,new_access_token= new_access_token)
    except Exception as ex:
        print(str(ex))
        raise ex

def get_user(user_id: str):
    try:
        response= client.admin_get_user(UserPoolId=config['COGNITO_POOL_ID'],Username=user_id)
        user_id = response.get('Username')
        for item in response['UserAttributes']:
            if item['Name'] == 'nickname':
                nickname = item['Value']
            if item['Name'] == 'email':
                email = item['Value']
            if item['Name'] == 'identities':
                is_external_user = True
        if is_external_user:
            nickname = email
        return  Me(id=user_id, nickname=nickname, email=email,access_token="access_token",refresh_token="refresh_token" ,
                  new_access_token= "new_access_token")
    except Exception as ex:
        print(str(ex))
        raise ex

def list_users():
    try:
        users = []
        next_page = None
        kwargs = {
            'UserPoolId': config['COGNITO_POOL_ID'],
            'Filter': "email = 'afc@integrichain.com'"
            #'Filter': "email ^= 'afc'"
        }
        users_remain = True
        while users_remain:
            if next_page:
                kwargs['PaginationToken'] = next_page
            response = client.list_users(**kwargs)
            users.extend(response['Users'])
            next_page = response.get('PaginationToken', None)
            users_remain = next_page is not None
        return users
    except Exception as e:
        print(f"There is an error listing cognito users {str(e)}")


def get_user_from_me(user_id: str):
    try:
        response= client.admin_get_user(UserPoolId=config['COGNITO_POOL_ID'],Username=user_id)
        return response
    except Exception as ex:
        print(str(ex))
        raise ex

def get_user_info_me(access_token: str):
    nickname = None
    email = None
    new_access_token = None
    is_external_user = False
    try:
        response = client.get_user(AccessToken=access_token)
    except ClientError as e:
        print(f'CLIENT ERROR: {str(e)}')
 
    try:
        user_id = response.get('Username')
        for item in response['UserAttributes']:
            if item['Name'] == 'nickname':
                nickname = item['Value']
            if item['Name'] == 'email':
                email = item['Value']
            if item['Name'] == 'identities':
                is_external_user = True
        user_info = get_user_from_me(user_id)
        if is_external_user:
            nickname = email
        return Me(id=user_id, nickname=nickname, email=email,access_token=access_token,refresh_token="refresh_token" ,
                  new_access_token= new_access_token)
    except Exception as ex:
        print(str(ex))
        raise ex

def get_me(access_token:str) -> Me:
    try:
        if not access_token or  access_token.strip() == '':
            raise ex
        me = get_user_info_me(access_token)
        return me
    except Exception as ex:
        print(str(ex))
        raise ex



def _authenticated_by_cognito_token() -> Me:

    token_auth = "eyJraWQiOiJicE5Iblo5K0FMUGkrem5vWGdRT1wvU0xkSGhSTlZjV2lEWFdmZXFEZTRudz0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI0NmMyM2RlZi1hNDQ3LTRmOGYtOGY5MS1iNGI1M2VjY2NlNzEiLCJjb2duaXRvOmdyb3VwcyI6WyJ1cy1lYXN0LTFfRDl2cUs0RnBNX3BpbmdpZGdzayJdLCJpc3MiOiJodHRwczpcL1wvY29nbml0by1pZHAudXMtZWFzdC0xLmFtYXpvbmF3cy5jb21cL3VzLWVhc3QtMV9EOXZxSzRGcE0iLCJ2ZXJzaW9uIjoyLCJjbGllbnRfaWQiOiI0Zm8zdDN1NzI2dDV2bjk3amdsZmkzMGNyaSIsIm9yaWdpbl9qdGkiOiI0ZDAyODNmNC1mMGY0LTRjYzEtYjM0Zi0wYTAyYTE1NmVhYzUiLCJ0b2tlbl91c2UiOiJhY2Nlc3MiLCJzY29wZSI6ImF3cy5jb2duaXRvLnNpZ25pbi51c2VyLmFkbWluIG9wZW5pZCBlbWFpbCIsImF1dGhfdGltZSI6MTcwMDU4MTcwMSwiZXhwIjoxNzAwNTg1MzAxLCJpYXQiOjE3MDA1ODE3MDEsImp0aSI6ImE2NzNkNmE0LWM0YWMtNDU1Ni04YjBmLWY3OWEyMzI0NzBlMSIsInVzZXJuYW1lIjoicGluZ2lkZ3NrX2NocmlzLmEubWVsbG9AZ3NrLmNvbSJ9.lXutyggUgWNCc5fFHoaOvQmG8r80O1tv5XdJcsGJ1RrG6CbIBEU733z2S3ilZJqSUMKpAXEbfu0IVQgUgpwLiqKLTcU0znDXAUWBgvfue18ZSvS2Bn7tcfGJ20s1Nt_wJbimhBIkxomnIOsPtpztyYPYPkXbwBLAPgm6FZepYZafJYOtnxBgt40XJo6P7V68BtMzOoavUge-rZH891qiec3cQl_JK9d_UKWDp95pVA9IaIIQsNlqLmsIfA13TbI4UPyCn29t_jJCA-Sb4DwGBze0Qz4GQ30SnNSWNBqz75xnQvya3cWmiB0xnzvA9uoo9PckRag4a2WWe4C-UIlu4Q"
    if token_auth:
        me = get_me(token_auth)
    return me


if __name__ == '__main__':
    client = boto3.client('cognito-idp', region_name='us-east-1')
    print('GETTING AUTHENTICATED INFO')
    #get_user_from_me('pingidgsk_lisa.m.iannelli@gsk.com')
    me =_authenticated_by_cognito_token()
    print(me.email, me.nickname)



    '''
    print('**************GETTING USER')
    print(get_user('pingidgsk_krishna-deepthi.x.neeli-ranganathan@gsk.com'))
    print('**************GETTING USER')
    print(get_user('pingidgsk_donnica.a.wright@gsk.com'))
    exit()
    user_emails = UserEmails(andresfelipe25_email='andresfelipe25@gmail.com',afc_email='afc@integrichain.com', afr_email='afr@integrichain.com')
    user = NewUser(nickname = 'pipe', email= user_emails.andresfelipe25_email,password='123345678')
    print('*******************************************************************************************************')
    authenticate_response =  authenticate(user=user)
    print(authenticate_response)
    print('*******************************************************************************************************')



   
    print(new_user(user))
    challenge = AuthenticateChallenge(name= authenticate_response.get('ChallengeName'),email=user.email, password=user.password,session= authenticate_response.get('Session'))
    print(authenticate_challenge(challenge))

    print(list_users())
    print(get_user('dfb24df9-a465-4502-8ea8-597bbb774b3b'))
    print(get_user('azureig_afc@integrichainpoc.onmicrosoft.com'))
    print(get_user('dfb24df9-a465-4502-8ea8-597bbb774b3b'))
    print(get_user('azureig_afc@integrichainpoc.onmicrosoft.com'))
    
   
    user_attributes = UserAttribute(email=user_emails.afr_email,attribute='email_verified',value=True)
    print(f'Updating user {user_attributes}')
    update_attributes_response = update_user_attributes(user_attributes)
    print(update_attributes_response)

     user_attributes = UserAttribute(email=user_emails.afc_email,attribute='email',value=user_emails.afr_email)
    print(f'Updating user {user_attributes}')
    update_attributes_response = update_user_attributes(user_attributes)
    print(update_attributes_response)
   
 
    #user_forgot_password = UserConfirmForgotPassword(email=user.email,password=user.password,confirm_code='646957')
    #print(confirm_forgot_password(user_forgot_password))
    print(forgot_password(user=user))
    
    
    user_forgot_password = UserConfirmForgotPassword(email=user.email,password=user.password,confirm_code='646957')
    print(confirm_forgot_password(user_forgot_password))
   #quit()
  

    '''

  







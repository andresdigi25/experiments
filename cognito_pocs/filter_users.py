import json
import boto3
from pydantic import BaseModel, EmailStr

class Email(BaseModel):
    email: EmailStr

config = {'COGNITO_POOL_ID': 'us-east-1_96W9wQYyD', 'COGNITO_CLIENT_ID' : '2tkc5hlarek9mnfecigi627sa7'}
output_template= {'is_external': None,'idp_name': None,
    'source': None }
idps_per_domain={'integrichainpoc.onmicrosoft.com':'azureig',
    'ichaincustomer.onmicrosoft.com':'azurecustomer'}

def filter_users(email):
    try:
        users = []
        next_page = None
        kwargs = {
            'UserPoolId': config['COGNITO_POOL_ID'],
            'Filter': f"email = '{email}'"
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


if __name__ == '__main__':
    client = boto3.client('cognito-idp', region_name='us-east-1')
    cognito_user =  Email(email='afc@integrichain.com')
    azure_user = Email(email='afc@integrichainpoc.onmicrosoft.com')
    domain_user = Email(email='gus@integrichainpoc.onmicrosoft.com')
    non_user = Email(email='non@non.com')
    current_user = non_user
    response =  filter_users(current_user.email)
    print(type(response))
    if response:
        if response[0].get('UserStatus') != 'EXTERNAL_PROVIDER':
            output_template['is_external'] = False
            output_template['idp_name'] = ''
            output_template['source'] ='COGNITO'
        else:
            azure_attributes=json.loads(response[0].get('Attributes')[1].get('Value'))
            output_template['is_external'] = True
            output_template['idp_name'] = azure_attributes[0].get('providerName')
            output_template['source'] ='AZURE'
    else:
        domain = current_user.email.split('@')[1]
        idp_name = idps_per_domain.get(domain)
        if idp_name:
            output_template['is_external'] = True
            output_template['idp_name'] = idp_name
            output_template['source'] ='DOMAIN'

    
    print('********************************************')
    print(output_template)

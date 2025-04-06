import boto3

# Initialize the Cognito Identity Provider client
cognito_idp = boto3.client('cognito-idp', region_name='us-east-1')

# Replace these with your actual values
user_pool_id = 'us-east-1_1C4ibzjNa'
username = 'newuser@example.com'
temporary_password = 'TempPass123!'

# Define user attributes, including custom attributes
user_attributes = [
    {'Name': 'email', 'Value': 'newuser@example.com'},
    {'Name': 'custom:isAdmin', 'Value': 'no'}
]

try:
    response = cognito_idp.admin_create_user(
        UserPoolId=user_pool_id,
        Username=username,
        UserAttributes=user_attributes,
        TemporaryPassword=temporary_password,
        MessageAction='SUPPRESS'
    )
    print(f"User created successfully: {response['User']['Username']}")
except Exception as e:
    print(f"Error creating user: {str(e)}")
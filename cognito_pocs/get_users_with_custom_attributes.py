import boto3

# Initialize the Cognito Identity Provider client
session = boto3.Session(profile_name="sandbox")
cognito_client = session.client('cognito-idp', region_name='us-east-1')

#cognito_client = boto3.client('cognito-idp', region_name='us-east-1')

# Set your User Pool ID
user_pool_id = 'us-east-1_1C4ibzjNa'

# Initialize an empty list to store all users
all_users = []

# Paginate through all users
pagination_token = None
while True:
    if pagination_token:
        response = cognito_client.list_users(
            UserPoolId=user_pool_id,
            PaginationToken=pagination_token
        )
    else:
        response = cognito_client.list_users(UserPoolId=user_pool_id)
    
    all_users.extend(response['Users'])
    
    # Check if there are more users to fetch
    if 'PaginationToken' in response:
        pagination_token = response['PaginationToken']
    else:
        break

# Print users and their attributes
for user in all_users:
    print(f"Username: {user['Username']}")
    print("Custom Attributes:")
    for attr in user['Attributes']:
        if attr['Name'].startswith('custom:') or attr['Name'] == 'email':
            print(f"  {attr['Name']}: {attr['Value']}")

    print("---")

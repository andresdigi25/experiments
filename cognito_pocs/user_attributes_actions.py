import boto3
import json
from botocore.exceptions import ClientError

# Initialize the Cognito Identity Provider client
session = boto3.Session(profile_name="sandbox")
cognito_client = session.client('cognito-idp', region_name='us-east-1')

# Set your User Pool ID and Client ID
user_pool_id = 'us-east-1_1C4ibzjNa'

def create_user(username, email, custom_attributes):
    try:
        response = cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=username,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                *[{'Name': f'custom:{k}', 'Value': v} for k, v in custom_attributes.items()]
            ],
            MessageAction='SUPPRESS'
        )
        print(f"User {username} created successfully")
        return response['User']
    except ClientError as e:
        print(f"Error creating user: {e}")
        return None

def list_users():
    try:
        response = cognito_client.list_users(UserPoolId=user_pool_id)
        for user in response['Users']:
            print(f"Username: {user['Username']}")
            print("Attributes:")
            for attr in user['Attributes']:
                print(f"  {attr['Name']}: {attr['Value']}")
            print("---")
        return response['Users']
    except ClientError as e:
        print(f"Error listing users: {e}")
        return None

def get_user(username):
    try:
        response = cognito_client.admin_get_user(
            UserPoolId=user_pool_id,
            Username=username
        )
        print(f"User details for {username}:")
        for attr in response['UserAttributes']:
            print(f"  {attr['Name']}: {attr['Value']}")
        return response
    except ClientError as e:
        print(f"Error getting user: {e}")
        return None


# Example usage
if __name__ == "__main__":
    # Create 10 users with isAdmin custom attribute
    for i in range(1, 11):
        is_admin = 'true' if i <= 2 else 'false'  # Make first 2 users admins
        email = f'testuser{i}@example.com'
        create_user(email, email, {'isAdmin': is_admin})

    # List all users and their attributes
    print("\nListing all users:")
    list_users()

    # Get a specific user
    print("\nGetting details for testuser1@example.com:")
    get_user('testuser1@example.com')


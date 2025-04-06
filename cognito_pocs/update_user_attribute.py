import boto3
import json
from botocore.exceptions import ClientError

# Initialize the Cognito Identity Provider client
session = boto3.Session(profile_name="sandbox")
cognito_client = session.client('cognito-idp', region_name='us-east-1')

# Set your User Pool ID and Client ID
user_pool_id = 'us-east-1_1C4ibzjNa'

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

def update_is_admin(username, is_admin):
    try:
        response = cognito_client.admin_update_user_attributes(
            UserPoolId=user_pool_id,
            Username=username,
            UserAttributes=[
                {'Name': 'custom:isAdmin', 'Value': str(is_admin).lower()}
            ]
        )
        print(f"Successfully updated isAdmin to {is_admin} for user {username}")
        return response
    except ClientError as e:
        print(f"Error updating user attributes: {e}")
        return None

# Example usage
if __name__ == "__main__":
    # ... existing code ...

    # Example of updating isAdmin attribute
    print("\nUpdating user attribute:")
    update_is_admin('testuser4@example.com', 'true')
    
    # Verify the update
    print("\nVerifying update for testuser4@example.com:")
    get_user('testuser4@example.com')
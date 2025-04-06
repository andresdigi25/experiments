import boto3

# Create a client for the API Gateway service
client = boto3.client('apigateway')

# Retrieve the list of API keys
response = client.get_api_keys()

# Print the list of API keys
for api_key in response['items']:
    print(f"ID: {api_key['id']}, Name: {api_key['name']}")
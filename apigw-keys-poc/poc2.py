import boto3

# Create a client for the API Gateway service
client = boto3.client('apigateway')

# Retrieve the list of API keys
response = client.get_api_keys()

# Print the list of API keys and their associated usage plans
for api_key in response['items']:
    print(f"API Key ID: {api_key['id']}, Name: {api_key['name']}")
    
    # Retrieve the usage plans associated with the API key
    usage_plans_response = client.get_usage_plans(keyId=api_key['id'])
    
    for usage_plan in usage_plans_response['items']:
        print(f"  Usage Plan ID: {usage_plan['id']}, Name: {usage_plan['name']}")
        print(f"    Description: {usage_plan.get('description', 'No description')}")
        print(f"    Quota: {usage_plan.get('quota', 'No quota')}")
        print(f"    Throttle: {usage_plan.get('throttle', 'No throttle')}")
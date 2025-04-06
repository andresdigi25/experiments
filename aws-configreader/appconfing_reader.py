import boto3
import json

# Initialize Boto3 client for AppConfigData
client = boto3.client('appconfigdata')

# Start configuration session
response = client.start_configuration_session(
	ApplicationIdentifier='kdesveh',
	ConfigurationProfileIdentifier='0tbbvw0',
	EnvironmentIdentifier='m7tg4q5'
)
initial_config_token = response['InitialConfigurationToken']

# Get latest configuration
config_response = client.get_latest_configuration(
	ConfigurationToken=initial_config_token
)
config_data = config_response['Configuration'].read()

# Parse configuration
config_json = json.loads(config_data)
print(f"Configuration JSON: {config_json}")

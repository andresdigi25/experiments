import json
import os
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get the endpoint name from environment variable
ENDPOINT_NAME = os.environ.get('SAGEMAKER_ENDPOINT_NAME')

# Initialize the SageMaker runtime client
sagemaker_runtime = boto3.client('sagemaker-runtime')

def lambda_handler(event, context):
    """Lambda function that invokes a SageMaker endpoint for address matching."""
    logger.info(f"Event: {json.dumps(event)}")
    
    # Check if endpoint name is configured
    if not ENDPOINT_NAME:
        logger.error("SAGEMAKER_ENDPOINT_NAME environment variable not set")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'SageMaker endpoint name not configured'})
        }
    
    try:
        # Extract request body
        if 'body' in event:
            # API Gateway integration
            if isinstance(event['body'], str):
                request_body = json.loads(event['body'])
            else:
                request_body = event['body']
        else:
            # Direct Lambda invocation
            request_body = event
        
        logger.info(f"Request body: {json.dumps(request_body)}")
        
        # Validate input
        if 'addresses' not in request_body and not all(key in request_body for key in ['addr1', 'addr2']):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid input. Provide either an "addresses" array or "addr1" and "addr2" fields.'
                })
            }
        
        # Invoke SageMaker endpoint
        response = sagemaker_runtime.invoke_endpoint(
            EndpointName=ENDPOINT_NAME,
            ContentType='application/json',
            Body=json.dumps(request_body)
        )
        
        # Parse response
        result = json.loads(response['Body'].read().decode())
        
        # Return response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',  # For CORS support
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
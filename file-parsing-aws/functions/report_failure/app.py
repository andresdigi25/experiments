import json
import boto3
import os
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize SNS client
sns = boto3.client('sns')

def lambda_handler(event, context):
    """Lambda handler for reporting file processing failures"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract error details
        error = event.get('error', 'Unknown error')
        cause = event.get('cause', 'No cause specified')
        
        # Get file details from input
        input_data = event.get('input', {})
        bucket = input_data.get('bucket', 'unknown')
        key = input_data.get('key', 'unknown')
        
        # Prepare notification message
        message = {
            'status': 'FAILURE',
            'file': {
                'bucket': bucket,
                'key': key
            },
            'error': error,
            'cause': cause,
            'timestamp': context.invoked_function_arn
        }
        
        # Send SNS notification
        topic_arn = os.environ.get('SNS_TOPIC_ARN')
        if topic_arn:
            sns.publish(
                TopicArn=topic_arn,
                Message=json.dumps(message),
                Subject=f"File Processing Failure: {key}"
            )
        
        logger.info(f"Failure report sent for {key}")
        
        # Return final result
        return {
            'status': 'FAILURE',
            'file': {
                'bucket': bucket,
                'key': key
            },
            'error': error,
            'cause': cause
        }
        
    except Exception as e:
        logger.error(f"Error in failure reporting lambda: {str(e)}")
        return {
            'status': 'ERROR',
            'error': str(e),
            'file': {
                'bucket': 'unknown',
                'key': 'unknown'
            }
        }
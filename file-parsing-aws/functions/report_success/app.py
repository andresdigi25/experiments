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
    """Lambda handler for reporting successful file processing"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract event details
        bucket = event['bucket']
        key = event['key']
        storage_result = event['storageResult']
        mapped_data = event['mappedData']
        
        # Prepare notification message
        message = {
            'status': 'SUCCESS',
            'file': {
                'bucket': bucket,
                'key': key
            },
            'summary': {
                'totalRecords': mapped_data['total'],
                'validRecords': mapped_data['valid'],
                'invalidRecords': mapped_data['invalid'],
                'savedRecords': storage_result['savedCount'],
                'failedRecords': storage_result['failedCount']
            },
            'timestamp': context.invoked_function_arn
        }
        
        # Send SNS notification
        topic_arn = os.environ.get('SNS_TOPIC_ARN')
        if topic_arn:
            sns.publish(
                TopicArn=topic_arn,
                Message=json.dumps(message),
                Subject=f"File Processing Success: {key}"
            )
        
        logger.info(f"Success report sent for {key}")
        
        # Return final result
        return {
            'status': 'SUCCESS',
            'file': {
                'bucket': bucket,
                'key': key
            },
            'summary': {
                'totalRecords': mapped_data['total'],
                'validRecords': mapped_data['valid'],
                'invalidRecords': mapped_data['invalid'],
                'savedRecords': storage_result['savedCount'],
                'failedRecords': storage_result['failedCount']
            }
        }
        
    except Exception as e:
        logger.error(f"Error in success reporting lambda: {str(e)}")
        return {
            'status': 'ERROR',
            'error': str(e),
            'file': {
                'bucket': event.get('bucket', 'unknown'),
                'key': event.get('key', 'unknown')
            }
        }
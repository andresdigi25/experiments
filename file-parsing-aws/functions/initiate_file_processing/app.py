import json
import boto3
import os
import uuid
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
stepfunctions = boto3.client('stepfunctions')

def lambda_handler(event, context):
    """Lambda handler for initiating file processing workflow"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Check event source
        if 'httpMethod' in event:
            # API Gateway event
            return handle_api_event(event)
        elif 'source' in event and event['source'] == 'aws.s3':
            # EventBridge event from S3
            return handle_s3_event(event)
        else:
            logger.error("Unknown event source")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Unknown event source'
                })
            }
            
    except Exception as e:
        logger.error(f"Error in initiate processing lambda: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }

def handle_api_event(event):
    """Handle API Gateway event to initiate processing"""
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        
        # Extract parameters
        bucket = body.get('bucket')
        key = body.get('key')
        mapping_source = body.get('mappingSource', 'default')
        
        # Validate parameters
        if not bucket or not key:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'Missing required parameters: bucket and key'
                })
            }
        
        # Start Step Functions execution
        execution_arn = start_execution(bucket, key, mapping_source)
        
        return {
            'statusCode': 202,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'File processing initiated',
                'file': {
                    'bucket': bucket,
                    'key': key
                },
                'execution': {
                    'arn': execution_arn
                }
            })
        }
        
    except Exception as e:
        logger.error(f"Error handling API event: {str(e)}")
        raise

def handle_s3_event(event):
    """Handle S3 event via EventBridge"""
    try:
        # Extract S3 details from EventBridge event
        detail = event.get('detail', {})
        bucket = detail.get('bucket', {}).get('name')
        object_info = detail.get('object', {})
        key = object_info.get('key')
        
        # Default mapping source
        mapping_source = 'default'
        
        # Validate parameters
        if not bucket or not key:
            logger.error("Missing bucket or key in S3 event")
            return {
                'error': 'Missing bucket or key in S3 event'
            }
        
        # Check if we should process this file (e.g., only process files in 'uploads/' prefix)
        if not key.startswith('uploads/'):
            logger.info(f"Skipping file not in uploads directory: {key}")
            return {
                'status': 'skipped',
                'reason': 'File not in uploads directory'
            }
        
        # Start Step Functions execution
        execution_arn = start_execution(bucket, key, mapping_source)
        
        return {
            'status': 'initiated',
            'file': {
                'bucket': bucket,
                'key': key
            },
            'execution': {
                'arn': execution_arn
            }
        }
        
    except Exception as e:
        logger.error(f"Error handling S3 event: {str(e)}")
        raise

def start_execution(bucket, key, mapping_source):
    """Start Step Functions execution for file processing"""
    # Prepare input for Step Functions
    execution_input = {
        'bucket': bucket,
        'key': key,
        'mappingSource': mapping_source
    }
    
    # Get state machine ARN
    state_machine_arn = os.environ.get('STATE_MACHINE_ARN')
    if not state_machine_arn:
        raise ValueError("STATE_MACHINE_ARN environment variable not set")
    
    # Start execution
    response = stepfunctions.start_execution(
        stateMachineArn=state_machine_arn,
        name=f"file-processing-{str(uuid.uuid4())}",
        input=json.dumps(execution_input)
    )
    
    return response['executionArn']
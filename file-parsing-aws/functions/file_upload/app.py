import json
import boto3
import base64
import os
import logging
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3 = boto3.client('s3')
stepfunctions = boto3.client('stepfunctions')

def lambda_handler(event, context):
    """Lambda handler for file upload API"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Parse request body
        if 'body' not in event:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'No body found in request'
                })
            }
        
        # Check if body is base64 encoded
        body = event['body']
        is_base64 = event.get('isBase64Encoded', False)
        
        if is_base64:
            body = base64.b64decode(body)
        
        # Parse multipart/form-data
        # For simplicity, we're assuming a direct file upload rather than parsing multipart/form-data
        # In a real implementation, you would need to parse the multipart/form-data properly
        
        # Get content type and file name from headers
        content_type = 'application/octet-stream'  # Default
        file_name = f"upload-{str(uuid.uuid4())}.csv"  # Default
        
        # Extract content type from headers
        headers = event.get('headers', {})
        if headers and 'Content-Type' in headers:
            content_type = headers['Content-Type']
        
        # Extract file name from queryStringParameters or use default
        query_params = event.get('queryStringParameters', {})
        if query_params and 'filename' in query_params:
            file_name = query_params['filename']
        
        # Get mapping source
        mapping_source = 'default'
        if query_params and 'source' in query_params:
            mapping_source = query_params['source']
        
        # Upload to S3
        bucket_name = os.environ.get('UPLOAD_BUCKET')
        s3_key = f"uploads/{file_name}"
        
        s3.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=body,
            ContentType=content_type
        )
        
        # Start Step Functions execution
        state_machine_arn = os.environ.get('STATE_MACHINE_ARN')
        if state_machine_arn:
            execution_input = {
                'bucket': bucket_name,
                'key': s3_key,
                'mappingSource': mapping_source
            }
            
            response = stepfunctions.start_execution(
                stateMachineArn=state_machine_arn,
                name=f"file-processing-{str(uuid.uuid4())}",
                input=json.dumps(execution_input)
            )
            
            execution_arn = response['executionArn']
            
            return {
                'statusCode': 202,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'message': 'File uploaded and processing started',
                    'file': {
                        'bucket': bucket_name,
                        'key': s3_key
                    },
                    'execution': {
                        'arn': execution_arn
                    }
                })
            }
        else:
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'message': 'File uploaded but processing not started (no state machine ARN)',
                    'file': {
                        'bucket': bucket_name,
                        'key': s3_key
                    }
                })
            }
        
    except Exception as e:
        logger.error(f"Error in file upload lambda: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }
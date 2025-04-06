import json
import boto3
import os
import uuid
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
records_table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE'))

def lambda_handler(event, context):
    """Lambda handler for storing mapped data in DynamoDB"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract mapped records
        mapped_data = event['mappedData']
        records = mapped_data['records']
        
        # Track success/failure
        saved_count = 0
        failed_count = 0
        failures = []
        
        # Process each record
        for record in records:
            try:
                # Prepare item for DynamoDB
                item = {
                    'id': str(uuid.uuid4()),
                    'name': record['name'],
                    'address1': record.get('address1', ''),
                    'city': record.get('city', ''),
                    'state': record.get('state', ''),
                    'zip': record.get('zip', ''),
                    'auth_id': record['auth_id'],
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                # Insert or update record in DynamoDB
                records_table.put_item(Item=item)
                saved_count += 1
                
            except Exception as e:
                failed_count += 1
                failures.append({
                    'record': record,
                    'error': str(e)
                })
                logger.error(f"Error saving record: {str(e)}")
        
        logger.info(f"Saved {saved_count} records, {failed_count} failures")
        
        # Return storage results
        return {
            'bucket': event['bucket'],
            'key': event['key'],
            'mappingSource': event.get('mappingSource', 'default'),
            'validation': event['validation'],
            'fileType': event['fileType'],
            'mappedData': event['mappedData'],
            'storageResult': {
                'savedCount': saved_count,
                'failedCount': failed_count,
                'failures': failures[:5]  # Limit to first 5 failures to avoid large payloads
            }
        }
        
    except Exception as e:
        logger.error(f"Error in storage lambda: {str(e)}")
        return {
            'bucket': event.get('bucket', 'unknown'),
            'key': event.get('key', 'unknown'),
            'mappingSource': event.get('mappingSource', 'default'),
            'validation': event.get('validation', {'isValid': False}),
            'fileType': event.get('fileType', {'type': 'unknown'}),
            'mappedData': event.get('mappedData', {'total': 0, 'valid': 0, 'records': []}),
            'storageResult': {
                'savedCount': 0,
                'failedCount': 0,
                'error': str(e)
            }
        }
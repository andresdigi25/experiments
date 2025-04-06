import json
import logging
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def detect_file_type(filename):
    """Detect file type based on extension"""
    extension = filename.split('.')[-1].lower()
    
    if extension == 'csv':
        return 'csv'
    elif extension in ['xls', 'xlsx']:
        return 'excel'
    elif extension == 'json':
        return 'json'
    elif extension == 'txt':
        return 'text'
    else:
        return 'unknown'

def lambda_handler(event, context):
    """Lambda handler to determine file type"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Get file key from event
        key = event['key']
        
        # Determine file type
        file_type = detect_file_type(key)
        
        logger.info(f"Determined file type: {file_type}")
        
        # Return file type information
        return {
            'bucket': event['bucket'],
            'key': event['key'],
            'mappingSource': event.get('mappingSource', 'default'),
            'validation': event['validation'],
            'fileType': {
                'type': file_type,
                'extension': key.split('.')[-1].lower()
            }
        }
    
    except Exception as e:
        logger.error(f"Error determining file type: {str(e)}")
        return {
            'bucket': event.get('bucket', 'unknown'),
            'key': event.get('key', 'unknown'),
            'mappingSource': event.get('mappingSource', 'default'),
            'validation': event.get('validation', {'isValid': False}),
            'fileType': {
                'type': 'unknown',
                'extension': 'unknown',
                'error': str(e)
            }
        }
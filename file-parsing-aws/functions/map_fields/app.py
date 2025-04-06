import json
import boto3
import os
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
mappings_table = dynamodb.Table(os.environ.get('FIELD_MAPPINGS_TABLE'))

def get_field_mappings(mapping_key='default'):
    """Retrieve field mappings from DynamoDB"""
    try:
        response = mappings_table.get_item(Key={'mapping_name': mapping_key})
        if 'Item' in response:
            return response['Item']['mappings']
    except Exception as e:
        logger.error(f"Error retrieving field mappings: {str(e)}")
    
    # Default mappings if retrieval fails or mapping not found
    return {
        "name": ["name", "full_name", "customer_name", "client_name"],
        "address1": ["address", "address1", "street_address", "street"],
        "city": ["city", "town"],
        "state": ["state", "province", "region"],
        "zip": ["zip", "zipcode", "postal_code", "postalcode", "zip_code"],
        "auth_id": ["auth_id", "authid", "authorization_id", "auth", "id"]
    }

def normalize_record(record, mapping):
    """Map source fields to target fields based on mapping configuration"""
    # Initialize normalized record with None values
    normalized = {target_field: None for target_field in mapping.keys()}
    
    # Process each field in the source record
    for source_field, value in record.items():
        source_field_lower = source_field.lower().strip()
        
        # Check each target field for possible mappings
        for target_field, possible_source_fields in mapping.items():
            # Check if source field matches any possible mapping
            if any(source_field_lower == s.lower() or source_field_lower.find(s.lower()) >= 0 
                  for s in possible_source_fields):
                normalized[target_field] = value
                break
    
    return normalized

def lambda_handler(event, context):
    """Lambda handler for field mapping"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract event details
        parsed_data = event['parsedData']
        mapping_source = event.get('mappingSource', 'default')
        
        # Get field mappings
        field_mappings = get_field_mappings(mapping_source)
        
        # Map fields for each record
        mapped_records = [normalize_record(record, field_mappings) for record in parsed_data]
        
        # Filter out invalid records (missing required fields)
        valid_records = [
            record for record in mapped_records 
            if record['name'] is not None and record['auth_id'] is not None
        ]
        
        logger.info(f"Mapped {len(mapped_records)} records, {len(valid_records)} valid")
        
        # Return mapped data
        return {
            'bucket': event['bucket'],
            'key': event['key'],
            'mappingSource': mapping_source,
            'validation': event['validation'],
            'fileType': event['fileType'],
            'mappedData': {
                'total': len(mapped_records),
                'valid': len(valid_records),
                'invalid': len(mapped_records) - len(valid_records),
                'records': valid_records
            }
        }
        
    except Exception as e:
        logger.error(f"Error in mapping lambda: {str(e)}")
        return {
            'bucket': event.get('bucket', 'unknown'),
            'key': event.get('key', 'unknown'),
            'mappingSource': event.get('mappingSource', 'default'),
            'validation': event.get('validation', {'isValid': False}),
            'fileType': event.get('fileType', {'type': 'unknown'}),
            'mappedData': {
                'total': 0,
                'valid': 0,
                'invalid': 0,
                'records': [],
                'error': str(e)
            }
        }
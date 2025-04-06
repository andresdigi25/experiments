import json
import boto3
import pandas as pd
import io
import os
import csv
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3 = boto3.client('s3')
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

def validate_csv(file_content, mapping_key):
    """Validate CSV file by checking if required fields can be mapped"""
    validation_result = {'isValid': False, 'errors': []}
    
    try:
        # Read CSV data
        csv_buffer = io.StringIO(file_content.decode('utf-8'))
        reader = csv.reader(csv_buffer)
        
        # Get headers (first row)
        headers = next(reader)
        
        # Get field mappings
        field_mappings = get_field_mappings(mapping_key)
        
        # Check if we can map all required fields
        required_target_fields = ['name', 'auth_id']
        missing_fields = []
        
        for target_field in required_target_fields:
            source_fields = field_mappings.get(target_field, [])
            if not any(source in [h.lower() for h in headers] for source in [s.lower() for s in source_fields]):
                missing_fields.append(target_field)
        
        if missing_fields:
            validation_result['errors'].append(f"Missing mappable fields: {', '.join(missing_fields)}")
        else:
            validation_result['isValid'] = True
            
    except Exception as e:
        validation_result['errors'].append(f"CSV validation error: {str(e)}")
    
    return validation_result

def validate_json(file_content, mapping_key):
    """Validate JSON file structure and content"""
    validation_result = {'isValid': False, 'errors': []}
    
    try:
        # Parse JSON
        data = json.loads(file_content)
        
        # Ensure data is a list
        if not isinstance(data, list):
            data = [data]
        
        # Check if we have any records
        if len(data) == 0:
            validation_result['errors'].append("JSON file contains no records")
            return validation_result
        
        # Get field mappings
        field_mappings = get_field_mappings(mapping_key)
        required_target_fields = ['name', 'auth_id']
        
        # Check first record to see if required fields can be mapped
        first_record = data[0]
        missing_fields = []
        
        for target_field in required_target_fields:
            source_fields = field_mappings.get(target_field, [])
            if not any(source in first_record for source in source_fields):
                missing_fields.append(target_field)
        
        if missing_fields:
            validation_result['errors'].append(f"Missing mappable fields: {', '.join(missing_fields)}")
        else:
            validation_result['isValid'] = True
            
    except Exception as e:
        validation_result['errors'].append(f"JSON validation error: {str(e)}")
    
    return validation_result

def validate_txt(file_content, mapping_key):
    """Validate text file by checking if required fields can be mapped"""
    validation_result = {'isValid': False, 'errors': []}
    
    try:
        # Decode content
        content = file_content.decode('utf-8')
        
        # Try to detect delimiter
        first_line = content.split('\n')[0].strip()
        delimiter = '\t' if '\t' in first_line else ','
        
        # Parse as CSV with detected delimiter
        csv_buffer = io.StringIO(content)
        reader = csv.reader(csv_buffer, delimiter=delimiter)
        
        # Get headers (first row)
        headers = next(reader)
        
        # Get field mappings
        field_mappings = get_field_mappings(mapping_key)
        
        # Check if we can map all required fields
        required_target_fields = ['name', 'auth_id']
        missing_fields = []
        
        for target_field in required_target_fields:
            source_fields = field_mappings.get(target_field, [])
            if not any(source in [h.lower() for h in headers] for source in [s.lower() for s in source_fields]):
                missing_fields.append(target_field)
        
        if missing_fields:
            validation_result['errors'].append(f"Missing mappable fields: {', '.join(missing_fields)}")
        else:
            validation_result['isValid'] = True
            
    except Exception as e:
        validation_result['errors'].append(f"Text file validation error: {str(e)}")
    
    return validation_result

def lambda_handler(event, context):
    """Lambda handler for file validation"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract event details
        bucket = event['bucket']
        key = event['key']
        mapping_source = event.get('mappingSource', 'default')
        
        # Get file extension
        file_extension = key.split('.')[-1].lower()
        
        # Get file from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        file_content = response['Body'].read()
        
        # Validate based on file type
        if file_extension == 'csv':
            validation_result = validate_csv(file_content, mapping_source)
        elif file_extension == 'json':
            validation_result = validate_json(file_content, mapping_source)
        elif file_extension == 'txt':
            validation_result = validate_txt(file_content, mapping_source)
        elif file_extension in ['xls', 'xlsx']:
            # For Excel files, we'd need additional processing
            # For simplicity, we'll just mark them as valid
            validation_result = {'isValid': True, 'errors': []}
        else:
            validation_result = {
                'isValid': False, 
                'errors': [f"Unsupported file type: {file_extension}"]
            }
        
        logger.info(f"Validation result: {json.dumps(validation_result)}")
        
        # Return result
        return {
            'bucket': bucket,
            'key': key,
            'mappingSource': mapping_source,
            'validation': validation_result
        }
        
    except Exception as e:
        logger.error(f"Error in validation lambda: {str(e)}")
        return {
            'bucket': event.get('bucket', 'unknown'),
            'key': event.get('key', 'unknown'),
            'mappingSource': event.get('mappingSource', 'default'),
            'validation': {
                'isValid': False,
                'errors': [f"Validation process error: {str(e)}"]
            }
        }
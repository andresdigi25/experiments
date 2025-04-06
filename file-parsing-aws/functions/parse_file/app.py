import json
import boto3
import pandas as pd
import io
import csv
import logging
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize S3 client
s3 = boto3.client('s3')

def parse_csv(file_content):
    """Parse CSV file content into a list of records"""
    try:
        # Parse CSV
        csv_buffer = io.StringIO(file_content.decode('utf-8'))
        reader = csv.DictReader(csv_buffer)
        records = [row for row in reader]
        
        return records
    except Exception as e:
        logger.error(f"Error parsing CSV: {str(e)}")
        raise

def parse_json(file_content):
    """Parse JSON file content into a list of records"""
    try:
        # Parse JSON
        data = json.loads(file_content)
        
        # Ensure data is a list
        if not isinstance(data, list):
            data = [data]
        
        return data
    except Exception as e:
        logger.error(f"Error parsing JSON: {str(e)}")
        raise

def parse_excel(file_content):
    """Parse Excel file content into a list of records"""
    try:
        # Save content to a temporary file
        temp_file = '/tmp/temp.xlsx'
        with open(temp_file, 'wb') as f:
            f.write(file_content)
        
        # Read Excel file
        df = pd.read_excel(temp_file)
        
        # Convert to list of dictionaries
        records = df.to_dict(orient='records')
        
        # Clean up
        os.remove(temp_file)
        
        return records
    except Exception as e:
        logger.error(f"Error parsing Excel: {str(e)}")
        # Clean up in case of error
        if os.path.exists('/tmp/temp.xlsx'):
            os.remove('/tmp/temp.xlsx')
        raise

def parse_text(file_content):
    """Parse text file content into a list of records"""
    try:
        # Decode content
        content = file_content.decode('utf-8')
        
        # Try to detect delimiter
        first_line = content.split('\n')[0].strip()
        delimiter = '\t' if '\t' in first_line else ','
        
        # Parse as CSV with detected delimiter
        csv_buffer = io.StringIO(content)
        reader = csv.DictReader(csv_buffer, delimiter=delimiter)
        records = [row for row in reader]
        
        return records
    except Exception as e:
        logger.error(f"Error parsing text file: {str(e)}")
        raise

def lambda_handler(event, context):
    """Lambda handler for file parsing"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract event details
        bucket = event['bucket']
        key = event['key']
        file_type = event['fileType']['type']
        
        # Get file from S3
        response = s3.get_object(Bucket=bucket, Key=key)
        file_content = response['Body'].read()
        
        # Parse based on file type
        if file_type == 'csv':
            records = parse_csv(file_content)
        elif file_type == 'json':
            records = parse_json(file_content)
        elif file_type == 'excel':
            records = parse_excel(file_content)
        elif file_type == 'text':
            records = parse_text(file_content)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        logger.info(f"Successfully parsed {len(records)} records")
        
        # Return parsed data
        return {
            'bucket': bucket,
            'key': key,
            'mappingSource': event.get('mappingSource', 'default'),
            'validation': event['validation'],
            'fileType': event['fileType'],
            'parsedData': records
        }
        
    except Exception as e:
        logger.error(f"Error in parsing lambda: {str(e)}")
        return {
            'bucket': event.get('bucket', 'unknown'),
            'key': event.get('key', 'unknown'),
            'mappingSource': event.get('mappingSource', 'default'),
            'validation': event.get('validation', {'isValid': False}),
            'fileType': event.get('fileType', {'type': 'unknown'}),
            'parsedData': [],
            'error': str(e)
        }
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

def lambda_handler(event, context):
    """Lambda handler for managing field mappings"""
    logger.info(f"Received event: {json.dumps(event)}")
    
    try:
        # Determine HTTP method
        http_method = event.get('httpMethod', '')
        
        # Handle different methods
        if http_method == 'GET':
            return get_mappings()
        elif http_method == 'POST':
            # Parse request body
            if 'body' in event:
                body = json.loads(event.get('body', '{}'))
                return create_mapping(body)
        
        # Unsupported method
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': f"Unsupported method: {http_method}"
            })
        }
        
    except Exception as e:
        logger.error(f"Error in manage mappings lambda: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e)
            })
        }

def get_mappings():
    """Retrieve all field mappings"""
    try:
        # Scan the mappings table
        response = mappings_table.scan()
        items = response.get('Items', [])
        
        # Convert to a dictionary with mapping_name as key
        mappings = {item['mapping_name']: item['mappings'] for item in items}
        
        # If no mappings found, initialize with defaults
        if not mappings:
            default_mappings = {
                "default": {
                    "name": ["name", "full_name", "customer_name", "client_name"],
                    "address1": ["address", "address1", "street_address", "street"],
                    "city": ["city", "town"],
                    "state": ["state", "province", "region"],
                    "zip": ["zip", "zipcode", "postal_code", "postalcode", "zip_code"],
                    "auth_id": ["auth_id", "authid", "authorization_id", "auth", "id"]
                }
            }
            
            # Save default mappings
            mappings_table.put_item(
                Item={
                    'mapping_name': 'default',
                    'mappings': default_mappings['default']
                }
            )
            
            mappings = default_mappings
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(mappings)
        }
        
    except Exception as e:
        logger.error(f"Error getting mappings: {str(e)}")
        raise

def create_mapping(body):
    """Create or update a field mapping"""
    try:
        # Extract mapping details
        name = body.get('name')
        mappings = body.get('mappings')
        
        # Validate input
        if not name or not mappings:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps({
                    'error': 'Missing required fields: name and mappings'
                })
            }
        
        # Save to DynamoDB
        mappings_table.put_item(
            Item={
                'mapping_name': name,
                'mappings': mappings
            }
        )
        
        return {
            'statusCode': 201,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'message': 'Mapping configuration created',
                'name': name
            })
        }
        
    except Exception as e:
        logger.error(f"Error creating mapping: {str(e)}")
        raise
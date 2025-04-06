from fastapi import FastAPI
import boto3
from botocore.exceptions import ClientError
from pydantic import BaseModel
import os
import time

app = FastAPI()

# Get the DynamoDB endpoint from environment variables, with a default value
dynamodb_endpoint = os.getenv('DYNAMODB_ENDPOINT', 'http://localhost:8000')

# Configure DynamoDB client with dummy credentials for local use
dynamodb = boto3.resource(
    'dynamodb',
    region_name='us-east-1',
    endpoint_url=dynamodb_endpoint,
    aws_access_key_id='dummy_access_key',
    aws_secret_access_key='dummy_secret_key'
)

# Create a table
try:
    table = dynamodb.create_table(
        TableName='Cache',
        KeySchema=[
            {
                'AttributeName': 'key',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'key',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    table.wait_until_exists()
    
    # Enable TTL on the table
    dynamodb.meta.client.update_time_to_live(
        TableName='Cache',
        TimeToLiveSpecification={
            'Enabled': True,
            'AttributeName': 'ttl'
        }
    )
except ClientError as e:
    if e.response['Error']['Code'] != 'ResourceInUseException':
        raise

class CacheItem(BaseModel):
    key: str
    value: str
    ttl: int  # TTL in seconds

@app.post("/cache/")
def set_cache(item: CacheItem):
    ttl_timestamp = int(time.time()) + item.ttl
    table.put_item(Item={'key': item.key, 'value': item.value, 'ttl': ttl_timestamp})
    return {"message": "Item cached"}

@app.get("/cache/{key}")
def get_cache(key: str):
    response = table.get_item(Key={'key': key})
    if 'Item' in response:
        return response['Item']
    else:
        return {"message": "Item not found"}
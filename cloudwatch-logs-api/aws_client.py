import boto3
import aioboto3
from config import settings
import logging

logger = logging.getLogger(__name__)

def get_aws_credentials():
    """
    Get AWS credentials configuration based on settings.
    If using instance profile, return empty dict to use instance credentials.
    """
    if settings.USE_AWS_INSTANCE_PROFILE:
        logger.info("Using AWS instance profile for credentials")
        return {}
    
    logger.info(f"Using AWS credentials from environment for region {settings.AWS_REGION}")
    return {
        "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
        "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
        "region_name": settings.AWS_REGION
    }

def get_boto3_client(service_name):
    """
    Get a boto3 client for the specified service.
    """
    credentials = get_aws_credentials()
    return boto3.client(service_name, **credentials)

def get_boto3_resource(service_name):
    """
    Get a boto3 resource for the specified service.
    """
    credentials = get_aws_credentials()
    return boto3.resource(service_name, **credentials)

async def get_aioboto3_client(service_name):
    """
    Get an async boto3 client for the specified service.
    """
    credentials = get_aws_credentials()
    session = aioboto3.Session()
    return session.client(service_name, **credentials)

# Initialize commonly used clients
logs_client = get_boto3_client('logs')
cloudwatch_client = get_boto3_client('cloudwatch')
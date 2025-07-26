"""
Lambda Handler Entry Point
Minimal entry point that delegates to the application layer
"""

import os
import boto3
from src.api_handler import create_handler
from src.vector_service import DatabaseConfig

# Get AWS region from Lambda runtime
aws_region = os.environ.get('AWS_REGION') or boto3.Session().region_name

config = DatabaseConfig(
    opensearch_endpoint=os.environ['OPENSEARCH_ENDPOINT'],
    rds_endpoint=os.environ['RDS_ENDPOINT'],
    rds_secret_arn=os.environ['RDS_SECRET_ARN'],
    aws_region=aws_region
)

api_handler = create_handler(config)

def handler(event, context):
    """Lambda function entry point"""
    return api_handler.handle_request(event) 
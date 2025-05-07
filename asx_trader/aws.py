"""
AWS integration module for cloud deployment.
"""
import json
import logging
from datetime import datetime
import boto3
from asx_trader.config import Config

logger = logging.getLogger(__name__)

class AWSDeployment:
    """Handles cloud deployment on AWS"""
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=Config.AWS_ACCESS_KEY,
            aws_secret_access_key=Config.AWS_SECRET_KEY,
            region_name=Config.AWS_REGION
        )
        self.bucket_name = Config.S3_BUCKET_NAME
        
    def save_trading_results(self, data, file_prefix):
        """Save trading results to S3"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            key = f"{file_prefix}_{timestamp}.json"
            
            self.s3_client.put_object(
                Body=json.dumps(data, indent=2),
                Bucket=self.bucket_name,
                Key=key,
                ContentType='application/json'
            )
            
            logger.info(f"Data saved to S3: s3://{self.bucket_name}/{key}")
            return f"s3://{self.bucket_name}/{key}"
        except Exception as e:
            logger.error(f"Error saving data to S3: {e}")
            return None
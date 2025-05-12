"""
Monitoring and alerting system for trading activity.
"""
import json
import logging
from datetime import datetime
import boto3
from asx_trader.config import Config

logger = logging.getLogger(__name__)

class MonitoringSystem:
    """Monitors trading activity and sends alerts"""
    def __init__(self):
        self.sns_client = boto3.client(
            'sns',
            aws_access_key_id=Config.AWS_ACCESS_KEY,
            aws_secret_access_key=Config.AWS_SECRET_KEY,
            region_name=Config.AWS_REGION
        )
        self.topic_arn = Config.SNS_TOPIC_ARN
        
    def send_notification(self, subject, message):
        """Send notification via AWS SNS"""
        try:
            response = self.sns_client.publish(
                TopicArn=self.topic_arn,
                Message=message,
                Subject=subject
            )
            logger.info(f"Notification sent: {subject}")
            return response
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return None
            
    def track_trading_activity(self, orders, signals, risk_assessment):
        """Track trading activity and send relevant notifications"""
        try:
            # Compile trade summary
            summary = {
                "timestamp": datetime.now().isoformat(),
                "orders": orders,
                "signals_count": len(signals),
                "overall_risk_level": risk_assessment.get("overall_risk_level", "Unknown")
            }
            
            # Log activity
            logger.info(f"Trading activity tracked: {len(orders)} orders placed")
            
            # Skip notification if no SNS topic is configured
            if not self.topic_arn:
                logger.warning("SNS Topic ARN not configured, skipping notifications")
                return True
                
            # Send notification with summary
            self.send_notification(
                f"Trading Summary - {datetime.now().strftime('%Y-%m-%d')}",
                json.dumps(summary, indent=2)
            )
            
            # Send alerts for high-risk trades
            for order in orders:
                if order.get("risk_level") in ["High", "Extreme"]:
                    alert_msg = f"HIGH RISK TRADE: {order.get('action')} {order.get('quantity')} {order.get('symbol')}"
                    self.send_notification("HIGH RISK TRADE ALERT", alert_msg)
                    
            return True
        except Exception as e:
            logger.error(f"Error tracking trading activity: {e}")
            return False
# Add to your trading/monitoring.py file
def track_api_usage(api_calls, tokens_used, analysis_type):
    """Track OpenAI API usage"""
    try:
        # Record in CloudWatch custom metrics
        cloudwatch_client.put_metric_data(
            Namespace='TradingSystem',
            MetricData=[
                {
                    'MetricName': 'APICallCount',
                    'Dimensions': [{'Name': 'AnalysisType', 'Value': analysis_type}],
                    'Value': api_calls
                },
                {
                    'MetricName': 'TokensUsed',
                    'Dimensions': [{'Name': 'AnalysisType', 'Value': analysis_type}],
                    'Value': tokens_used
                }
            ]
        )
        
        # Also log to database for cost analysis
        with db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO api_usage (timestamp, calls, tokens, analysis_type)
                    VALUES (NOW(), %s, %s, %s)
                    """,
                    (api_calls, tokens_used, analysis_type)
                )
    except Exception as e:
        logger.error(f"Error tracking API usage: {e}")
"""Monitoring Adapters for FleetOps

Datadog, Sentry, CloudWatch, Grafana
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from datetime import datetime

class BaseMonitoringAdapter(ABC):
    """Abstract monitoring adapter"""
    
    PROVIDER_NAME: str = "base"
    
    def __init__(self, api_key: str = None, config: Dict = None):
        self.api_key = api_key
        self.config = config or {}
    
    @abstractmethod
    async def log_event(self, event_type: str, data: Dict) -> bool:
        """Log an event"""
        pass
    
    @abstractmethod
    async def log_error(self, error: Exception, context: Dict = None) -> bool:
        """Log an error"""
        pass
    
    @abstractmethod
    async def record_metric(self, name: str, value: float,
                           tags: Dict = None) -> bool:
        """Record a metric"""
        pass
    
    @abstractmethod
    async def create_alert(self, name: str, condition: str,
                          threshold: float) -> Dict:
        """Create an alert"""
        pass

class SentryAdapter(BaseMonitoringAdapter):
    """Sentry.io error tracking"""
    
    PROVIDER_NAME = "sentry"
    
    def __init__(self, dsn: str = None, environment: str = "production"):
        super().__init__(api_key=dsn)
        self.dsn = dsn
        self.environment = environment
        
        # Initialize Sentry SDK if available
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=dsn,
                environment=environment,
                traces_sample_rate=1.0,
                profiles_sample_rate=1.0
            )
            self.sentry = sentry_sdk
        except ImportError:
            self.sentry = None
    
    async def log_event(self, event_type: str, data: Dict) -> bool:
        """Log event as Sentry breadcrumb"""
        if self.sentry:
            self.sentry.add_breadcrumb(
                category=event_type,
                data=data,
                level="info"
            )
            return True
        return False
    
    async def log_error(self, error: Exception, 
                       context: Dict = None) -> bool:
        """Capture exception in Sentry"""
        if self.sentry:
            with self.sentry.push_scope() as scope:
                if context:
                    for key, value in context.items():
                        scope.set_extra(key, value)
                self.sentry.capture_exception(error)
            return True
        return False
    
    async def record_metric(self, name: str, value: float,
                           tags: Dict = None) -> bool:
        """Sentry doesn't support custom metrics in free tier"""
        # Could use Sentry's metrics in paid tier
        return True
    
    async def create_alert(self, name: str, condition: str,
                          threshold: float) -> Dict:
        """Sentry alerts are configured via UI"""
        return {"status": "manual_config_required", "provider": "sentry"}
    
    async def track_performance(self, operation: str, 
                                duration_ms: float) -> bool:
        """Track performance with Sentry transactions"""
        if self.sentry:
            transaction = self.sentry.start_transaction(
                op=operation,
                name=f"fleetops_{operation}"
            )
            transaction.finish()
            return True
        return False

class DatadogAdapter(BaseMonitoringAdapter):
    """Datadog APM and monitoring"""
    
    PROVIDER_NAME = "datadog"
    
    def __init__(self, api_key: str = None, app_key: str = None):
        super().__init__(api_key=api_key)
        self.app_key = app_key
        self.base_url = "https://api.datadoghq.com/api/v1"
    
    async def log_event(self, event_type: str, data: Dict) -> bool:
        """Send event to Datadog"""
        import requests
        
        try:
            response = requests.post(
                f"{self.base_url}/events",
                headers={
                    "DD-API-KEY": self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "title": f"FleetOps: {event_type}",
                    "text": str(data),
                    "tags": ["fleetops", f"event:{event_type}"],
                    "alert_type": "info"
                }
            )
            return response.status_code == 202
        except Exception:
            return False
    
    async def log_error(self, error: Exception,
                       context: Dict = None) -> bool:
        """Send error to Datadog"""
        import requests
        
        try:
            response = requests.post(
                f"{self.base_url}/events",
                headers={
                    "DD-API-KEY": self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "title": f"FleetOps Error: {type(error).__name__}",
                    "text": str(error),
                    "tags": ["fleetops", "error", type(error).__name__],
                    "alert_type": "error"
                }
            )
            return response.status_code == 202
        except Exception:
            return False
    
    async def record_metric(self, name: str, value: float,
                           tags: Dict = None) -> bool:
        """Send metric to Datadog"""
        import requests
        
        try:
            tag_list = [f"{k}:{v}" for k, v in (tags or {}).items()]
            
            response = requests.post(
                f"{self.base_url}/series",
                headers={
                    "DD-API-KEY": self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "series": [{
                        "metric": f"fleetops.{name}",
                        "points": [[int(datetime.utcnow().timestamp()), value]],
                        "tags": tag_list,
                        "type": "gauge"
                    }]
                }
            )
            return response.status_code == 202
        except Exception:
            return False
    
    async def create_alert(self, name: str, condition: str,
                          threshold: float) -> Dict:
        """Create Datadog monitor"""
        import requests
        
        try:
            response = requests.post(
                f"https://api.datadoghq.com/api/v1/monitor",
                headers={
                    "DD-API-KEY": self.api_key,
                    "DD-APPLICATION-KEY": self.app_key,
                    "Content-Type": "application/json"
                },
                json={
                    "name": f"FleetOps: {name}",
                    "type": "metric alert",
                    "query": f"avg(last_5m):sum:fleetops.{condition} > {threshold}",
                    "message": f"Alert: {name} has exceeded threshold",
                    "tags": ["fleetops", "auto-generated"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {"status": "created", "monitor_id": data.get("id")}
            
            return {"status": "error"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class CloudWatchAdapter(BaseMonitoringAdapter):
    """AWS CloudWatch monitoring"""
    
    PROVIDER_NAME = "cloudwatch"
    
    def __init__(self, region: str = "us-east-1", 
                 log_group: str = "/fleetops/app"):
        super().__init__()
        self.region = region
        self.log_group = log_group
        
        try:
            import boto3
            self.client = boto3.client("logs", region_name=region)
            self.cloudwatch = boto3.client("cloudwatch", region_name=region)
        except ImportError:
            self.client = None
            self.cloudwatch = None
    
    async def log_event(self, event_type: str, data: Dict) -> bool:
        """Log to CloudWatch Logs"""
        if not self.client:
            return False
        
        try:
            import json
            from datetime import datetime
            
            self.client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=f"events/{datetime.utcnow().strftime('%Y/%m/%d')}",
                logEvents=[{
                    "timestamp": int(datetime.utcnow().timestamp() * 1000),
                    "message": json.dumps({
                        "event_type": event_type,
                        "data": data,
                        "source": "fleetops"
                    })
                }]
            )
            return True
        except Exception:
            return False
    
    async def log_error(self, error: Exception,
                       context: Dict = None) -> bool:
        """Log error to CloudWatch"""
        if not self.client:
            return False
        
        try:
            import json
            from datetime import datetime
            
            self.client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=f"errors/{datetime.utcnow().strftime('%Y/%m/%d')}",
                logEvents=[{
                    "timestamp": int(datetime.utcnow().timestamp() * 1000),
                    "message": json.dumps({
                        "error": str(error),
                        "type": type(error).__name__,
                        "context": context,
                        "source": "fleetops"
                    })
                }]
            )
            return True
        except Exception:
            return False
    
    async def record_metric(self, name: str, value: float,
                           tags: Dict = None) -> bool:
        """Put CloudWatch metric"""
        if not self.cloudwatch:
            return False
        
        try:
            dimensions = [
                {"Name": k, "Value": str(v)}
                for k, v in (tags or {}).items()
            ]
            
            self.cloudwatch.put_metric_data(
                Namespace="FleetOps",
                MetricData=[{
                    "MetricName": name,
                    "Value": value,
                    "Unit": "Count",
                    "Dimensions": dimensions,
                    "Timestamp": datetime.utcnow()
                }]
            )
            return True
        except Exception:
            return False
    
    async def create_alert(self, name: str, condition: str,
                          threshold: float) -> Dict:
        """Create CloudWatch alarm"""
        if not self.cloudwatch:
            return {"status": "error", "message": "CloudWatch not configured"}
        
        try:
            self.cloudwatch.put_metric_alarm(
                AlarmName=f"FleetOps-{name}",
                AlarmDescription=f"Auto-generated alert for {name}",
                MetricName=condition,
                Namespace="FleetOps",
                Statistic="Average",
                Period=300,
                EvaluationPeriods=1,
                Threshold=threshold,
                ComparisonOperator="GreaterThanThreshold"
            )
            return {"status": "created"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Registry
MONITORING_ADAPTERS = {
    "sentry": SentryAdapter,
    "datadog": DatadogAdapter,
    "cloudwatch": CloudWatchAdapter,
    "grafana": SentryAdapter,  # TODO: Implement Grafana
    "none": SentryAdapter  # No-op adapter
}

def get_monitoring_adapter(provider: str, config: Dict = None):
    """Get monitoring adapter"""
    adapter_class = MONITORING_ADAPTERS.get(provider)
    if not adapter_class:
        raise ValueError(f"Unknown monitoring provider: {provider}")
    
    return adapter_class(**(config or {}))

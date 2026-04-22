"""Webhook Service for FleetOps

Features:
- Outbound webhooks for events
- Retry logic with exponential backoff
- Signature verification
- Event filtering
"""

import hmac
import hashlib
import json
import asyncio
from datetime import datetime
from typing import Optional, Dict, List
import aiohttp

from app.models.models import Event, Task, Approval

class WebhookService:
    """Webhook delivery and management"""
    
    def __init__(self):
        self.webhooks: Dict[str, Dict] = {}  # org_id -> webhook config
        self.retry_delays = [1, 2, 4, 8, 16, 32, 64]  # Exponential backoff
    
    def register_webhook(self, org_id: str, url: str, 
                         events: List[str], secret: str,
                         headers: Optional[Dict] = None) -> Dict:
        """Register a webhook for an organization"""
        webhook_id = f"wh_{org_id}_{hashlib.md5(url.encode()).hexdigest()[:8]}"
        
        self.webhooks[org_id] = {
            "id": webhook_id,
            "url": url,
            "events": events,
            "secret": secret,
            "headers": headers or {},
            "active": True,
            "created_at": datetime.utcnow().isoformat(),
            "delivery_count": 0,
            "failure_count": 0
        }
        
        return {"webhook_id": webhook_id, "status": "registered"}
    
    def generate_signature(self, payload: str, secret: str) -> str:
        """Generate HMAC signature for webhook"""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
    
    async def deliver_event(self, org_id: str, event_type: str, 
                           payload: Dict) -> Dict:
        """Deliver event to registered webhook"""
        if org_id not in self.webhooks:
            return {"status": "no_webhook"}
        
        webhook = self.webhooks[org_id]
        
        if not webhook["active"]:
            return {"status": "inactive"}
        
        if event_type not in webhook["events"] and "*" not in webhook["events"]:
            return {"status": "event_filtered"}
        
        # Prepare payload
        delivery_payload = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "webhook_id": webhook["id"],
            "data": payload
        }
        
        payload_str = json.dumps(delivery_payload)
        signature = self.generate_signature(payload_str, webhook["secret"])
        
        headers = {
            "Content-Type": "application/json",
            "X-FleetOps-Signature": f"sha256={signature}",
            "X-FleetOps-Event": event_type,
            "X-FleetOps-Delivery-ID": f"del_{datetime.utcnow().timestamp()}",
            **webhook["headers"]
        }
        
        # Attempt delivery with retries
        for attempt, delay in enumerate(self.retry_delays):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        webhook["url"],
                        data=payload_str,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status < 400:
                            webhook["delivery_count"] += 1
                            return {
                                "status": "delivered",
                                "attempt": attempt + 1,
                                "http_status": response.status
                            }
                        else:
                            raise Exception(f"HTTP {response.status}")
            except Exception as e:
                if attempt < len(self.retry_delays) - 1:
                    await asyncio.sleep(delay)
                else:
                    webhook["failure_count"] += 1
                    return {
                        "status": "failed",
                        "attempts": attempt + 1,
                        "error": str(e)
                    }
        
        return {"status": "failed", "error": "Max retries exceeded"}
    
    async def handle_task_event(self, task: Task, event_type: str) -> None:
        """Handle task-related events"""
        payload = {
            "task_id": task.id,
            "title": task.title,
            "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
            "stage": task.stage,
            "risk_level": task.risk_level.value if hasattr(task.risk_level, 'value') else str(task.risk_level),
            "agent_id": task.agent_id,
            "org_id": task.org_id
        }
        
        await self.deliver_event(task.org_id, event_type, payload)
    
    async def handle_approval_event(self, approval: Approval, 
                                    event_type: str) -> None:
        """Handle approval-related events"""
        payload = {
            "approval_id": approval.id,
            "task_id": approval.task_id,
            "stage": approval.stage,
            "decision": approval.decision,
            "human_id": approval.human_id,
            "comments": approval.comments,
            "resolved_at": approval.resolved_at.isoformat() if approval.resolved_at else None
        }
        
        # Get org_id from task
        # This would need to be fetched from DB in real implementation
        await self.deliver_event("default", event_type, payload)
    
    def get_webhook_status(self, org_id: str) -> Dict:
        """Get webhook status for organization"""
        if org_id not in self.webhooks:
            return {"status": "not_registered"}
        
        webhook = self.webhooks[org_id]
        return {
            "webhook_id": webhook["id"],
            "url": webhook["url"],
            "events": webhook["events"],
            "active": webhook["active"],
            "delivery_count": webhook["delivery_count"],
            "failure_count": webhook["failure_count"],
            "success_rate": webhook["delivery_count"] / (webhook["delivery_count"] + webhook["failure_count"]) * 100 if (webhook["delivery_count"] + webhook["failure_count"]) > 0 else 0,
            "created_at": webhook["created_at"]
        }

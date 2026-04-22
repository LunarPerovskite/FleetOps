"""Webhook Event System for FleetOps

Send real-time events to external systems with retry logic
"""

import asyncio
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import aiohttp

from app.core.database import get_db
from app.models.models import Webhook, Event

class WebhookEventSystem:
    """System for sending webhook events to external URLs"""
    
    def __init__(self):
        self.retry_delays = [1, 5, 15, 60, 300]  # Seconds between retries
        self.max_retries = 5
    
    async def send_event(self, webhook_id: str, event: dict) -> bool:
        """Send event to webhook URL with retries"""
        db = next(get_db())
        webhook = db.query(Webhook).filter(Webhook.id == webhook_id).first()
        
        if not webhook or not webhook.active:
            return False
        
        payload = {
            "event_id": event.get("id"),
            "event_type": event.get("event_type"),
            "timestamp": datetime.utcnow().isoformat(),
            "data": event,
            "webhook_id": webhook_id
        }
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "FleetOps-Webhook/0.1.0",
            "X-Webhook-ID": webhook_id,
            "X-Event-Type": event.get("event_type", "unknown")
        }
        
        # Add signature if secret is configured
        if webhook.secret:
            signature = self._sign_payload(payload, webhook.secret)
            headers["X-Webhook-Signature"] = signature
        
        # Attempt delivery with retries
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        webhook.url,
                        json=payload,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        if response.status < 400:
                            # Success
                            self._record_delivery(db, webhook_id, event["id"], "success", response.status)
                            return True
                        else:
                            # Failed, will retry
                            self._record_delivery(db, webhook_id, event["id"], "failed", response.status, attempt + 1)
                            
            except Exception as e:
                self._record_delivery(db, webhook_id, event["id"], "error", None, attempt + 1, str(e))
            
            # Wait before retry (except last attempt)
            if attempt < self.max_retries - 1:
                delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                await asyncio.sleep(delay)
        
        # All retries exhausted
        self._disable_webhook_if_needed(db, webhook_id)
        return False
    
    def _sign_payload(self, payload: dict, secret: str) -> str:
        """Sign payload with HMAC-SHA256"""
        payload_json = json.dumps(payload, sort_keys=True)
        return hmac.new(
            secret.encode(),
            payload_json.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def _record_delivery(self, db, webhook_id: str, event_id: str, status: str, http_status: Optional[int], attempt: int = 1, error: Optional[str] = None):
        """Record delivery attempt"""
        # In production, store in database
        print(f"Webhook {webhook_id}: Event {event_id} - {status} (HTTP {http_status}, Attempt {attempt})" + (f" Error: {error}" if error else ""))
    
    def _disable_webhook_if_needed(self, db, webhook_id: str):
        """Disable webhook after too many failures"""
        # Count recent failures
        # If > 10 failures in 24h, disable webhook
        pass  # Implement in production
    
    async def broadcast_event(self, org_id: str, event: dict):
        """Send event to all active webhooks for organization"""
        db = next(get_db())
        webhooks = db.query(Webhook).filter(
            Webhook.org_id == org_id,
            Webhook.active == True
        ).all()
        
        tasks = []
        for webhook in webhooks:
            # Check if webhook is subscribed to this event type
            if self._should_send(webhook, event.get("event_type")):
                tasks.append(self.send_event(webhook.id, event))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    def _should_send(self, webhook: Webhook, event_type: str) -> bool:
        """Check if webhook should receive this event type"""
        if not webhook.events:
            return True  # Send all events if not filtered
        
        subscribed_events = webhook.events.split(",")
        return event_type in subscribed_events or "*" in subscribed_events
    
    async def test_webhook(self, webhook_id: str) -> dict:
        """Test webhook with a ping event"""
        test_event = {
            "id": "test_" + webhook_id,
            "event_type": "webhook_test",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "This is a test event from FleetOps"
        }
        
        success = await self.send_event(webhook_id, test_event)
        return {
            "webhook_id": webhook_id,
            "success": success,
            "test_event": test_event
        }

# Initialize webhook system
webhook_system = WebhookEventSystem()

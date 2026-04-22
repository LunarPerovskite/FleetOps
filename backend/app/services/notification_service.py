"""Notification Service for FleetOps

Features:
- Multi-channel notifications (email, SMS, push, Slack, Discord)
- Real-time alerts for critical events
- Notification preferences per user
- Digest mode (hourly/daily summaries)
- Escalation chains
"""

import json
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from enum import Enum

class NotificationChannel(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    IN_APP = "in_app"

class NotificationPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationService:
    """Multi-channel notification delivery"""
    
    def __init__(self):
        self.notification_queue: List[Dict] = []
        self.user_preferences: Dict[str, Dict] = {}
        self.escalation_chains: Dict[str, List[str]] = {}
    
    def set_user_preferences(self, user_id: str, preferences: Dict):
        """Set notification preferences for user"""
        self.user_preferences[user_id] = {
            "channels": preferences.get("channels", ["email", "in_app"]),
            "priority_threshold": preferences.get("priority_threshold", "medium"),
            "digest_mode": preferences.get("digest_mode", "realtime"),  # realtime, hourly, daily
            "digest_time": preferences.get("digest_time", "09:00"),
            "quiet_hours": preferences.get("quiet_hours", {"start": "22:00", "end": "08:00"}),
            "enabled": preferences.get("enabled", True)
        }
    
    def send_notification(self, user_id: str, title: str, message: str,
                         priority: NotificationPriority = NotificationPriority.MEDIUM,
                         channels: Optional[List[NotificationChannel]] = None,
                         data: Optional[Dict] = None) -> Dict:
        """Send notification to user"""
        prefs = self.user_preferences.get(user_id, {})
        
        if not prefs.get("enabled", True):
            return {"status": "disabled"}
        
        # Check priority threshold
        priority_levels = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        if priority_levels.get(priority.value, 0) < priority_levels.get(prefs.get("priority_threshold", "medium"), 2):
            return {"status": "filtered", "reason": "priority_too_low"}
        
        # Check quiet hours (except critical)
        if priority != NotificationPriority.CRITICAL:
            now = datetime.utcnow()
            quiet_start = datetime.strptime(prefs.get("quiet_hours", {}).get("start", "22:00"), "%H:%M").time()
            quiet_end = datetime.strptime(prefs.get("quiet_hours", {}).get("end", "08:00"), "%H:%M").time()
            current_time = now.time()
            
            if quiet_start <= quiet_end:
                if quiet_start <= current_time <= quiet_end:
                    return {"status": "queued", "reason": "quiet_hours"}
            else:
                if current_time >= quiet_start or current_time <= quiet_end:
                    return {"status": "queued", "reason": "quiet_hours"}
        
        # Determine channels
        target_channels = channels or [NotificationChannel(ch) for ch in prefs.get("channels", ["email", "in_app"])]
        
        notification = {
            "id": f"notif_{datetime.utcnow().timestamp()}_{user_id}",
            "user_id": user_id,
            "title": title,
            "message": message,
            "priority": priority.value,
            "channels": [ch.value for ch in target_channels],
            "data": data or {},
            "timestamp": datetime.utcnow().isoformat(),
            "read": False
        }
        
        # Add to queue
        self.notification_queue.append(notification)
        
        # Send based on digest mode
        if prefs.get("digest_mode") == "realtime":
            asyncio.create_task(self._deliver_notification(notification))
        else:
            return {"status": "queued", "digest_mode": prefs.get("digest_mode")}
        
        return {"status": "sent", "notification_id": notification["id"]}
    
    async def _deliver_notification(self, notification: Dict):
        """Deliver notification to all channels"""
        for channel in notification["channels"]:
            try:
                if channel == "email":
                    await self._send_email(notification)
                elif channel == "sms":
                    await self._send_sms(notification)
                elif channel == "push":
                    await self._send_push(notification)
                elif channel == "slack":
                    await self._send_slack(notification)
                elif channel == "discord":
                    await self._send_discord(notification)
                elif channel == "in_app":
                    await self._send_in_app(notification)
            except Exception as e:
                print(f"Failed to send {channel}: {e}")
    
    async def _send_email(self, notification: Dict):
        """Send email notification"""
        # Integration with email service
        print(f"📧 Email to {notification['user_id']}: {notification['title']}")
    
    async def _send_sms(self, notification: Dict):
        """Send SMS notification"""
        # Integration with SMS service (Twilio)
        print(f"📱 SMS to {notification['user_id']}: {notification['title']}")
    
    async def _send_push(self, notification: Dict):
        """Send push notification"""
        # Integration with push service (FCM/APNs)
        print(f"🔔 Push to {notification['user_id']}: {notification['title']}")
    
    async def _send_slack(self, notification: Dict):
        """Send Slack notification"""
        # Integration with Slack webhook
        print(f"💬 Slack to {notification['user_id']}: {notification['title']}")
    
    async def _send_discord(self, notification: Dict):
        """Send Discord notification"""
        # Integration with Discord webhook
        print(f"🎮 Discord to {notification['user_id']}: {notification['title']}")
    
    async def _send_in_app(self, notification: Dict):
        """Send in-app notification"""
        # Store in user's notification center
        print(f"📌 In-app to {notification['user_id']}: {notification['title']}")
    
    def get_user_notifications(self, user_id: str, 
                               unread_only: bool = False,
                               limit: int = 50) -> List[Dict]:
        """Get notifications for user"""
        notifications = [n for n in self.notification_queue if n["user_id"] == user_id]
        
        if unread_only:
            notifications = [n for n in notifications if not n["read"]]
        
        return sorted(notifications, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    def mark_as_read(self, notification_id: str) -> bool:
        """Mark notification as read"""
        for notification in self.notification_queue:
            if notification["id"] == notification_id:
                notification["read"] = True
                return True
        return False
    
    def setup_escalation_chain(self, org_id: str, chain: List[Dict]):
        """Setup escalation chain for critical alerts"""
        self.escalation_chains[org_id] = chain
    
    async def escalate_notification(self, org_id: str, original_notification: Dict):
        """Escalate notification through chain"""
        chain = self.escalation_chains.get(org_id, [])
        
        for level in chain:
            user_id = level.get("user_id")
            delay = level.get("delay_minutes", 0)
            
            if delay > 0:
                await asyncio.sleep(delay * 60)
            
            self.send_notification(
                user_id=user_id,
                title=f"[ESCALATED] {original_notification['title']}",
                message=original_notification['message'],
                priority=NotificationPriority.CRITICAL,
                data={"escalation": True, "original": original_notification}
            )
    
    async def send_digest(self, user_id: str):
        """Send digest notification for queued items"""
        prefs = self.user_preferences.get(user_id, {})
        digest_mode = prefs.get("digest_mode", "realtime")
        
        if digest_mode == "realtime":
            return
        
        # Get queued notifications
        queued = [n for n in self.notification_queue 
                  if n["user_id"] == user_id and not n.get("sent", False)]
        
        if not queued:
            return
        
        # Mark as sent
        for notification in queued:
            notification["sent"] = True
        
        # Send digest
        self.send_notification(
            user_id=user_id,
            title=f"FleetOps Digest ({len(queued)} notifications)",
            message=f"You have {len(queued)} notifications from the past {digest_mode}.",
            priority=NotificationPriority.MEDIUM,
            channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
            data={"digest": True, "count": len(queued), "notifications": queued}
        )


# Global notification service instance
notification_service = NotificationService()

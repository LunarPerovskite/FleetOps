"""Slack Bot Integration for FleetOps

Connect FleetOps to Slack for notifications and commands
"""

import os
from typing import Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from app.services.notification_service import notification_service

class SlackBotAdapter:
    """Slack bot for FleetOps notifications"""
    
    def __init__(self):
        self.token = os.getenv("SLACK_BOT_TOKEN")
        self.client = WebClient(token=self.token) if self.token else None
        self.enabled = self.client is not None
    
    async def send_task_notification(self, channel: str, task: dict):
        """Send task update to Slack channel"""
        if not self.enabled:
            return
        
        try:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"Task Update: {task['title']}"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Status:*\n{task['status']}"},
                        {"type": "mrkdwn", "text": f"*Agent:*\n{task.get('agent_name', 'N/A')}"},
                        {"type": "mrkdwn", "text": f"*Priority:*\n{task.get('priority', 'N/A')}"},
                        {"type": "mrkdwn", "text": f"*Risk:*\n{task.get('risk_level', 'N/A')}"}
                    ]
                }
            ]
            
            await self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=f"Task update: {task['title']}"
            )
        except SlackApiError as e:
            print(f"Slack notification failed: {e}")
    
    async def send_approval_request(self, channel: str, approval: dict):
        """Send approval request with interactive buttons"""
        if not self.enabled:
            return
        
        try:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🔍 Approval Required"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Task:* {approval['task_title']}\n*Stage:* {approval['stage']}\n*Requested by:* {approval.get('agent_name', 'System')}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "✅ Approve"},
                            "style": "primary",
                            "value": f"approve_{approval['id']}",
                            "action_id": "approve_task"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "❌ Reject"},
                            "style": "danger",
                            "value": f"reject_{approval['id']}",
                            "action_id": "reject_task"
                        },
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "⬆️ Escalate"},
                            "value": f"escalate_{approval['id']}",
                            "action_id": "escalate_task"
                        }
                    ]
                }
            ]
            
            await self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=f"Approval required: {approval['task_title']}"
            )
        except SlackApiError as e:
            print(f"Slack approval request failed: {e}")
    
    async def send_daily_summary(self, channel: str, stats: dict):
        """Send daily activity summary"""
        if not self.enabled:
            return
        
        try:
            text = f"""
📊 *FleetOps Daily Summary*

• Tasks completed: {stats.get('tasks_completed', 0)}
• Tasks created: {stats.get('tasks_created', 0)}
• Approvals pending: {stats.get('pending_approvals', 0)}
• Active agents: {stats.get('active_agents', 0)}
• Cost today: ${stats.get('cost_today', 0):.2f}

View dashboard: {os.getenv('FRONTEND_URL', 'http://localhost:3000')}
            """
            
            await self.client.chat_postMessage(
                channel=channel,
                text=text
            )
        except SlackApiError as e:
            print(f"Slack summary failed: {e}")

# Initialize adapter
slack_bot = SlackBotAdapter()

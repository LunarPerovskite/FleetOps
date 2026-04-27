"""Slack Integration for FleetOps Approval Flow

Sends approval requests to Slack and receives responses.
Supports:
- Incoming webhooks (send messages)
- Interactive messages (buttons, emoji reactions)
- Slash commands (/fleetops status, /fleetops approve)
- Real-time messaging via Socket Mode
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import json
import httpx


@dataclass
class SlackMessage:
    """A Slack message for approval requests"""
    channel: str
    text: str
    blocks: Optional[List[Dict[str, Any]]] = None
    thread_ts: Optional[str] = None


class SlackIntegration:
    """Slack integration for FleetOps approvals"""
    
    def __init__(self, 
                 webhook_url: Optional[str] = None,
                 bot_token: Optional[str] = None,
                 app_token: Optional[str] = None):
        self.webhook_url = webhook_url
        self.bot_token = bot_token
        self.app_token = app_token
        self._http_client = httpx.AsyncClient()
    
    async def send_approval_request(
        self,
        approval_id: str,
        title: str,
        description: str,
        requester_name: str,
        danger_level: str,
        estimated_cost: Optional[float],
        channel: str = "#approvals"
    ) -> Dict[str, Any]:
        """Send an approval request to Slack with interactive buttons"""
        
        # Danger level emoji mapping
        danger_emojis = {
            "safe": "🟢",
            "low": "🟡",
            "medium": "🟠",
            "high": "🔴",
            "critical": "🚨"
        }
        emoji = danger_emojis.get(danger_level, "⚪")
        
        # Cost display
        cost_text = f"${estimated_cost:.2f}" if estimated_cost else "N/A"
        
        # Build interactive message with buttons
        message = {
            "channel": channel,
            "text": f"{emoji} Approval Request: {title}",
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} Approval Request",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Title:*\n{title}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Requested by:*\n{requester_name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Danger Level:*\n{danger_level.upper()}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Estimated Cost:*\n{cost_text}"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Description:*\n{description}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "✅ Approve",
                                "emoji": True
                            },
                            "style": "primary",
                            "value": approval_id,
                            "action_id": f"approve_{approval_id}"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "❌ Reject",
                                "emoji": True
                            },
                            "style": "danger",
                            "value": approval_id,
                            "action_id": f"reject_{approval_id}"
                        },
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "🔍 View Details",
                                "emoji": True
                            },
                            "value": approval_id,
                            "action_id": f"details_{approval_id}"
                        }
                    ]
                }
            ]
        }
        
        return await self._send_message(message)
    
    async def send_cost_alert(
        self,
        org_id: str,
        current_cost: float,
        budget_limit: float,
        channel: str = "#cost-alerts"
    ) -> Dict[str, Any]:
        """Send budget warning to Slack"""
        
        percentage = (current_cost / budget_limit) * 100 if budget_limit > 0 else 0
        
        # Determine severity
        if percentage >= 90:
            emoji = "🔴"
            text = f"CRITICAL: Budget at {percentage:.1f}%"
        elif percentage >= 75:
            emoji = "🟠"
            text = f"WARNING: Budget at {percentage:.1f}%"
        else:
            emoji = "🟡"
            text = f"Budget alert: {percentage:.1f}%"
        
        message = {
            "channel": channel,
            "text": text,
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} Budget Alert",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Current Cost:*\n${current_cost:.2f}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Budget Limit:*\n${budget_limit:.2f}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Used:*\n{percentage:.1f}%"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Remaining:*\n${budget_limit - current_cost:.2f}"
                        }
                    ]
                }
            ]
        }
        
        return await self._send_message(message)
    
    async def send_agent_status(
        self,
        agent_name: str,
        status: str,
        current_task: Optional[str],
        channel: str = "#agent-updates"
    ) -> Dict[str, Any]:
        """Send agent status update to Slack"""
        
        status_emojis = {
            "running": "🟢",
            "paused": "⏸️",
            "waiting_approval": "⏳",
            "error": "🔴",
            "completed": "✅"
        }
        emoji = status_emojis.get(status, "⚪")
        
        message = {
            "channel": channel,
            "text": f"{emoji} Agent {agent_name}: {status}",
            "blocks": [
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Agent:*\n{agent_name}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Status:*\n{emoji} {status.replace('_', ' ').title()}"
                        }
                    ]
                }
            ]
        }
        
        if current_task:
            message["blocks"].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Current Task:*\n{current_task}"
                }
            })
        
        return await self._send_message(message)
    
    async def handle_interactive_response(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle interactive button clicks from Slack"""
        
        action = payload.get("actions", [{}])[0]
        action_id = action.get("action_id", "")
        approval_id = action.get("value", "")
        user_id = payload.get("user", {}).get("id")
        
        # Parse action type
        if action_id.startswith("approve_"):
            return {
                "approval_id": approval_id,
                "decision": "approved",
                "approver_id": user_id,
                "message": "Approved via Slack"
            }
        elif action_id.startswith("reject_"):
            return {
                "approval_id": approval_id,
                "decision": "rejected",
                "approver_id": user_id,
                "message": "Rejected via Slack"
            }
        elif action_id.startswith("details_"):
            return {
                "approval_id": approval_id,
                "decision": "view_details",
                "approver_id": user_id,
                "message": "Viewing details"
            }
        
        return {
            "approval_id": approval_id,
            "decision": "unknown",
            "approver_id": user_id,
            "message": "Unknown action"
        }
    
    async def _send_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Send message via Slack API"""
        
        if self.webhook_url:
            # Use incoming webhook
            try:
                response = await self._http_client.post(
                    self.webhook_url,
                    json=message
                )
                return {
                    "success": response.status_code == 200,
                    "status_code": response.status_code,
                    "method": "webhook"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "method": "webhook"
                }
        
        elif self.bot_token:
            # Use Slack API directly
            try:
                response = await self._http_client.post(
                    "https://slack.com/api/chat.postMessage",
                    headers={"Authorization": f"Bearer {self.bot_token}"},
                    json=message
                )
                data = response.json()
                return {
                    "success": data.get("ok", False),
                    "response": data,
                    "method": "api"
                }
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e),
                    "method": "api"
                }
        
        else:
            return {
                "success": False,
                "error": "No Slack webhook or bot token configured",
                "method": "none"
            }
    
    async def close(self):
        """Close HTTP client"""
        await self._http_client.aclose()


# Global instance
slack_integration = SlackIntegration()

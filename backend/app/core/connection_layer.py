"""FleetOps Connection Layer — Webhook Handler

This is the bridge between agents (Claude Code, Copilot, etc.) and FleetOps.
Agents call FleetOps webhooks to request approval.
FleetOps sends notifications via Slack, Email, CLI, or Dashboard.

Flow:
1. Agent sends webhook to FleetOps
2. FleetOps detects danger level
3. FleetOps routes to right approvers (hierarchy)
4. FleetOps sends notification (Slack, Email, etc.)
5. Approver responds via any channel
6. FleetOps tells agent: GO or BLOCK
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import uuid
import asyncio

from app.core.danger_detector import DangerDetector, analyze_action
from app.core.hierarchy_escalation import get_approvers
from app.core.approval_flow import ApprovalFlow, ApprovalStage
from app.services.slack_integration import SlackIntegration
from app.core.logging_config import get_logger

logger = get_logger("fleetops.connection_layer")


@dataclass
class AgentRequest:
    """Request from an agent to FleetOps"""
    agent_id: str
    agent_name: str
    agent_type: str  # "claude_code", "copilot", "roo_code", "crewai", etc.
    action: str      # "bash", "write", "read", "api", "db", etc.
    environment: str
    arguments: Optional[str] = None
    file_path: Optional[str] = None
    estimated_cost: Optional[float] = None
    estimated_tokens: Optional[int] = None
    org_id: str = "default"
    requester_id: str = ""


class FleetOpsConnectionLayer:
    """Central connection layer for all agent approvals"""
    
    def __init__(self):
        self.danger_detector = DangerDetector()
        self.approval_flow = ApprovalFlow()
        self.slack = SlackIntegration()
        self._pending_callbacks: Dict[str, asyncio.Event] = {}
    
    async def process_agent_request(self, request: AgentRequest) -> Dict[str, Any]:
        """Process an approval request from any agent
        
        This is the main entry point for all agent approvals.
        """
        
        logger.info(
            f"Processing request from {request.agent_name} ({request.agent_type}): "
            f"{request.action} - {request.arguments[:50] if request.arguments else 'N/A'}"
        )
        
        # Step 1: Detect danger level
        danger = analyze_action(
            tool=request.action,
            arguments=request.arguments,
            file_path=request.file_path,
            environment=request.environment,
            estimated_cost=request.estimated_cost,
            estimated_tokens=request.estimated_tokens,
            org_id=request.org_id
        )
        
        danger_level = danger["danger_level"]
        requires_approval = danger["requires_approval"]
        approver_count = danger["approver_count"]
        
        logger.info(
            f"Danger analysis: {danger_level} (score: {danger['score']:.2f}), "
            f"requires_approval={requires_approval}, approvers_needed={approver_count}"
        )
        
        # Step 2: If safe, auto-approve
        if not requires_approval:
            details = danger.get("details", "No danger detected")
            logger.info(f"Auto-approved: {details}")
            return {
                "status": "auto_approved",
                "danger_level": danger_level,
                "score": danger.get("score", 0.0),
                "message": details,
                "agent_id": request.agent_id,
                "can_proceed": True
            }
        
        # Step 3: Route to approvers
        approvers = get_approvers(
            action_type=request.action,
            danger_level=danger_level,
            requester_id=request.requester_id or request.agent_id,
            org_id=request.org_id,
            estimated_cost=request.estimated_cost or 0.0
        )
        
        logger.info(f"Routing to approvers: {approvers}")
        
        # Step 4: Create approval request
        approval_id = str(uuid.uuid4())
        
        approval = await self.approval_flow.request_approval(
            task_id=request.agent_id,
            stage=ApprovalStage.EXTERNAL_ACTION,
            title=f"{request.agent_name}: {request.action}",
            description=danger["details"],
            requester_id=request.agent_id,
            approver_ids=approvers,
            metadata={
                "agent_type": request.agent_type,
                "danger_analysis": danger,
                "arguments": request.arguments,
                "file_path": request.file_path,
                "environment": request.environment
            }
        )
        
        # Step 5: Notify via channels based on danger level
        await self._notify_channels(
            approval_id=approval["id"],
            request=request,
            danger=danger,
            approvers=approvers
        )
        
        # Step 6: Wait for approval (blocking)
        logger.info(f"Waiting for approval {approval['id']}...")
        result = await self.approval_flow.wait_for_approval(
            approval_id=approval["id"],
            timeout=3600  # 1 hour timeout
        )
        
        # Step 7: Return result to agent
        if result["status"] == "approved":
            return {
                "status": "approved",
                "approval_id": approval["id"],
                "danger_level": danger_level,
                "message": "Approved. Agent can proceed.",
                "agent_id": request.agent_id,
                "can_proceed": True
            }
        elif result["status"] == "timeout":
            return {
                "status": "timeout",
                "approval_id": approval["id"],
                "danger_level": danger_level,
                "message": "Approval timed out. Agent should retry or escalate.",
                "agent_id": request.agent_id,
                "can_proceed": False
            }
        else:
            return {
                "status": "rejected",
                "approval_id": approval["id"],
                "danger_level": danger_level,
                "message": "Rejected. Agent must stop.",
                "agent_id": request.agent_id,
                "can_proceed": False
            }
    
    async def _notify_channels(
        self,
        approval_id: str,
        request: AgentRequest,
        danger: Dict[str, Any],
        approvers: List[str]
    ) -> None:
        """Send notifications through appropriate channels based on danger level"""
        
        danger_level = danger["danger_level"]
        
        # Channel routing rules
        channel_routing = {
            "safe": ["log"],
            "low": ["log"],
            "medium": ["dashboard", "email"],
            "high": ["slack", "dashboard", "email"],
            "critical": ["slack", "dashboard", "email", "cli"]
        }
        
        channels = channel_routing.get(danger_level, ["dashboard"])
        
        logger.info(f"Routing to channels: {channels} for danger level: {danger_level}")
        
        # Send to Slack
        if "slack" in channels:
            try:
                await self.slack.send_approval_request(
                    approval_id=approval_id,
                    title=f"{request.agent_name}: {request.action}",
                    description=danger.get("details", "Approval required"),
                    requester_name=request.agent_name,
                    danger_level=danger_level,
                    estimated_cost=request.estimated_cost
                )
                logger.info(f"Slack notification sent for {approval_id}")
            except Exception as e:
                logger.error(f"Failed to send Slack notification: {e}")
        
        # Send to Dashboard (always for medium+)
        if "dashboard" in channels:
            logger.info(f"Dashboard notification queued for {approval_id}")
            # Dashboard notifications are stored in DB and polled by frontend
        
        # Send email
        if "email" in channels:
            logger.info(f"Email notification queued for {approval_id}")
            # Email would be sent via SendGrid/Resend
        
        # Send CLI notification
        if "cli" in channels:
            logger.info(f"CLI notification queued for {approval_id}")
            # CLI notifications are stored for `fleetops approve` command
        
        # Always log
        logger.info(f"Approval request logged: {approval_id}")
    
    async def handle_approval_response(
        self,
        approval_id: str,
        decision: str,  # "approve" or "reject"
        approver_id: str,
        comments: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle approval response from any channel (Slack, CLI, Dashboard, Email)"""
        
        logger.info(
            f"Approval response: {decision} for {approval_id} by {approver_id}"
        )
        
        try:
            result = await self.approval_flow.approve(
                approval_id=approval_id,
                approver_id=approver_id,
                decision=decision,
                comments=comments
            )
            
            # Notify agent
            logger.info(f"Approval {approval_id} resolved: {decision}")
            
            return {
                "status": "success",
                "approval_id": approval_id,
                "decision": decision,
                "message": f"Approval {decision}d successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to process approval response: {e}")
            return {
                "status": "error",
                "approval_id": approval_id,
                "error": str(e)
            }


# Singleton
connection_layer = FleetOpsConnectionLayer()


# ═══════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════

async def request_agent_approval(
    agent_id: str,
    agent_name: str,
    agent_type: str,
    action: str,
    arguments: Optional[str] = None,
    file_path: Optional[str] = None,
    environment: str = "development",
    estimated_cost: Optional[float] = None,
    org_id: str = "default",
    requester_id: str = ""
) -> Dict[str, Any]:
    """Convenience function for agents to request approval"""
    
    request = AgentRequest(
        agent_id=agent_id,
        agent_name=agent_name,
        agent_type=agent_type,
        action=action,
        arguments=arguments,
        file_path=file_path,
        environment=environment,
        estimated_cost=estimated_cost,
        org_id=org_id,
        requester_id=requester_id
    )
    
    return await connection_layer.process_agent_request(request)


async def approve_from_channel(
    approval_id: str,
    decision: str,
    approver_id: str,
    comments: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience function for any channel to approve/reject"""
    
    return await connection_layer.handle_approval_response(
        approval_id=approval_id,
        decision=decision,
        approver_id=approver_id,
        comments=comments
    )

"""Agent Execution Service for FleetOps

Orchestrates task execution through personal AI agents:
- OpenClaw, Hermes, or any adapter-based agent
- Handles the full lifecycle: submit → execute → approve → complete
- Manages polling, timeouts, and error recovery
- Creates FleetOps approvals for human review
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import logging

from app.adapters.personal_agent_adapter import PersonalAgentAdapter, AgentType
from app.adapters.personal_agent_adapter import PersonalAgentAdapter, AgentType
from app.services.service_stubs import task_service, approval_service, notification_service, event_service

logger = logging.getLogger(__name__)

class AgentExecutionService:
    """Service for executing FleetOps tasks through AI agents
    
    Orchestrates the full flow:
    1. FleetOps task created and assigned to agent
    2. Human clicks "Execute with Agent"
    3. This service submits task to agent
    4. Agent executes (with optional step-by-step approval)
    5. Results come back to FleetOps
    6. FleetOps creates approval request for human
    7. Human reviews and approves/rejects
    8. If approved, task marked complete; if rejected, agent retries or fails
    """
    
    def __init__(self):
        self._active_executions: Dict[str, Dict] = {}
        self._polling_tasks: Dict[str, asyncio.Task] = {}
    
    async def execute_task(self, task_id: str, agent_type: str = "openclaw",
                          auto_approve_low_risk: bool = False) -> Dict[str, Any]:
        """Execute a FleetOps task using the specified agent
        
        Args:
            task_id: FleetOps task ID
            agent_type: Type of agent (openclaw, hermes, ollama, custom)
            auto_approve_low_risk: Whether to auto-approve low-risk steps
        
        Returns:
            Execution result with status and tracking info
        """
        try:
            # 1. Get task details
            task = await task_service.get_task(task_id)
            if not task:
                return {"status": "error", "error": "Task not found"}
            
            # 2. Initialize agent adapter
            adapter = PersonalAgentAdapter(agent_type)
            
            # 3. Build context from task
            context = {
                "org_id": task.org_id,
                "task_title": task.title,
                "risk_level": task.risk_level,
                "priority": task.priority,
                "stage": task.stage,
                "created_by": task.created_by,
                "deadline": task.deadline.isoformat() if task.deadline else None,
                # Add any files or URLs from task context
                "attachments": task.context.get("attachments", []) if task.context else []
            }
            
            # 4. Submit to agent
            logger.info(f"Submitting task {task_id} to {agent_type}")
            
            result = await adapter.execute_task(
                task_id=task_id,
                instructions=task.description or task.title,
                context=context,
                require_approval=True  # Always require approval for governance
            )
            
            if result["status"] in ["executing", "awaiting_approval"]:
                # Track active execution
                execution_id = result.get("session_id") or result.get("execution_id")
                self._active_executions[task_id] = {
                    "execution_id": execution_id,
                    "agent_type": agent_type,
                    "started_at": datetime.utcnow(),
                    "status": "executing",
                    "auto_approve_low_risk": auto_approve_low_risk
                }
                
                # 5. Start polling for status
                poll_task = asyncio.create_task(
                    self._poll_execution(task_id, execution_id, adapter, auto_approve_low_risk)
                )
                self._polling_tasks[task_id] = poll_task
                
                # 6. Create event
                await event_service.create_event(
                    task_id=task_id,
                    event_type="agent_execution_started",
                    details={
                        "agent_type": agent_type,
                        "execution_id": execution_id,
                        "auto_approve_low_risk": auto_approve_low_risk
                    }
                )
                
                return {
                    "status": "started",
                    "task_id": task_id,
                    "execution_id": execution_id,
                    "agent_type": agent_type,
                    "message": f"Agent {agent_type} is working on this task"
                }
            
            else:
                # Execution failed immediately
                logger.error(f"Agent execution failed for task {task_id}: {result}")
                
                await task_service.update_task(task_id, {
                    "status": "failed",
                    "error": result.get("error", "Unknown agent error")
                })
                
                await event_service.create_event(
                    task_id=task_id,
                    event_type="agent_execution_failed",
                    details={"error": result.get("error")}
                )
                
                return result
                
        except Exception as e:
            logger.exception(f"Error executing task {task_id}")
            return {"status": "error", "error": str(e)}
    
    async def _poll_execution(self, task_id: str, execution_id: str,
                             adapter: PersonalAgentAdapter,
                             auto_approve_low_risk: bool):
        """Poll agent execution status and handle approvals
        
        Runs as background task until execution completes or fails.
        """
        try:
            while True:
                # Check if task still exists
                if task_id not in self._active_executions:
                    logger.info(f"Task {task_id} no longer tracked, stopping poll")
                    break
                
                # Get current status
                status = await adapter.get_status(execution_id)
                
                if status["status"] == "error":
                    logger.error(f"Agent error for task {task_id}: {status.get('error')}")
                    await self._handle_execution_error(task_id, execution_id, status.get("error"))
                    break
                
                if status.get("awaiting_approval") or status.get("status") == "awaiting_approval":
                    # Agent needs human approval
                    logger.info(f"Task {task_id} awaiting approval")
                    
                    # Get pending approvals
                    approvals = await adapter.get_pending_approvals(execution_id)
                    
                    for approval in approvals:
                        # Check if auto-approve eligible
                        if auto_approve_low_risk and approval.get("can_auto_approve"):
                            logger.info(f"Auto-approving low-risk step for task {task_id}")
                            await adapter.approve(
                                execution_id=execution_id,
                                step_id=approval["step_id"],
                                decision="approve",
                                comments="Auto-approved (low risk)"
                            )
                            continue
                        
                        # Create FleetOps approval request
                        fleetops_approval = await approval_service.create_approval(
                            task_id=task_id,
                            stage="agent_execution",
                            approver_role="operator",  # Or based on task risk
                            description=approval.get("description", "Agent step requires approval"),
                            metadata={
                                "agent_type": adapter.agent_type.value,
                                "execution_id": execution_id,
                                "step_id": approval["step_id"],
                                "action_type": approval.get("action_type"),
                                "risk_level": approval.get("risk_level", "medium"),
                                "affected_files": approval.get("affected_files", [])
                            }
                        )
                        
                        # Notify human approvers
                        await notification_service.send_approval_request(
                            task_id=task_id,
                            approval_id=fleetops_approval.id,
                            message=f"Agent {adapter.agent_type.value} needs approval for: {approval.get('description', 'step')}"
                        )
                    
                    # Wait a bit before checking again
                    await asyncio.sleep(5)
                    continue
                
                if status["status"] in ["completed", "success"]:
                    logger.info(f"Task {task_id} completed successfully")
                    await self._handle_execution_complete(task_id, execution_id, status)
                    break
                
                if status["status"] == "failed":
                    logger.error(f"Task {task_id} failed")
                    await self._handle_execution_error(task_id, execution_id, status.get("error", "Unknown"))
                    break
                
                # Still running, wait and check again
                await asyncio.sleep(5)
                
        except asyncio.CancelledError:
            logger.info(f"Polling cancelled for task {task_id}")
        except Exception as e:
            logger.exception(f"Error polling task {task_id}")
            await self._handle_execution_error(task_id, execution_id, str(e))
        finally:
            # Cleanup
            self._active_executions.pop(task_id, None)
            self._polling_tasks.pop(task_id, None)
    
    async def _handle_execution_complete(self, task_id: str, execution_id: str, status: Dict):
        """Handle successful execution completion"""
        try:
            # Update task status
            await task_service.update_task(task_id, {
                "status": "reviewing",  # Ready for human review
                "stage": "review",
                "agent_output": status.get("output"),
                "execution_completed_at": datetime.utcnow().isoformat()
            })
            
            # Create completion event
            await event_service.create_event(
                task_id=task_id,
                event_type="agent_execution_completed",
                details={
                    "execution_id": execution_id,
                    "output_preview": str(status.get("output", ""))[:500]
                }
            )
            
            # Get logs for audit
            adapter = self._get_adapter_for_task(task_id)
            if adapter:
                logs = await adapter.get_logs(execution_id)
                # Store logs with task for audit
                await task_service.update_task(task_id, {
                    "execution_logs": logs
                })
            
            # Notify task creator
            task = await task_service.get_task(task_id)
            await notification_service.send_notification(
                user_id=task.created_by,
                message=f"Agent completed task: {task.title}. Please review the results."
            )
            
        except Exception as e:
            logger.exception(f"Error handling completion for task {task_id}")
    
    async def _handle_execution_error(self, task_id: str, execution_id: str, error: str):
        """Handle execution failure"""
        try:
            await task_service.update_task(task_id, {
                "status": "failed",
                "error": error,
                "failed_at": datetime.utcnow().isoformat()
            })
            
            await event_service.create_event(
                task_id=task_id,
                event_type="agent_execution_failed",
                details={"error": error, "execution_id": execution_id}
            )
            
            # Notify
            task = await task_service.get_task(task_id)
            await notification_service.send_notification(
                user_id=task.created_by,
                message=f"Agent failed on task: {task.title}. Error: {error[:200]}"
            )
            
        except Exception as e:
            logger.exception(f"Error handling failure for task {task_id}")
    
    async def handle_human_approval(self, task_id: str, approval_id: str,
                                  decision: str, comments: Optional[str] = None) -> Dict[str, Any]:
        """Handle human approval decision from FleetOps
        
        Called when a human approves/rejects an agent step in FleetOps UI.
        Forwards the decision to the agent so it can continue or stop.
        """
        try:
            # Get execution info
            exec_info = self._active_executions.get(task_id)
            if not exec_info:
                return {"status": "error", "error": "No active execution found for this task"}
            
            execution_id = exec_info["execution_id"]
            agent_type = exec_info["agent_type"]
            
            # Get adapter
            adapter = PersonalAgentAdapter(agent_type)
            
            # Get approval details to find step_id
            approval = await approval_service.get_approval(approval_id)
            step_id = approval.metadata.get("step_id") if approval and approval.metadata else None
            
            if not step_id:
                return {"status": "error", "error": "No step ID found in approval"}
            
            # Send decision to agent
            logger.info(f"Sending approval decision to agent for task {task_id}: {decision}")
            
            result = await adapter.approve(
                execution_id=execution_id,
                step_id=step_id,
                decision=decision,
                comments=comments
            )
            
            # Update FleetOps approval
            await approval_service.update_approval(
                approval_id=approval_id,
                decision=decision,
                comments=comments
            )
            
            # Create event
            await event_service.create_event(
                task_id=task_id,
                event_type="human_approval_submitted",
                details={
                    "decision": decision,
                    "step_id": step_id,
                    "approval_id": approval_id
                }
            )
            
            return {
                "status": "success",
                "decision": decision,
                "agent_response": result
            }
            
        except Exception as e:
            logger.exception(f"Error handling approval for task {task_id}")
            return {"status": "error", "error": str(e)}
    
    async def cancel_execution(self, task_id: str, reason: str = "") -> Dict[str, Any]:
        """Cancel running agent execution"""
        try:
            exec_info = self._active_executions.get(task_id)
            if not exec_info:
                return {"status": "error", "error": "No active execution found"}
            
            execution_id = exec_info["execution_id"]
            agent_type = exec_info["agent_type"]
            
            adapter = PersonalAgentAdapter(agent_type)
            cancelled = await adapter.cancel(execution_id, reason)
            
            if cancelled:
                # Stop polling
                poll_task = self._polling_tasks.get(task_id)
                if poll_task:
                    poll_task.cancel()
                
                # Cleanup
                self._active_executions.pop(task_id, None)
                self._polling_tasks.pop(task_id, None)
                
                # Update task
                await task_service.update_task(task_id, {
                    "status": "cancelled",
                    "cancelled_at": datetime.utcnow().isoformat(),
                    "cancel_reason": reason
                })
                
                return {"status": "success", "message": "Execution cancelled"}
            else:
                return {"status": "error", "error": "Failed to cancel execution"}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def get_execution_status(self, task_id: str) -> Dict[str, Any]:
        """Get current execution status"""
        exec_info = self._active_executions.get(task_id)
        if not exec_info:
            task = await task_service.get_task(task_id)
            return {
                "status": task.status if task else "unknown",
                "active": False
            }
        
        return {
            "status": exec_info["status"],
            "active": True,
            "agent_type": exec_info["agent_type"],
            "started_at": exec_info["started_at"].isoformat(),
            "execution_id": exec_info["execution_id"]
        }
    
    def _get_adapter_for_task(self, task_id: str) -> Optional[PersonalAgentAdapter]:
        """Get adapter for a tracked task"""
        exec_info = self._active_executions.get(task_id)
        if exec_info:
            return PersonalAgentAdapter(exec_info["agent_type"])
        return None

# Singleton
agent_execution_service = AgentExecutionService()

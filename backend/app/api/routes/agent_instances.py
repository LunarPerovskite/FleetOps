"""Agent Instance Management API

CRUD operations for managing agent instances:
- Create/Update/Delete agent instances
- Activate/Deactivate agents
- Configure permissions and auto-approve settings
- Manage approved/blocked actions
- View execution statistics
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.models import User
from app.services.agent_instance_service import agent_instance_service

router = APIRouter(prefix="/agent-instances", tags=["Agent Instances"])

# ═══════════════════════════════════════
# INSTANCE CRUD
# ═══════════════════════════════════════

@router.post("/")
async def create_instance(
    agent_type: str,
    name: str,
    description: str = "",
    is_remote: bool = False,
    host_url: Optional[str] = None,
    permission_level: str = "approved_actions",
    auto_approve_low_risk: bool = False,
    auto_approve_read_only: bool = True,
    auto_approve_predefined: bool = False,
    max_risk_level: str = "medium",
    approved_actions: List[str] = None,
    blocked_actions: List[str] = None,
    max_execution_time: int = 3600,
    max_steps_per_session: int = 50,
    max_concurrent_tasks: int = 1,
    config: Dict = None,
    credentials: Dict = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new agent instance
    
    Agent types: openclaw, hermes, ollama, custom
    
    Permission levels:
    - read_only: Can only read data
    - low_risk: Auto-approve low risk actions
    - approved_actions: Can do pre-approved actions
    - full_access: Everything needs approval
    - supervised: Human must approve every step
    - autonomous: Can work independently (dangerous!)
    """
    try:
        instance = await agent_instance_service.create_instance(
            db=db,
            org_id=current_user.org_id,
            agent_type=agent_type,
            name=name,
            description=description,
            is_remote=is_remote,
            host_url=host_url,
            permission_level=permission_level,
            auto_approve_low_risk=auto_approve_low_risk,
            auto_approve_read_only=auto_approve_read_only,
            auto_approve_predefined=auto_approve_predefined,
            max_risk_level=max_risk_level,
            approved_actions=approved_actions or [],
            blocked_actions=blocked_actions or [],
            max_execution_time=max_execution_time,
            max_steps_per_session=max_steps_per_session,
            max_concurrent_tasks=max_concurrent_tasks,
            config=config or {},
            credentials=credentials
        )
        
        return {
            "status": "success",
            "message": f"Agent instance '{name}' created",
            "instance": instance.to_dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def list_instances(
    agent_type: Optional[str] = None,
    status: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_remote: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List agent instances with filters"""
    try:
        instances = await agent_instance_service.list_instances(
            db=db,
            org_id=current_user.org_id,
            agent_type=agent_type,
            status=status,
            is_active=is_active,
            is_remote=is_remote
        )
        
        return {
            "instances": [i.to_dict() for i in instances],
            "total": len(instances)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{instance_id}")
async def get_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get agent instance details"""
    try:
        instance = await agent_instance_service.get_instance(
            db, instance_id, current_user.org_id
        )
        
        if not instance:
            raise HTTPException(status_code=404, detail="Agent instance not found")
        
        return {"instance": instance.to_dict()}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{instance_id}")
async def update_instance(
    instance_id: str,
    updates: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update agent instance"""
    try:
        instance = await agent_instance_service.update_instance(
            db, instance_id, current_user.org_id, updates
        )
        
        if not instance:
            raise HTTPException(status_code=404, detail="Agent instance not found")
        
        return {
            "status": "success",
            "message": "Agent instance updated",
            "instance": instance.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{instance_id}")
async def delete_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete agent instance"""
    try:
        deleted = await agent_instance_service.delete_instance(
            db, instance_id, current_user.org_id
        )
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Agent instance not found")
        
        return {
            "status": "success",
            "message": "Agent instance deleted"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════
# ACTIVATION / DEACTIVATION
# ═══════════════════════════════════════

@router.post("/{instance_id}/activate")
async def activate_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Activate an agent instance"""
    try:
        instance = await agent_instance_service.activate_instance(
            db, instance_id, current_user.org_id
        )
        
        if not instance:
            raise HTTPException(status_code=404, detail="Agent instance not found")
        
        return {
            "status": "success",
            "message": f"Agent '{instance.name}' activated",
            "instance": instance.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{instance_id}/deactivate")
async def deactivate_instance(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deactivate an agent instance"""
    try:
        instance = await agent_instance_service.deactivate_instance(
            db, instance_id, current_user.org_id
        )
        
        if not instance:
            raise HTTPException(status_code=404, detail="Agent instance not found")
        
        return {
            "status": "success",
            "message": f"Agent '{instance.name}' deactivated",
            "instance": instance.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════
# PERMISSION MANAGEMENT
# ═══════════════════════════════════════

@router.post("/{instance_id}/permissions")
async def set_permissions(
    instance_id: str,
    permission_level: str,
    auto_approve_low_risk: Optional[bool] = None,
    auto_approve_read_only: Optional[bool] = None,
    auto_approve_predefined: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Set permission level and auto-approve settings
    
    Permission levels:
    - read_only: Can only read data
    - low_risk: Auto-approve low risk actions
    - approved_actions: Can do pre-approved actions
    - full_access: Everything needs approval
    - supervised: Human must approve every step
    - autonomous: Can work independently (dangerous!)
    """
    try:
        auto_approve_settings = {}
        if auto_approve_low_risk is not None:
            auto_approve_settings["auto_approve_low_risk"] = auto_approve_low_risk
        if auto_approve_read_only is not None:
            auto_approve_settings["auto_approve_read_only"] = auto_approve_read_only
        if auto_approve_predefined is not None:
            auto_approve_settings["auto_approve_predefined"] = auto_approve_predefined
        
        instance = await agent_instance_service.set_permission_level(
            db, instance_id, current_user.org_id,
            permission_level, auto_approve_settings
        )
        
        if not instance:
            raise HTTPException(status_code=404, detail="Agent instance not found")
        
        return {
            "status": "success",
            "message": f"Permissions updated for '{instance.name}'",
            "instance": instance.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{instance_id}/permissions")
async def get_permissions(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get current permissions for an agent instance"""
    try:
        instance = await agent_instance_service.get_instance(
            db, instance_id, current_user.org_id
        )
        
        if not instance:
            raise HTTPException(status_code=404, detail="Agent instance not found")
        
        return {
            "instance_id": instance.id,
            "name": instance.name,
            "permission_level": instance.permission_level.value,
            "auto_approve_low_risk": instance.auto_approve_low_risk,
            "auto_approve_read_only": instance.auto_approve_read_only,
            "auto_approve_predefined": instance.auto_approve_predefined,
            "max_risk_level": instance.max_risk_level.value,
            "approved_actions": instance.approved_actions,
            "blocked_actions": instance.blocked_actions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════
# ACTION MANAGEMENT
# ═══════════════════════════════════════

@router.post("/{instance_id}/approved-actions")
async def add_approved_action(
    instance_id: str,
    action: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add an approved action to an agent"""
    try:
        instance = await agent_instance_service.add_approved_action(
            db, instance_id, current_user.org_id, action
        )
        
        if not instance:
            raise HTTPException(status_code=404, detail="Agent instance not found")
        
        return {
            "status": "success",
            "message": f"Action '{action}' added to approved list",
            "approved_actions": instance.approved_actions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{instance_id}/approved-actions/{action}")
async def remove_approved_action(
    instance_id: str,
    action: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove an approved action"""
    try:
        instance = await agent_instance_service.remove_approved_action(
            db, instance_id, current_user.org_id, action
        )
        
        if not instance:
            raise HTTPException(status_code=404, detail="Agent instance not found")
        
        return {
            "status": "success",
            "message": f"Action '{action}' removed from approved list",
            "approved_actions": instance.approved_actions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{instance_id}/blocked-actions")
async def add_blocked_action(
    instance_id: str,
    action: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a blocked action to an agent"""
    try:
        instance = await agent_instance_service.add_blocked_action(
            db, instance_id, current_user.org_id, action
        )
        
        if not instance:
            raise HTTPException(status_code=404, detail="Agent instance not found")
        
        return {
            "status": "success",
            "message": f"Action '{action}' added to blocked list",
            "blocked_actions": instance.blocked_actions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════
# EXECUTION VALIDATION
# ═══════════════════════════════════════

@router.post("/{instance_id}/can-execute")
async def can_execute_action(
    instance_id: str,
    action: str,
    risk_level: str = "medium",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Check if an action can be executed by this agent
    
    Returns whether the action is allowed and if approval is required.
    """
    try:
        result = await agent_instance_service.can_execute_action(
            db, instance_id, current_user.org_id, action, risk_level
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════
# STATISTICS
# ═══════════════════════════════════════

@router.get("/{instance_id}/stats")
async def get_execution_stats(
    instance_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get execution statistics for an agent instance"""
    try:
        stats = await agent_instance_service.get_execution_stats(
            db, instance_id, current_user.org_id
        )
        
        if not stats:
            raise HTTPException(status_code=404, detail="Agent instance not found")
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ═══════════════════════════════════════
# AVAILABLE AGENT TYPES
# ═══════════════════════════════════════

@router.get("/types/available")
async def list_available_agent_types(
    current_user: User = Depends(get_current_user)
):
    """List all available agent types that can be configured"""
    from app.adapters.personal_agent_adapter import AgentType
    
    return {
        "agent_types": [
            {
                "id": "openclaw",
                "name": "OpenClaw",
                "description": "Session-based autonomous agent with step-by-step governance",
                "supports_remote": True,
                "supports_local": True,
                "capabilities": [
                    "session_based_execution",
                    "step_by_step_approval",
                    "file_editing",
                    "command_execution",
                    "git_operations"
                ],
                "config_fields": [
                    {"name": "OPENCLAW_URL", "type": "url", "required": True},
                    {"name": "OPENCLAW_API_KEY", "type": "string", "required": False},
                    {"name": "OPENCLAW_TIMEOUT", "type": "number", "default": 300},
                    {"name": "OPENCLAW_MAX_STEPS", "type": "number", "default": 50}
                ]
            },
            {
                "id": "hermes",
                "name": "Hermes",
                "description": "Task-based personal AI assistant with progress tracking",
                "supports_remote": True,
                "supports_local": True,
                "capabilities": [
                    "task_based_execution",
                    "progress_tracking",
                    "artifact_generation",
                    "workflow_automation"
                ],
                "config_fields": [
                    {"name": "HERMES_URL", "type": "url", "required": True},
                    {"name": "HERMES_API_KEY", "type": "string", "required": False},
                    {"name": "HERMES_TIMEOUT", "type": "number", "default": 300},
                    {"name": "HERMES_PERSONA", "type": "string", "default": "professional"}
                ]
            },
            {
                "id": "ollama",
                "name": "Ollama",
                "description": "Local LLM agent that runs entirely on your machine",
                "supports_remote": False,
                "supports_local": True,
                "capabilities": [
                    "local_llm",
                    "text_generation",
                    "code_generation",
                    "offline_capable"
                ],
                "config_fields": [
                    {"name": "OLLAMA_BASE_URL", "type": "url", "required": True},
                    {"name": "OLLAMA_MODEL", "type": "string", "default": "llama2"}
                ]
            },
            {
                "id": "custom",
                "name": "Custom Agent",
                "description": "Any agent with an HTTP API",
                "supports_remote": True,
                "supports_local": True,
                "capabilities": [
                    "configurable",
                    "api_based",
                    "generic"
                ],
                "config_fields": [
                    {"name": "CUSTOM_AGENT_URL", "type": "url", "required": True},
                    {"name": "CUSTOM_AGENT_API_KEY", "type": "string", "required": False}
                ]
            }
        ]
    }

@router.get("/permissions/levels")
async def list_permission_levels(
    current_user: User = Depends(get_current_user)
):
    """List all available permission levels with descriptions"""
    return {
        "permission_levels": [
            {
                "id": "read_only",
                "name": "Read Only",
                "description": "Agent can only read data. No modifications allowed.",
                "auto_approve": True,
                "risk": "low",
                "use_case": "Monitoring, analysis, reporting"
            },
            {
                "id": "low_risk",
                "name": "Low Risk",
                "description": "Auto-approve low-risk actions. Medium/high need approval.",
                "auto_approve": "configurable",
                "risk": "low",
                "use_case": "Safe automation with oversight"
            },
            {
                "id": "approved_actions",
                "name": "Approved Actions",
                "description": "Can execute pre-approved actions without human review.",
                "auto_approve": "predefined_only",
                "risk": "medium",
                "use_case": "Routine tasks with pre-approved workflow"
            },
            {
                "id": "full_access",
                "name": "Full Access (with Approval)",
                "description": "Can do anything but every action needs human approval.",
                "auto_approve": False,
                "risk": "medium",
                "use_case": "Sensitive operations with full oversight"
            },
            {
                "id": "supervised",
                "name": "Fully Supervised",
                "description": "Human must approve every single step.",
                "auto_approve": False,
                "risk": "high",
                "use_case": "Critical operations, learning phase"
            },
            {
                "id": "autonomous",
                "name": "Autonomous",
                "description": "⚠️ Can work without any human approval. Use with caution!",
                "auto_approve": True,
                "risk": "critical",
                "use_case": "Emergency response, trusted mature agents"
            }
        ],
        "recommendations": {
            "new_agents": "supervised",
            "production": "approved_actions",
            "monitoring": "read_only",
            "emergency": "autonomous"
        }
    }

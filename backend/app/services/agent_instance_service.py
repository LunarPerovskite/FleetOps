"""Agent Instance Management Service

CRUD operations for agent instances with:
- Activation/deactivation
- Permission management
- Auto-approve configuration
- Remote agent support
- Audit logging
"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from sqlalchemy.orm import joinedload

from app.models.agent_models import AgentInstance, AgentExecutionLog, AgentStatus, AgentPermissionLevel, RiskLevel

class AgentInstanceService:
    """Service for managing agent instances"""
    
    async def create_instance(
        self,
        db: AsyncSession,
        org_id: str,
        agent_type: str,
        name: str,
        description: str = "",
        is_remote: bool = False,
        host_url: str = None,
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
    ) -> AgentInstance:
        """Create a new agent instance"""
        
        instance = AgentInstance(
            id=str(uuid.uuid4()),
            org_id=org_id,
            agent_type=agent_type,
            name=name,
            description=description,
            status=AgentStatus.ACTIVE,
            is_active=True,
            is_remote=is_remote,
            host_url=host_url,
            permission_level=AgentPermissionLevel(permission_level),
            auto_approve_low_risk=auto_approve_low_risk,
            auto_approve_read_only=auto_approve_read_only,
            auto_approve_predefined=auto_approve_predefined,
            max_risk_level=RiskLevel(max_risk_level),
            approved_actions=approved_actions or [],
            blocked_actions=blocked_actions or [],
            max_execution_time=max_execution_time,
            max_steps_per_session=max_steps_per_session,
            max_concurrent_tasks=max_concurrent_tasks,
            config=config or {},
            credentials=credentials,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(instance)
        await db.commit()
        await db.refresh(instance)
        
        return instance
    
    async def get_instance(self, db: AsyncSession, instance_id: str, org_id: str) -> Optional[AgentInstance]:
        """Get agent instance by ID"""
        result = await db.execute(
            select(AgentInstance).where(
                and_(AgentInstance.id == instance_id, AgentInstance.org_id == org_id)
            )
        )
        return result.scalar_one_or_none()
    
    async def list_instances(
        self,
        db: AsyncSession,
        org_id: str,
        agent_type: Optional[str] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_remote: Optional[bool] = None
    ) -> List[AgentInstance]:
        """List agent instances with filters"""
        query = select(AgentInstance).where(AgentInstance.org_id == org_id)
        
        if agent_type:
            query = query.where(AgentInstance.agent_type == agent_type)
        if status:
            query = query.where(AgentInstance.status == AgentStatus(status))
        if is_active is not None:
            query = query.where(AgentInstance.is_active == is_active)
        if is_remote is not None:
            query = query.where(AgentInstance.is_remote == is_remote)
        
        query = query.order_by(AgentInstance.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()
    
    async def update_instance(
        self,
        db: AsyncSession,
        instance_id: str,
        org_id: str,
        updates: Dict[str, Any]
    ) -> Optional[AgentInstance]:
        """Update agent instance"""
        
        instance = await self.get_instance(db, instance_id, org_id)
        if not instance:
            return None
        
        # Map update fields
        allowed_fields = [
            "name", "description", "status", "is_active",
            "is_remote", "host_url", "permission_level",
            "auto_approve_low_risk", "auto_approve_read_only",
            "auto_approve_predefined", "max_risk_level",
            "approved_actions", "blocked_actions",
            "max_execution_time", "max_steps_per_session",
            "max_concurrent_tasks", "config", "credentials"
        ]
        
        for field, value in updates.items():
            if field in allowed_fields and hasattr(instance, field):
                # Handle enum conversions
                if field == "status" and value:
                    value = AgentStatus(value)
                elif field == "permission_level" and value:
                    value = AgentPermissionLevel(value)
                elif field == "max_risk_level" and value:
                    value = RiskLevel(value)
                
                setattr(instance, field, value)
        
        instance.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(instance)
        
        return instance
    
    async def activate_instance(self, db: AsyncSession, instance_id: str, org_id: str) -> Optional[AgentInstance]:
        """Activate an agent instance"""
        return await self.update_instance(db, instance_id, org_id, {
            "is_active": True,
            "status": "active"
        })
    
    async def deactivate_instance(self, db: AsyncSession, instance_id: str, org_id: str) -> Optional[AgentInstance]:
        """Deactivate an agent instance"""
        return await self.update_instance(db, instance_id, org_id, {
            "is_active": False,
            "status": "inactive"
        })
    
    async def delete_instance(self, db: AsyncSession, instance_id: str, org_id: str) -> bool:
        """Delete an agent instance"""
        instance = await self.get_instance(db, instance_id, org_id)
        if not instance:
            return False
        
        await db.delete(instance)
        await db.commit()
        return True
    
    async def set_permission_level(
        self,
        db: AsyncSession,
        instance_id: str,
        org_id: str,
        permission_level: str,
        auto_approve_settings: Dict[str, bool] = None
    ) -> Optional[AgentInstance]:
        """Set permission level and auto-approve settings"""
        
        updates = {"permission_level": permission_level}
        
        if auto_approve_settings:
            if "auto_approve_low_risk" in auto_approve_settings:
                updates["auto_approve_low_risk"] = auto_approve_settings["auto_approve_low_risk"]
            if "auto_approve_read_only" in auto_approve_settings:
                updates["auto_approve_read_only"] = auto_approve_settings["auto_approve_read_only"]
            if "auto_approve_predefined" in auto_approve_settings:
                updates["auto_approve_predefined"] = auto_approve_settings["auto_approve_predefined"]
        
        return await self.update_instance(db, instance_id, org_id, updates)
    
    async def add_approved_action(
        self,
        db: AsyncSession,
        instance_id: str,
        org_id: str,
        action: str
    ) -> Optional[AgentInstance]:
        """Add an approved action"""
        instance = await self.get_instance(db, instance_id, org_id)
        if not instance:
            return None
        
        if action not in instance.approved_actions:
            instance.approved_actions.append(action)
            instance.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(instance)
        
        return instance
    
    async def remove_approved_action(
        self,
        db: AsyncSession,
        instance_id: str,
        org_id: str,
        action: str
    ) -> Optional[AgentInstance]:
        """Remove an approved action"""
        instance = await self.get_instance(db, instance_id, org_id)
        if not instance:
            return None
        
        if action in instance.approved_actions:
            instance.approved_actions.remove(action)
            instance.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(instance)
        
        return instance
    
    async def add_blocked_action(
        self,
        db: AsyncSession,
        instance_id: str,
        org_id: str,
        action: str
    ) -> Optional[AgentInstance]:
        """Add a blocked action"""
        instance = await self.get_instance(db, instance_id, org_id)
        if not instance:
            return None
        
        if action not in instance.blocked_actions:
            instance.blocked_actions.append(action)
            instance.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(instance)
        
        return instance
    
    async def can_execute_action(
        self,
        db: AsyncSession,
        instance_id: str,
        org_id: str,
        action: str,
        risk_level: str
    ) -> Dict[str, Any]:
        """Check if an action can be executed by an agent instance
        
        Returns dict with:
        - can_execute: bool
        - requires_approval: bool
        - reason: str
        """
        instance = await self.get_instance(db, instance_id, org_id)
        if not instance:
            return {
                "can_execute": False,
                "requires_approval": False,
                "reason": "Agent instance not found"
            }
        
        # Check if active
        if not instance.is_active:
            return {
                "can_execute": False,
                "requires_approval": False,
                "reason": "Agent instance is inactive"
            }
        
        # Check if action is blocked
        if action in instance.blocked_actions:
            return {
                "can_execute": False,
                "requires_approval": False,
                "reason": f"Action '{action}' is blocked for this agent"
            }
        
        # Check risk level
        risk_levels = ["low", "medium", "high", "critical"]
        instance_max = risk_levels.index(instance.max_risk_level.value)
        action_risk = risk_levels.index(risk_level)
        
        if action_risk > instance_max:
            return {
                "can_execute": False,
                "requires_approval": False,
                "reason": f"Risk level '{risk_level}' exceeds agent's maximum '{instance.max_risk_level.value}'"
            }
        
        # Determine if approval required based on permission level
        requires_approval = True
        auto_approve = False
        
        if instance.permission_level == AgentPermissionLevel.READ_ONLY:
            requires_approval = True
            # Only read actions
            read_actions = ["read_file", "view_file", "list_dir", "search", "analyze"]
            if action not in read_actions:
                return {
                    "can_execute": False,
                    "requires_approval": False,
                    "reason": f"Action '{action}' is not a read-only action"
                }
        
        elif instance.permission_level == AgentPermissionLevel.AUTONOMOUS:
            requires_approval = False
            auto_approve = True
        
        elif instance.permission_level == AgentPermissionLevel.SUPERVISED:
            requires_approval = True
        
        elif instance.permission_level == AgentPermissionLevel.LOW_RISK:
            if risk_level == "low" and instance.auto_approve_low_risk:
                requires_approval = False
                auto_approve = True
        
        elif instance.permission_level == AgentPermissionLevel.APPROVED_ACTIONS:
            if action in instance.approved_actions and instance.auto_approve_predefined:
                requires_approval = False
                auto_approve = True
        
        elif instance.permission_level == AgentPermissionLevel.FULL_ACCESS:
            # Everything needs approval
            requires_approval = True
        
        # Check auto-approve read-only
        if instance.auto_approve_read_only:
            read_actions = ["read_file", "view_file", "list_dir", "search", "analyze", "get_status"]
            if action in read_actions and risk_level == "low":
                requires_approval = False
                auto_approve = True
        
        return {
            "can_execute": True,
            "requires_approval": requires_approval,
            "auto_approve": auto_approve,
            "reason": "Auto-approved" if auto_approve else "Requires human approval"
        }
    
    async def get_execution_stats(
        self,
        db: AsyncSession,
        instance_id: str,
        org_id: str
    ) -> Dict[str, Any]:
        """Get execution statistics for an agent instance"""
        instance = await self.get_instance(db, instance_id, org_id)
        if not instance:
            return None
        
        # Get recent executions
        from sqlalchemy import select
        result = await db.execute(
            select(AgentExecutionLog).where(
                and_(
                    AgentExecutionLog.agent_instance_id == instance_id,
                    AgentExecutionLog.org_id == org_id
                )
            ).order_by(AgentExecutionLog.started_at.desc()).limit(10)
        )
        recent_executions = result.scalars().all()
        
        return {
            "instance": instance.to_dict(),
            "total_executions": instance.total_executions,
            "successful": instance.successful_executions,
            "failed": instance.failed_executions,
            "success_rate": (
                instance.successful_executions / instance.total_executions * 100
                if instance.total_executions > 0 else 0
            ),
            "recent_executions": [e.to_dict() for e in recent_executions]
        }

# Singleton
agent_instance_service = AgentInstanceService()

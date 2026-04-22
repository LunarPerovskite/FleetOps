"""Hierarchy Management Service for FleetOps

Features:
- Create unlimited hierarchy levels
- Custom approval ladders per org
- Role templates
- Audit logging
"""

from datetime import datetime
from typing import Optional, Dict, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from app.models.hierarchy_models import (
    HierarchyScale, HierarchyLevel, RoleTemplate,
    UserHierarchyAssignment, AgentHierarchyAssignment,
    ApprovalLadder, HierarchyChangeLog
)

class HierarchyService:
    """Manage customizable hierarchies"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_scale(self, org_id: str, name: str, 
                          scale_type: str, description: str = None,
                          created_by: str = None) -> Dict:
        """Create a new hierarchy scale"""
        scale = HierarchyScale(
            org_id=org_id,
            name=name,
            description=description,
            scale_type=scale_type,
            created_by=created_by
        )
        self.db.add(scale)
        await self.db.commit()
        
        # Log change
        await self._log_change(org_id, created_by, "created", "scale", scale.id)
        
        return {
            "scale_id": scale.id,
            "name": name,
            "type": scale_type,
            "status": "created"
        }
    
    async def add_level(self, scale_id: str, name: str, 
                       level_order: int, permissions: List[str] = None,
                       color: str = None, icon: str = None,
                       auto_approve_threshold: str = None,
                       sla_multiplier: float = 1.0) -> Dict:
        """Add a level to a hierarchy"""
        level = HierarchyLevel(
            scale_id=scale_id,
            name=name,
            level_order=level_order,
            permissions=permissions or [],
            color=color or "#6B7280",
            icon=icon,
            auto_approve_threshold=auto_approve_threshold,
            sla_multiplier=sla_multiplier
        )
        self.db.add(level)
        await self.db.commit()
        
        return {
            "level_id": level.id,
            "name": name,
            "order": level_order,
            "status": "created"
        }
    
    async def get_scale_levels(self, scale_id: str) -> List[Dict]:
        """Get all levels in a scale, ordered by level_order"""
        result = await self.db.execute(
            select(HierarchyLevel)
            .where(HierarchyLevel.scale_id == scale_id)
            .where(HierarchyLevel.is_active == True)
            .order_by(HierarchyLevel.level_order.desc())
        )
        levels = result.scalars().all()
        
        return [
            {
                "id": level.id,
                "name": level.name,
                "display_name": level.display_name,
                "order": level.level_order,
                "color": level.color,
                "icon": level.icon,
                "permissions": level.permissions,
                "sla_multiplier": level.sla_multiplier,
                "auto_approve_threshold": level.auto_approve_threshold
            }
            for level in levels
        ]
    
    async def assign_user_level(self, user_id: str, scale_id: str, 
                              level_id: str, org_id: str,
                              assigned_by: str = None,
                              valid_until: datetime = None) -> Dict:
        """Assign a user to a hierarchy level"""
        # Deactivate old primary assignment
        await self.db.execute(
            select(UserHierarchyAssignment)
            .where(
                and_(
                    UserHierarchyAssignment.user_id == user_id,
                    UserHierarchyAssignment.scale_id == scale_id,
                    UserHierarchyAssignment.is_primary == True
                )
            )
        )
        
        assignment = UserHierarchyAssignment(
            user_id=user_id,
            scale_id=scale_id,
            level_id=level_id,
            org_id=org_id,
            assigned_by=assigned_by,
            valid_until=valid_until,
            is_primary=True
        )
        self.db.add(assignment)
        await self.db.commit()
        
        await self._log_change(org_id, assigned_by, "assigned", "user", user_id)
        
        return {
            "assignment_id": assignment.id,
            "user_id": user_id,
            "level_id": level_id,
            "status": "assigned"
        }
    
    async def create_approval_ladder(self, org_id: str, scale_id: str,
                                     name: str, risk_level: str,
                                     min_approver_level: int,
                                     required_approvers: int = 1,
                                     auto_approve: bool = False,
                                     escalation_minutes: int = 60) -> Dict:
        """Create a custom approval ladder"""
        ladder = ApprovalLadder(
            org_id=org_id,
            scale_id=scale_id,
            name=name,
            risk_level=risk_level,
            min_approver_level=min_approver_level,
            required_approvers=required_approvers,
            auto_approve=auto_approve,
            escalation_minutes=escalation_minutes
        )
        self.db.add(ladder)
        await self.db.commit()
        
        return {
            "ladder_id": ladder.id,
            "name": name,
            "risk_level": risk_level,
            "min_level": min_approver_level,
            "status": "created"
        }
    
    async def get_approval_ladder(self, org_id: str, 
                                   risk_level: str, scale_id: str = None) -> Optional[Dict]:
        """Get approval ladder for a risk level"""
        query = select(ApprovalLadder).where(
            and_(
                ApprovalLadder.org_id == org_id,
                ApprovalLadder.risk_level == risk_level,
                ApprovalLadder.is_active == True
            )
        )
        
        if scale_id:
            query = query.where(ApprovalLadder.scale_id == scale_id)
        
        result = await self.db.execute(query)
        ladder = result.scalar_one_or_none()
        
        if not ladder:
            return None
        
        return {
            "ladder_id": ladder.id,
            "name": ladder.name,
            "risk_level": ladder.risk_level,
            "min_approver_level": ladder.min_approver_level,
            "required_approvers": ladder.required_approvers,
            "auto_approve": ladder.auto_approve,
            "escalation_minutes": ladder.escalation_minutes,
            "requires_second_pair": ladder.requires_second_pair
        }
    
    async def create_role_template(self, name: str, scale_type: str,
                                   description: str = None,
                                   permissions: List[str] = None,
                                   icon: str = None,
                                   category: str = None) -> Dict:
        """Create a reusable role template"""
        template = RoleTemplate(
            name=name,
            description=description,
            scale_type=scale_type,
            default_permissions=permissions or [],
            icon=icon,
            category=category
        )
        self.db.add(template)
        await self.db.commit()
        
        return {
            "template_id": template.id,
            "name": name,
            "type": scale_type,
            "status": "created"
        }
    
    async def get_role_templates(self, scale_type: str = None,
                                 category: str = None) -> List[Dict]:
        """Get role templates, optionally filtered"""
        query = select(RoleTemplate)
        
        if scale_type:
            query = query.where(RoleTemplate.scale_type == scale_type)
        if category:
            query = query.where(RoleTemplate.category == category)
        
        result = await self.db.execute(query)
        templates = result.scalars().all()
        
        return [
            {
                "id": t.id,
                "name": t.name,
                "description": t.description,
                "type": t.scale_type,
                "permissions": t.default_permissions,
                "icon": t.icon,
                "category": t.category,
                "usage_count": t.usage_count
            }
            for t in templates
        ]
    
    async def get_user_effective_level(self, user_id: str, 
                                      scale_id: str) -> Optional[Dict]:
        """Get user's current level in a scale"""
        result = await self.db.execute(
            select(UserHierarchyAssignment, HierarchyLevel)
            .join(HierarchyLevel, UserHierarchyAssignment.level_id == HierarchyLevel.id)
            .where(
                and_(
                    UserHierarchyAssignment.user_id == user_id,
                    UserHierarchyAssignment.scale_id == scale_id,
                    UserHierarchyAssignment.is_primary == True,
                    or_(
                        UserHierarchyAssignment.valid_until.is_(None),
                        UserHierarchyAssignment.valid_until >= datetime.utcnow()
                    )
                )
            )
        )
        
        assignment = result.first()
        if not assignment:
            return None
        
        _, level = assignment
        return {
            "level_id": level.id,
            "name": level.name,
            "display_name": level.display_name,
            "order": level.level_order,
            "permissions": level.permissions,
            "sla_multiplier": level.sla_multiplier,
            "auto_approve_threshold": level.auto_approve_threshold
        }
    
    async def _log_change(self, org_id: str, user_id: str, 
                         action: str, entity_type: str, 
                         entity_id: str) -> None:
        """Log hierarchy changes"""
        log = HierarchyChangeLog(
            org_id=org_id,
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id
        )
        self.db.add(log)
        await self.db.commit()

"""Hierarchy API Routes

Manage custom hierarchies, levels, and approval ladders
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict

from app.core.database import get_db
from app.core.auth import get_current_user
from app.services.hierarchy_service import HierarchyService
from app.models.models import User

router = APIRouter()

@router.post("/scales")
async def create_scale(
    name: str,
    scale_type: str,
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new hierarchy scale"""
    service = HierarchyService(db)
    result = await service.create_scale(
        org_id=current_user.org_id,
        name=name,
        scale_type=scale_type,
        description=description,
        created_by=current_user.id
    )
    return result

@router.get("/scales/{scale_id}/levels")
async def get_scale_levels(
    scale_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all levels in a scale"""
    service = HierarchyService(db)
    levels = await service.get_scale_levels(scale_id)
    return {"scale_id": scale_id, "levels": levels}

@router.post("/scales/{scale_id}/levels")
async def add_level(
    scale_id: str,
    name: str,
    level_order: int,
    permissions: Optional[List[str]] = None,
    color: Optional[str] = None,
    icon: Optional[str] = None,
    auto_approve_threshold: Optional[str] = None,
    sla_multiplier: Optional[float] = 1.0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a level to a hierarchy"""
    service = HierarchyService(db)
    result = await service.add_level(
        scale_id=scale_id,
        name=name,
        level_order=level_order,
        permissions=permissions,
        color=color,
        icon=icon,
        auto_approve_threshold=auto_approve_threshold,
        sla_multiplier=sla_multiplier
    )
    return result

@router.post("/assignments/users")
async def assign_user_level(
    user_id: str,
    scale_id: str,
    level_id: str,
    valid_until: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign user to hierarchy level"""
    from datetime import datetime
    service = HierarchyService(db)
    
    valid_until_dt = None
    if valid_until:
        valid_until_dt = datetime.fromisoformat(valid_until)
    
    result = await service.assign_user_level(
        user_id=user_id,
        scale_id=scale_id,
        level_id=level_id,
        org_id=current_user.org_id,
        assigned_by=current_user.id,
        valid_until=valid_until_dt
    )
    return result

@router.post("/approval-ladders")
async def create_approval_ladder(
    name: str,
    risk_level: str,
    min_approver_level: int,
    required_approvers: Optional[int] = 1,
    auto_approve: Optional[bool] = False,
    escalation_minutes: Optional[int] = 60,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create custom approval ladder"""
    service = HierarchyService(db)
    result = await service.create_approval_ladder(
        org_id=current_user.org_id,
        scale_id=None,  # Will be determined from context
        name=name,
        risk_level=risk_level,
        min_approver_level=min_approver_level,
        required_approvers=required_approvers,
        auto_approve=auto_approve,
        escalation_minutes=escalation_minutes
    )
    return result

@router.get("/approval-ladders/{risk_level}")
async def get_approval_ladder(
    risk_level: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get approval ladder for risk level"""
    service = HierarchyService(db)
    result = await service.get_approval_ladder(
        org_id=current_user.org_id,
        risk_level=risk_level
    )
    return result

@router.get("/role-templates")
async def get_role_templates(
    scale_type: Optional[str] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get role templates"""
    service = HierarchyService(db)
    templates = await service.get_role_templates(
        scale_type=scale_type,
        category=category
    )
    return {"templates": templates}

@router.post("/role-templates")
async def create_role_template(
    name: str,
    scale_type: str,
    description: Optional[str] = None,
    permissions: Optional[List[str]] = None,
    icon: Optional[str] = None,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create role template"""
    service = HierarchyService(db)
    result = await service.create_role_template(
        name=name,
        scale_type=scale_type,
        description=description,
        permissions=permissions,
        icon=icon,
        category=category
    )
    return result

@router.get("/users/{user_id}/effective-level/{scale_id}")
async def get_user_effective_level(
    user_id: str,
    scale_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's effective level in scale"""
    service = HierarchyService(db)
    result = await service.get_user_effective_level(user_id, scale_id)
    return result

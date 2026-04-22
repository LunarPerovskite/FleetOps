"""Customizable Hierarchy Models for FleetOps

Admins can create unlimited hierarchy levels,
custom roles, and flexible approval ladders.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Text, Boolean, Float, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.models.models import Base

class HierarchyScale(Base):
    """A customizable hierarchy scale (e.g., corporate, flat, military)"""
    __tablename__ = "hierarchy_scales"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"))
    name = Column(String(255), nullable=False)  # "Corporate", "Flat", "Military"
    description = Column(Text)
    scale_type = Column(String(50), nullable=False)  # "human", "agent", "mixed"
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    levels = relationship("HierarchyLevel", back_populates="scale", cascade="all, delete-orphan")
    organization = relationship("Organization", backref="hierarchy_scales")

class HierarchyLevel(Base):
    """A single level within a hierarchy scale"""
    __tablename__ = "hierarchy_levels"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    scale_id = Column(String(36), ForeignKey("hierarchy_scales.id"))
    name = Column(String(255), nullable=False)  # "CEO", "Manager", "Director"
    display_name = Column(String(255))  # Localized display name
    level_order = Column(Integer, nullable=False)  # 1, 2, 3 (higher = more authority)
    color = Column(String(7), default="#6B7280")  # UI color
    icon = Column(String(50))  # Lucide icon name
    permissions = Column(JSON, default=list)  # ["approve_critical", "manage_agents", "view_all"]
    sla_multiplier = Column(Float, default=1.0)  # 0.5 = faster SLA
    auto_approve_threshold = Column(String(20))  # "low", "medium", "none"
    can_escalate_to = Column(JSON, default=list)  # Level IDs this can escalate to
    requires_approval_from = Column(JSON, default=list)  # Level IDs required for approval
    metadata = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    scale = relationship("HierarchyScale", back_populates="levels")

class RoleTemplate(Base):
    """Reusable role templates across organizations"""
    __tablename__ = "role_templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text)
    scale_type = Column(String(50), nullable=False)  # "human", "agent"
    default_permissions = Column(JSON, default=list)
    default_sla_minutes = Column(Integer, default=60)
    icon = Column(String(50))
    category = Column(String(50))  # "leadership", "operations", "support", "technical"
    is_system = Column(Boolean, default=False)  # Built-in templates can't be deleted
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserHierarchyAssignment(Base):
    """Links a user to their hierarchy level"""
    __tablename__ = "user_hierarchy_assignments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"))
    scale_id = Column(String(36), ForeignKey("hierarchy_scales.id"))
    level_id = Column(String(36), ForeignKey("hierarchy_levels.id"))
    org_id = Column(String(36), ForeignKey("organizations.id"))
    assigned_by = Column(String(36), ForeignKey("users.id"))
    assigned_at = Column(DateTime, default=datetime.utcnow)
    valid_until = Column(DateTime)  # For temporary promotions
    is_primary = Column(Boolean, default=True)  # Primary role vs secondary
    metadata = Column(JSON, default=dict)

class AgentHierarchyAssignment(Base):
    """Links an agent to their hierarchy level"""
    __tablename__ = "agent_hierarchy_assignments"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id = Column(String(36), ForeignKey("agents.id"))
    scale_id = Column(String(36), ForeignKey("hierarchy_scales.id"))
    level_id = Column(String(36), ForeignKey("hierarchy_levels.id"))
    org_id = Column(String(36), ForeignKey("organizations.id"))
    assigned_by = Column(String(36), ForeignKey("users.id"))
    assigned_at = Column(DateTime, default=datetime.utcnow)
    is_primary = Column(Boolean, default=True)
    capabilities_override = Column(JSON, default=dict)  # Level-specific capabilities
    metadata = Column(JSON, default=dict)

class ApprovalLadder(Base):
    """Custom approval rules per org/scale"""
    __tablename__ = "approval_ladders"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"))
    scale_id = Column(String(36), ForeignKey("hierarchy_scales.id"))
    name = Column(String(255), nullable=False)
    risk_level = Column(String(20), nullable=False)  # low, medium, high, critical
    min_approver_level = Column(Integer)  # Minimum hierarchy level required
    required_approvers = Column(Integer, default=1)  # How many approvals needed
    auto_approve = Column(Boolean, default=False)
    auto_approve_conditions = Column(JSON, default=dict)  # {"cost_threshold": 10}
    escalation_minutes = Column(Integer, default=60)
    notify_levels = Column(JSON, default=list)  # Which levels to notify
    requires_second_pair = Column(Boolean, default=False)  # Four-eyes principle
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class HierarchyChangeLog(Base):
    """Audit log for hierarchy changes"""
    __tablename__ = "hierarchy_change_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id = Column(String(36), ForeignKey("organizations.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    action = Column(String(50), nullable=False)  # created, updated, deleted, assigned
    entity_type = Column(String(50), nullable=False)  # scale, level, assignment
    entity_id = Column(String(36))
    old_values = Column(JSON)
    new_values = Column(JSON)
    reason = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

"""Agent Instance Management for FleetOps

Database models and service for managing agent instances:
- Activation/deactivation
- Auto-approve settings per agent
- Permission levels per agent
- Remote vs local agent tracking
- Instance-specific configuration
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from typing import Optional, Dict, Any, List

from app.models.models import Base

class AgentStatus(str, enum.Enum):
    """Agent instance status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CONNECTING = "connecting"
    MAINTENANCE = "maintenance"

class AgentPermissionLevel(str, enum.Enum):
    """Permission levels for agents"""
    READ_ONLY = "read_only"           # Can only read data
    LOW_RISK = "low_risk"             # Auto-approve low risk
    APPROVED_ACTIONS = "approved_actions"  # Can do pre-approved actions
    FULL_ACCESS = "full_access"       # Everything needs approval
    SUPERVISED = "supervised"         # Human must approve every step
    AUTONOMOUS = "autonomous"         # Can work independently (dangerous!)

class RiskLevel(str, enum.Enum):
    """Risk levels for agent actions"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AgentInstance(Base):
    """Agent instance configuration
    
    Each agent instance can be:
    - Local (running on same machine)
    - Remote (running on different machine)
    - Managed (third-party service)
    """
    __tablename__ = "agent_instances"
    
    id = Column(String(36), primary_key=True)
    org_id = Column(String(36), ForeignKey("organizations.id"), nullable=False)
    
    # Agent identification
    agent_type = Column(String(50), nullable=False)  # openclaw, hermes, ollama, custom
    name = Column(String(100), nullable=False)  # Display name
    description = Column(Text, nullable=True)
    
    # Status
    status = Column(SQLEnum(AgentStatus), default=AgentStatus.ACTIVE)
    is_active = Column(Boolean, default=True)
    
    # Location
    is_remote = Column(Boolean, default=False)  # Remote vs local
    host_url = Column(String(500), nullable=True)  # URL if remote
    
    # Permissions
    permission_level = Column(
        SQLEnum(AgentPermissionLevel), 
        default=AgentPermissionLevel.APPROVED_ACTIONS
    )
    
    # Auto-approve settings
    auto_approve_low_risk = Column(Boolean, default=False)
    auto_approve_read_only = Column(Boolean, default=True)
    auto_approve_predefined = Column(Boolean, default=False)
    
    # Risk assessment
    max_risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.MEDIUM)
    
    # Pre-approved actions (JSON list)
    approved_actions = Column(JSON, default=list)  # ["read_file", "list_dir"]
    blocked_actions = Column(JSON, default=list)    # ["delete_database", "drop_table"]
    
    # Execution limits
    max_execution_time = Column(Integer, default=3600)  # seconds
    max_steps_per_session = Column(Integer, default=50)
    max_concurrent_tasks = Column(Integer, default=1)
    
    # Configuration
    config = Column(JSON, default=dict)  # Agent-specific config
    credentials = Column(JSON, nullable=True)  # Encrypted credentials
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    
    # Relationships
    organization = relationship("Organization", back_populates="agent_instances")
    executions = relationship("AgentExecutionLog", back_populates="agent_instance")
    
    def to_dict(self, include_sensitive=False):
        """Serialize to dict"""
        data = {
            "id": self.id,
            "agent_type": self.agent_type,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "is_active": self.is_active,
            "is_remote": self.is_remote,
            "host_url": self.host_url,
            "permission_level": self.permission_level.value,
            "auto_approve_low_risk": self.auto_approve_low_risk,
            "auto_approve_read_only": self.auto_approve_read_only,
            "auto_approve_predefined": self.auto_approve_predefined,
            "max_risk_level": self.max_risk_level.value,
            "approved_actions": self.approved_actions,
            "blocked_actions": self.blocked_actions,
            "max_execution_time": self.max_execution_time,
            "max_steps_per_session": self.max_steps_per_session,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
        }
        
        if include_sensitive:
            data["config"] = self.config
        
        return data


class AgentExecutionLog(Base):
    """Log of agent executions"""
    __tablename__ = "agent_execution_logs"
    
    id = Column(String(36), primary_key=True)
    agent_instance_id = Column(String(36), ForeignKey("agent_instances.id"))
    task_id = Column(String(36), ForeignKey("tasks.id"))
    org_id = Column(String(36), ForeignKey("organizations.id"))
    
    # Execution details
    execution_id = Column(String(100), nullable=True)  # Agent's execution ID
    status = Column(String(50), nullable=False)  # running, completed, failed, cancelled
    
    # Approval tracking
    total_steps = Column(Integer, default=0)
    approved_steps = Column(Integer, default=0)
    rejected_steps = Column(Integer, default=0)
    auto_approved_steps = Column(Integer, default=0)
    
    # Risk tracking
    max_risk_encountered = Column(SQLEnum(RiskLevel), nullable=True)
    
    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Results
    output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    artifacts = Column(JSON, default=list)
    
    # Full log
    execution_log = Column(JSON, default=list)
    
    # Relationships
    agent_instance = relationship("AgentInstance", back_populates="executions")
    
    def to_dict(self):
        return {
            "id": self.id,
            "agent_instance_id": self.agent_instance_id,
            "task_id": self.task_id,
            "execution_id": self.execution_id,
            "status": self.status,
            "total_steps": self.total_steps,
            "approved_steps": self.approved_steps,
            "rejected_steps": self.rejected_steps,
            "auto_approved_steps": self.auto_approved_steps,
            "max_risk_encountered": self.max_risk_encountered.value if self.max_risk_encountered else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "output": self.output,
            "error": self.error,
            "artifacts": self.artifacts,
        }


# Update Organization model to include relationship
# This would go in models.py but adding here for reference
# organization.agent_instances = relationship("AgentInstance", back_populates="organization")

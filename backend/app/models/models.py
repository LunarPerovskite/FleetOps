from sqlalchemy import create_engine, Column, String, DateTime, Integer, ForeignKey, Text, Enum, Boolean, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum

Base = declarative_base()

class TaskStatus(enum.Enum):
    CREATED = "created"
    PLANNING = "planning"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    APPROVAL_PENDING = "approval_pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RiskLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    BLOCKED = "blocked"

class HumanRole(enum.Enum):
    EXECUTIVE = "executive"
    DIRECTOR = "director"
    SENIOR_OPERATOR = "senior_operator"
    OPERATOR = "operator"
    REVIEWER = "reviewer"
    VIEWER = "viewer"

class AgentLevel(enum.Enum):
    LEAD = "lead"
    SENIOR = "senior"
    JUNIOR = "junior"
    SPECIALIST = "specialist"
    MONITOR = "monitor"

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    teams = relationship("Team", back_populates="organization")
    agents = relationship("Agent", back_populates="organization")
    users = relationship("User", back_populates="organization")

class Team(Base):
    __tablename__ = "teams"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    org_id = Column(String(36), ForeignKey("organizations.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="teams")
    members = relationship("User", back_populates="team")
    agents = relationship("Agent", back_populates="team")

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    password_hash = Column(String(255))
    role = Column(Enum(HumanRole), default=HumanRole.OPERATOR)
    org_id = Column(String(36), ForeignKey("organizations.id"))
    team_id = Column(String(36), ForeignKey("teams.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="users")
    team = relationship("Team", back_populates="members")
    approvals = relationship("Approval", back_populates="human")

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    provider = Column(String(100))  # anthropic, openai, ollama, etc.
    model = Column(String(100))
    level = Column(Enum(AgentLevel), default=AgentLevel.JUNIOR)
    capabilities = Column(JSON, default=list)
    org_id = Column(String(36), ForeignKey("organizations.id"))
    team_id = Column(String(36), ForeignKey("teams.id"))
    parent_agent_id = Column(String(36), ForeignKey("agents.id"), nullable=True)
    status = Column(String(50), default="active")
    cost_to_date = Column(Float, default=0.0)
    max_sub_agents = Column(Integer, nullable=True)  # null = unlimited sub-agents, any number = limit
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="agents")
    team = relationship("Team", back_populates="agents")
    tasks = relationship("Task", back_populates="agent")
    sub_agents = relationship("Agent", backref="parent", remote_side=[id])
    prompts = relationship("PromptVersion", back_populates="agent")
    llm_usage = relationship("LLMUsage", back_populates="agent")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String(36), primary_key=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    status = Column(Enum(TaskStatus), default=TaskStatus.CREATED)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW)
    stage = Column(String(50), default="initiation")
    agent_id = Column(String(36), ForeignKey("agents.id"))
    org_id = Column(String(36), ForeignKey("organizations.id"))
    created_by = Column(String(36), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    agent = relationship("Agent", back_populates="tasks")
    events = relationship("Event", back_populates="task")
    approvals = relationship("Approval", back_populates="task")

class Event(Base):
    __tablename__ = "events"
    
    id = Column(String(64), primary_key=True)  # sha256 hash
    task_id = Column(String(36), ForeignKey("tasks.id"))
    event_type = Column(String(100), nullable=False)
    agent_id = Column(String(36), ForeignKey("agents.id"))
    user_id = Column(String(36), ForeignKey("users.id"))
    data = Column(JSON)
    signature = Column(String(128))
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    task = relationship("Task", back_populates="events")

class Approval(Base):
    __tablename__ = "approvals"
    
    id = Column(String(36), primary_key=True)
    task_id = Column(String(36), ForeignKey("tasks.id"))
    human_id = Column(String(36), ForeignKey("users.id"))
    stage = Column(String(50), nullable=False)
    decision = Column(String(20))  # approve, reject, request_changes, escalate
    comments = Column(Text)
    sla_deadline = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    
    task = relationship("Task", back_populates="approvals")
    human = relationship("User", back_populates="approvals")

class PromptVersion(Base):
    __tablename__ = "prompt_versions"
    
    id = Column(String(36), primary_key=True)
    agent_id = Column(String(36), ForeignKey("agents.id"))
    task_id = Column(String(36), ForeignKey("tasks.id"))
    version = Column(String(20))
    system_prompt = Column(Text)
    user_prompt = Column(Text)
    rendered_prompt = Column(Text)
    model_used = Column(String(100))
    output = Column(Text)
    response_time_ms = Column(Integer)
    tokens_in = Column(Integer)
    tokens_out = Column(Integer)
    tokens_cached = Column(Integer)
    cost_usd = Column(Float)
    context_window_pct = Column(Float)
    review_status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    agent = relationship("Agent", back_populates="prompts")

class LLMUsage(Base):
    __tablename__ = "llm_usage"
    
    id = Column(String(36), primary_key=True)
    provider = Column(String(50))
    model = Column(String(100))
    task_id = Column(String(36), ForeignKey("tasks.id"))
    agent_id = Column(String(36), ForeignKey("agents.id"))
    org_id = Column(String(36), ForeignKey("organizations.id"))
    tokens_in = Column(Integer)
    tokens_out = Column(Integer)
    tokens_cached = Column(Integer)
    cost = Column(Float)
    latency_ms = Column(Integer)
    temperature = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    agent = relationship("Agent", back_populates="llm_usage")

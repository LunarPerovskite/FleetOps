"""Alembic migration script

Initial migration to create all tables
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import enum

# revision identifiers
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None

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

def upgrade():
    # Organizations
    op.create_table(
        'organizations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('tier', sa.String(20), default='free'),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Teams
    op.create_table(
        'teams',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('org_id', sa.String(36), sa.ForeignKey('organizations.id')),
        sa.Column('created_at', sa.DateTime, default=sa.func.now())
    )
    
    # Users
    op.create_table(
        'users',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('name', sa.String(255)),
        sa.Column('password_hash', sa.String(255)),
        sa.Column('role', sa.Enum(HumanRole), default=HumanRole.OPERATOR),
        sa.Column('org_id', sa.String(36), sa.ForeignKey('organizations.id')),
        sa.Column('team_id', sa.String(36), sa.ForeignKey('teams.id')),
        sa.Column('created_at', sa.DateTime, default=sa.func.now())
    )
    
    # Agents
    op.create_table(
        'agents',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('provider', sa.String(100)),
        sa.Column('model', sa.String(100)),
        sa.Column('level', sa.Enum(AgentLevel), default=AgentLevel.JUNIOR),
        sa.Column('capabilities', postgresql.JSONB, default=list),
        sa.Column('org_id', sa.String(36), sa.ForeignKey('organizations.id')),
        sa.Column('team_id', sa.String(36), sa.ForeignKey('teams.id')),
        sa.Column('parent_agent_id', sa.String(36), sa.ForeignKey('agents.id'), nullable=True),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('cost_to_date', sa.Float, default=0.0),
        sa.Column('max_sub_agents', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime, default=sa.func.now())
    )
    
    # Tasks
    op.create_table(
        'tasks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('status', sa.Enum(TaskStatus), default=TaskStatus.CREATED),
        sa.Column('risk_level', sa.Enum(RiskLevel), default=RiskLevel.LOW),
        sa.Column('stage', sa.String(50), default='initiation'),
        sa.Column('agent_id', sa.String(36), sa.ForeignKey('agents.id')),
        sa.Column('org_id', sa.String(36), sa.ForeignKey('organizations.id')),
        sa.Column('created_by', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime)
    )
    
    # Events
    op.create_table(
        'events',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('task_id', sa.String(36), sa.ForeignKey('tasks.id')),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('agent_id', sa.String(36), sa.ForeignKey('agents.id')),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('data', postgresql.JSONB),
        sa.Column('signature', sa.String(128)),
        sa.Column('timestamp', sa.DateTime, default=sa.func.now())
    )
    
    # Approvals
    op.create_table(
        'approvals',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('task_id', sa.String(36), sa.ForeignKey('tasks.id')),
        sa.Column('human_id', sa.String(36), sa.ForeignKey('users.id')),
        sa.Column('stage', sa.String(50), nullable=False),
        sa.Column('decision', sa.String(20)),
        sa.Column('comments', sa.Text),
        sa.Column('sla_deadline', sa.DateTime),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime)
    )
    
    # LLM Usage
    op.create_table(
        'llm_usage',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('provider', sa.String(50)),
        sa.Column('model', sa.String(100)),
        sa.Column('task_id', sa.String(36), sa.ForeignKey('tasks.id')),
        sa.Column('agent_id', sa.String(36), sa.ForeignKey('agents.id')),
        sa.Column('org_id', sa.String(36), sa.ForeignKey('organizations.id')),
        sa.Column('tokens_in', sa.Integer),
        sa.Column('tokens_out', sa.Integer),
        sa.Column('tokens_cached', sa.Integer),
        sa.Column('cost', sa.Float),
        sa.Column('latency_ms', sa.Integer),
        sa.Column('timestamp', sa.DateTime, default=sa.func.now())
    )
    
    # Indexes
    op.create_index('idx_tasks_org_id', 'tasks', ['org_id'])
    op.create_index('idx_tasks_status', 'tasks', ['status'])
    op.create_index('idx_tasks_agent_id', 'tasks', ['agent_id'])
    op.create_index('idx_events_task_id', 'events', ['task_id'])
    op.create_index('idx_events_timestamp', 'events', ['timestamp'])
    op.create_index('idx_approvals_task_id', 'approvals', ['task_id'])
    op.create_index('idx_llm_usage_org_id', 'llm_usage', ['org_id'])
    op.create_index('idx_agents_org_id', 'agents', ['org_id'])

def downgrade():
    op.drop_index('idx_agents_org_id')
    op.drop_index('idx_llm_usage_org_id')
    op.drop_index('idx_approvals_task_id')
    op.drop_index('idx_events_timestamp')
    op.drop_index('idx_events_task_id')
    op.drop_index('idx_tasks_agent_id')
    op.drop_index('idx_tasks_status')
    op.drop_index('idx_tasks_org_id')
    
    op.drop_table('llm_usage')
    op.drop_table('approvals')
    op.drop_table('events')
    op.drop_table('tasks')
    op.drop_table('agents')
    op.drop_table('users')
    op.drop_table('teams')
    op.drop_table('organizations')

"""Add agent instance management tables

Revision ID: 003
Revises: 002
Create Date: 2026-04-22 12:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Create agent_instances table
    op.create_table(
        'agent_instances',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('org_id', sa.String(36), sa.ForeignKey('organizations.id'), nullable=False),
        sa.Column('agent_type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_remote', sa.Boolean(), default=False),
        sa.Column('host_url', sa.String(500), nullable=True),
        sa.Column('permission_level', sa.String(30), default='approved_actions'),
        sa.Column('auto_approve_low_risk', sa.Boolean(), default=False),
        sa.Column('auto_approve_read_only', sa.Boolean(), default=True),
        sa.Column('auto_approve_predefined', sa.Boolean(), default=False),
        sa.Column('max_risk_level', sa.String(20), default='medium'),
        sa.Column('approved_actions', postgresql.JSON(astext_type=sa.Text()), default=list),
        sa.Column('blocked_actions', postgresql.JSON(astext_type=sa.Text()), default=list),
        sa.Column('max_execution_time', sa.Integer(), default=3600),
        sa.Column('max_steps_per_session', sa.Integer(), default=50),
        sa.Column('max_concurrent_tasks', sa.Integer(), default=1),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), default=dict),
        sa.Column('credentials', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('total_executions', sa.Integer(), default=0),
        sa.Column('successful_executions', sa.Integer(), default=0),
        sa.Column('failed_executions', sa.Integer(), default=0),
    )
    
    # Create indexes
    op.create_index('idx_agent_instances_org', 'agent_instances', ['org_id'])
    op.create_index('idx_agent_instances_type', 'agent_instances', ['agent_type'])
    op.create_index('idx_agent_instances_status', 'agent_instances', ['status'])
    op.create_index('idx_agent_instances_active', 'agent_instances', ['is_active'])
    
    # Create agent_execution_logs table
    op.create_table(
        'agent_execution_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('agent_instance_id', sa.String(36), sa.ForeignKey('agent_instances.id')),
        sa.Column('task_id', sa.String(36), sa.ForeignKey('tasks.id')),
        sa.Column('org_id', sa.String(36), sa.ForeignKey('organizations.id')),
        sa.Column('execution_id', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('total_steps', sa.Integer(), default=0),
        sa.Column('approved_steps', sa.Integer(), default=0),
        sa.Column('rejected_steps', sa.Integer(), default=0),
        sa.Column('auto_approved_steps', sa.Integer(), default=0),
        sa.Column('max_risk_encountered', sa.String(20), nullable=True),
        sa.Column('started_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('output', sa.Text(), nullable=True),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('artifacts', postgresql.JSON(astext_type=sa.Text()), default=list),
        sa.Column('execution_log', postgresql.JSON(astext_type=sa.Text()), default=list),
    )
    
    # Create indexes
    op.create_index('idx_exec_logs_instance', 'agent_execution_logs', ['agent_instance_id'])
    op.create_index('idx_exec_logs_task', 'agent_execution_logs', ['task_id'])
    op.create_index('idx_exec_logs_org', 'agent_execution_logs', ['org_id'])
    op.create_index('idx_exec_logs_status', 'agent_execution_logs', ['status'])


def downgrade():
    # Drop tables (reverse order)
    op.drop_index('idx_exec_logs_status', table_name='agent_execution_logs')
    op.drop_index('idx_exec_logs_org', table_name='agent_execution_logs')
    op.drop_index('idx_exec_logs_task', table_name='agent_execution_logs')
    op.drop_index('idx_exec_logs_instance', table_name='agent_execution_logs')
    op.drop_table('agent_execution_logs')
    
    op.drop_index('idx_agent_instances_active', table_name='agent_instances')
    op.drop_index('idx_agent_instances_status', table_name='agent_instances')
    op.drop_index('idx_agent_instances_type', table_name='agent_instances')
    op.drop_index('idx_agent_instances_org', table_name='agent_instances')
    op.drop_table('agent_instances')

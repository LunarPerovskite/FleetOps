"""Add database indexes for performance

Revision ID: 002
Revises: 001
Create Date: 2026-04-22
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None

def upgrade():
    # Tasks indexes
    op.create_index('idx_tasks_org_id', 'tasks', ['org_id'])
    op.create_index('idx_tasks_status', 'tasks', ['status'])
    op.create_index('idx_tasks_agent_id', 'tasks', ['agent_id'])
    op.create_index('idx_tasks_created_at', 'tasks', ['created_at'])
    
    # Agents indexes
    op.create_index('idx_agents_org_id', 'agents', ['org_id'])
    op.create_index('idx_agents_status', 'agents', ['status'])
    
    # Events indexes
    op.create_index('idx_events_task_id', 'events', ['task_id'])
    op.create_index('idx_events_timestamp', 'events', ['timestamp'])
    op.create_index('idx_events_org_id', 'events', ['org_id'])
    
    # Approvals indexes
    op.create_index('idx_approvals_task_id', 'approvals', ['task_id'])
    op.create_index('idx_approvals_decision', 'approvals', ['decision'])
    
    # Users indexes
    op.create_index('idx_users_org_id', 'users', ['org_id'])
    op.create_index('idx_users_email', 'users', ['email'], unique=True)
    
    # Organizations indexes
    op.create_index('idx_organizations_tier', 'organizations', ['tier'])


def downgrade():
    # Drop all indexes
    indexes = [
        ('tasks', 'idx_tasks_org_id'),
        ('tasks', 'idx_tasks_status'),
        ('tasks', 'idx_tasks_agent_id'),
        ('tasks', 'idx_tasks_created_at'),
        ('agents', 'idx_agents_org_id'),
        ('agents', 'idx_agents_status'),
        ('events', 'idx_events_task_id'),
        ('events', 'idx_events_timestamp'),
        ('events', 'idx_events_org_id'),
        ('approvals', 'idx_approvals_task_id'),
        ('approvals', 'idx_approvals_decision'),
        ('users', 'idx_users_org_id'),
        ('users', 'idx_users_email'),
        ('organizations', 'idx_organizations_tier'),
    ]
    
    for table, index in indexes:
        op.drop_index(index, table_name=table)

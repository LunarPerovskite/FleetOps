"""Add audit_logs, cost_records, pricing_configs tables

Revision ID: 004
Revises: 003
Create Date: 2026-04-24 15:30:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─── audit_logs ─────────────────────────────────────────────────────
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('table_name', sa.String(100), nullable=False),
        sa.Column('record_id', sa.String(36), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('old_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_values', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('changed_by', sa.String(36), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('org_id', sa.String(36), sa.ForeignKey('organizations.id'), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
    )
    op.create_index('ix_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('ix_audit_logs_table_record', 'audit_logs', ['table_name', 'record_id'])
    op.create_index('ix_audit_logs_org', 'audit_logs', ['org_id'])
    
    # ─── cost_records ───────────────────────────────────────────────────
    op.create_table(
        'cost_records',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('task_id', sa.String(36), sa.ForeignKey('tasks.id'), nullable=True),
        sa.Column('agent_id', sa.String(36), sa.ForeignKey('agents.id'), nullable=True),
        sa.Column('org_id', sa.String(36), sa.ForeignKey('organizations.id'), nullable=True),
        sa.Column('provider', sa.String(50), nullable=True),
        sa.Column('model', sa.String(100), nullable=True),
        sa.Column('tokens_in', sa.Integer(), default=0),
        sa.Column('tokens_out', sa.Integer(), default=0),
        sa.Column('tokens_cached', sa.Integer(), default=0),
        sa.Column('cost_usd', sa.Float(), default=0.0),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), default=dict),
    )
    op.create_index('ix_cost_records_timestamp', 'cost_records', ['timestamp'])
    op.create_index('ix_cost_records_task', 'cost_records', ['task_id'])
    op.create_index('ix_cost_records_agent', 'cost_records', ['agent_id'])
    op.create_index('ix_cost_records_org', 'cost_records', ['org_id'])
    
    # ─── pricing_configs ───────────────────────────────────────────────
    op.create_table(
        'pricing_configs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('service', sa.String(100), nullable=False),
        sa.Column('model', sa.String(100), nullable=False),
        sa.Column('model_name', sa.String(255), nullable=True),
        sa.Column('pricing_type', sa.String(50), default='pay_per_token'),
        sa.Column('input_rate_per_1m', sa.Float(), nullable=True),
        sa.Column('output_rate_per_1m', sa.Float(), nullable=True),
        sa.Column('cached_rate_per_1m', sa.Float(), nullable=True),
        sa.Column('monthly_cost', sa.Float(), nullable=True),
        sa.Column('annual_cost', sa.Float(), nullable=True),
        sa.Column('included_tokens', sa.Integer(), default=0),
        sa.Column('kwh_per_hour', sa.Float(), nullable=True),
        sa.Column('electricity_rate', sa.Float(), default=0.15),
        sa.Column('provider_url', sa.String(500), nullable=True),
        sa.Column('last_fetched', sa.DateTime(), nullable=True),
        sa.Column('is_user_configured', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    op.create_index('ix_pricing_configs_service_model', 'pricing_configs', ['service', 'model'], unique=True)
    op.create_index('ix_pricing_configs_active', 'pricing_configs', ['is_active'])


def downgrade() -> None:
    op.drop_table('pricing_configs')
    op.drop_table('cost_records')
    op.drop_table('audit_logs')

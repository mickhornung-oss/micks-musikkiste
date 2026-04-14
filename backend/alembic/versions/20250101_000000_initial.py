"""Initial migration for Micks Musikkiste

Revision ID: 001
Revises: 
Create Date: 2025-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('progress', sa.Integer(), default=0),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('result_file', sa.String(500), nullable=True),
        sa.Column('metadata', postgresql.JSON(), default=dict),
        sa.Column('preset_used', sa.String(100), nullable=True),
        sa.Column('engine', sa.String(50), nullable=False, default='mock'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('genre', sa.String(50), nullable=False),
        sa.Column('mood', sa.String(50), nullable=False),
        sa.Column('duration', sa.Integer(), nullable=False),
        sa.Column('output_file', sa.String(500), nullable=True),
        sa.Column('preset_used', sa.String(100), nullable=True),
        sa.Column('lyrics', sa.Text(), nullable=True),
        sa.Column('negative_prompts', postgresql.JSON(), default=list),
        sa.Column('parameters', postgresql.JSON(), default=dict),
        sa.Column('metadata', postgresql.JSON(), default=dict),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('exports', postgresql.JSON(), default=list),
        sa.Column('last_export_at', sa.DateTime(), nullable=True),
        sa.Column('last_job_id', sa.String(36), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create foreign key constraint
    op.create_foreign_key(
        'fk_projects_last_job',
        'projects', 'jobs',
        ['last_job_id'], ['id'],
    )

    # Create indexes
    op.create_index('ix_jobs_status', 'jobs', ['status'])
    op.create_index('ix_jobs_created_at', 'jobs', ['created_at'])
    op.create_index('ix_projects_type', 'projects', ['type'])
    op.create_index('ix_projects_genre', 'projects', ['genre'])
    op.create_index('ix_projects_created_at', 'projects', ['created_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_jobs_status', table_name='jobs')
    op.drop_index('ix_jobs_created_at', table_name='jobs')
    op.drop_index('ix_projects_type', table_name='projects')
    op.drop_index('ix_projects_genre', table_name='projects')
    op.drop_index('ix_projects_created_at', table_name='projects')

    # Drop foreign key constraint
    op.drop_constraint('fk_projects_last_job', 'projects', type_='foreignkey')

    # Drop tables
    op.drop_table('projects')
    op.drop_table('jobs')

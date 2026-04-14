"""Add queue fields to jobs table

Revision ID: 002
Revises: 001
Create Date: 2026-04-02 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add queue-specific columns to jobs table
    op.add_column('jobs', sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('jobs', sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='3'))
    op.add_column('jobs', sa.Column('scheduled_at', sa.DateTime(), nullable=True))
    op.add_column('jobs', sa.Column('claimed_at', sa.DateTime(), nullable=True))
    op.add_column('jobs', sa.Column('heartbeat_at', sa.DateTime(), nullable=True))
    op.add_column('jobs', sa.Column('worker_id', sa.String(100), nullable=True))
    op.add_column('jobs', sa.Column('last_error', sa.Text(), nullable=True))
    op.add_column('jobs', sa.Column('finished_at', sa.DateTime(), nullable=True))

    # Create indexes for efficient queue operations
    op.create_index('ix_jobs_status_scheduled', 'jobs', ['status', 'scheduled_at'])
    op.create_index('ix_jobs_worker_claimed', 'jobs', ['worker_id', 'claimed_at'])
    op.create_index('ix_jobs_claimed_heartbeat', 'jobs', ['status', 'heartbeat_at'])

    # Migrate existing RUNNING jobs to CLAIMED for recovery
    op.execute("""
        UPDATE jobs 
        SET status = 'claimed', 
            claimed_at = updated_at,
            attempt_count = 1,
            max_attempts = 3
        WHERE status = 'running'
    """)

    # Migrate existing COMPLETED jobs to have finished_at
    op.execute("""
        UPDATE jobs 
        SET finished_at = updated_at
        WHERE status = 'completed' AND finished_at IS NULL
    """)

    # Migrate existing FAILED jobs to have finished_at
    op.execute("""
        UPDATE jobs 
        SET finished_at = updated_at,
            last_error = COALESCE(error, 'Unknown error')
        WHERE status = 'failed' AND finished_at IS NULL
    """)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_jobs_claimed_heartbeat', table_name='jobs')
    op.drop_index('ix_jobs_worker_claimed', table_name='jobs')
    op.drop_index('ix_jobs_status_scheduled', table_name='jobs')

    # Drop columns
    op.drop_column('jobs', 'finished_at')
    op.drop_column('jobs', 'last_error')
    op.drop_column('jobs', 'worker_id')
    op.drop_column('jobs', 'heartbeat_at')
    op.drop_column('jobs', 'claimed_at')
    op.drop_column('jobs', 'scheduled_at')
    op.drop_column('jobs', 'max_attempts')
    op.drop_column('jobs', 'attempt_count')

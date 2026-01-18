"""Add CASCADE DELETE to assignment_history display_id foreign key

Revision ID: 14a2f7cdc2e5
Revises: f70598d0f069
Create Date: 2026-01-18 14:27:38.009448

This migration adds ON DELETE CASCADE to the assignment_history.display_id
foreign key constraint. When a display is deleted, all associated assignment
history records will be automatically deleted.

For SQLite, this requires recreating the table with the new constraint since
SQLite does not support ALTER TABLE for foreign key modifications.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '14a2f7cdc2e5'
down_revision = 'f70598d0f069'
branch_labels = None
depends_on = None


def upgrade():
    # SQLite does not support modifying foreign key constraints directly.
    # We need to recreate the table with the new constraint.
    #
    # 1. Create new table with CASCADE DELETE on display_id
    # 2. Copy data from old table
    # 3. Drop old table
    # 4. Rename new table

    # Create new table with the CASCADE constraint
    op.create_table(
        'assignment_history_new',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('display_id', sa.Integer(), nullable=False),
        sa.Column('previous_slideshow_id', sa.Integer(), nullable=True),
        sa.Column('new_slideshow_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(
            ['display_id'], ['displays.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(['new_slideshow_id'], ['slideshows.id']),
        sa.ForeignKeyConstraint(['previous_slideshow_id'], ['slideshows.id']),
    )

    # Copy data from old table to new table
    op.execute(
        'INSERT INTO assignment_history_new '
        'SELECT * FROM assignment_history'
    )

    # Drop old table
    op.drop_table('assignment_history')

    # Rename new table to original name
    op.rename_table('assignment_history_new', 'assignment_history')


def downgrade():
    # Revert to the original foreign key without CASCADE DELETE
    op.create_table(
        'assignment_history_new',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('display_id', sa.Integer(), nullable=False),
        sa.Column('previous_slideshow_id', sa.Integer(), nullable=True),
        sa.Column('new_slideshow_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('created_by_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['display_id'], ['displays.id']),
        sa.ForeignKeyConstraint(['new_slideshow_id'], ['slideshows.id']),
        sa.ForeignKeyConstraint(['previous_slideshow_id'], ['slideshows.id']),
    )

    op.execute(
        'INSERT INTO assignment_history_new '
        'SELECT * FROM assignment_history'
    )

    op.drop_table('assignment_history')
    op.rename_table('assignment_history_new', 'assignment_history')

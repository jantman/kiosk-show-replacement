"""Add show_info_overlay column to displays table

Revision ID: 8a3b5c7d9e1f
Revises: 14a2f7cdc2e5
Create Date: 2026-01-21 06:00:00.000000

This migration adds the show_info_overlay boolean column to the displays table.
This field controls whether the info overlay (showing display name, slideshow name,
and current slide) is visible on the display view page.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8a3b5c7d9e1f'
down_revision = '14a2f7cdc2e5'
branch_labels = None
depends_on = None


def upgrade():
    # Add show_info_overlay column with default False
    with op.batch_alter_table('displays', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('show_info_overlay', sa.Boolean(), nullable=False, server_default=sa.false())
        )


def downgrade():
    # Remove show_info_overlay column
    with op.batch_alter_table('displays', schema=None) as batch_op:
        batch_op.drop_column('show_info_overlay')

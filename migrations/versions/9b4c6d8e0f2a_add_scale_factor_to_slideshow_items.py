"""Add scale_factor column to slideshow_items table

Revision ID: 9b4c6d8e0f2a
Revises: 8a3b5c7d9e1f
Create Date: 2026-01-25 12:00:00.000000

This migration adds the scale_factor column to the slideshow_items table.
This field allows URL-type slides to be zoomed out to show more content.
Value is a percentage (10-100), where NULL or 100 means no scaling (normal).
Lower values zoom out to show more of the webpage content.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b4c6d8e0f2a'
down_revision = '8a3b5c7d9e1f'
branch_labels = None
depends_on = None


def upgrade():
    # Add scale_factor column (nullable integer, NULL = no scaling)
    with op.batch_alter_table('slideshow_items', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('scale_factor', sa.Integer(), nullable=True)
        )


def downgrade():
    # Remove scale_factor column
    with op.batch_alter_table('slideshow_items', schema=None) as batch_op:
        batch_op.drop_column('scale_factor')

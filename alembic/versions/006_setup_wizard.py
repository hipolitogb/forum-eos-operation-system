"""setup_completed flag for onboarding wizard

Revision ID: 006
Revises: 005
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "forum_settings",
        sa.Column("setup_completed", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade():
    op.drop_column("forum_settings", "setup_completed")

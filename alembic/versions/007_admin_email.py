"""add email to admin_users for password recovery

Revision ID: 007
Revises: 006
Create Date: 2026-04-16
"""
from alembic import op
import sqlalchemy as sa

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("admin_users", sa.Column("email", sa.String(200), nullable=True))


def downgrade():
    op.drop_column("admin_users", "email")

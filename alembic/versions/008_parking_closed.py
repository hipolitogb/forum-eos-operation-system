"""add closed flag to parking_items

Revision ID: 008
Revises: 007
Create Date: 2026-06-11
"""
from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("parking_items", sa.Column("closed", sa.Integer(), nullable=False, server_default="0"))


def downgrade():
    op.drop_column("parking_items", "closed")

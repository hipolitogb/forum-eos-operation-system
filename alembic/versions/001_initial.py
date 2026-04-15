"""initial tables

Revision ID: 001
Revises:
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "members",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("role", sa.String(100), nullable=False, server_default=""),
        sa.Column("display_order", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    op.create_table(
        "parking_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("person_name", sa.String(200), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("tag", sa.String(100), nullable=False, server_default="open"),
        sa.Column("deep_dive_date", sa.String(50), nullable=False, server_default=""),
        sa.Column("context", sa.Text(), nullable=False, server_default=""),
        sa.Column("display_order", sa.Integer(), server_default="0"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table("parking_items")
    op.drop_table("members")

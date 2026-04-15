"""forum_settings singleton

Revision ID: 002
Revises: 001
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "forum_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("forum_name", sa.String(100), nullable=False, server_default="FORUM OS"),
        sa.Column("tagline", sa.String(200), nullable=False, server_default="Operations Dashboard"),
        sa.Column("display_font", sa.String(100), nullable=False, server_default="Alfa Slab One"),
        sa.Column("body_font", sa.String(100), nullable=False, server_default="Manrope"),
        sa.Column("color_primary", sa.String(7), nullable=False, server_default="#F59E0B"),
        sa.Column("color_secondary", sa.String(7), nullable=False, server_default="#EF4444"),
        sa.Column("color_tertiary", sa.String(7), nullable=False, server_default="#3B82F6"),
        sa.Column("logo_path", sa.String(300), nullable=False, server_default=""),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )
    # Seed the singleton row.
    op.execute("INSERT INTO forum_settings (id) VALUES (1)")


def downgrade():
    op.drop_table("forum_settings")

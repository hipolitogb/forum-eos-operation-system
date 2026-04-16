"""admin_users table + default admin/admin credentials

Revision ID: 004
Revises: 003
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa
import bcrypt

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(200), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # Seed the default admin/admin. Moderators are expected to change this
    # immediately from the admin UI.
    pw_hash = bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode("utf-8")
    op.get_bind().execute(
        sa.text("INSERT INTO admin_users (id, username, password_hash) VALUES (1, :u, :p)"),
        {"u": "admin", "p": pw_hash},
    )


def downgrade():
    op.drop_table("admin_users")

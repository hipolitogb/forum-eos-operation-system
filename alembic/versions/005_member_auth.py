"""member magic-link auth + email settings

Revision ID: 005
Revises: 004
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade():
    # Members gain an email column. Nullable so existing rows stay valid;
    # moderator fills them in before turning auth on.
    op.add_column("members", sa.Column("email", sa.String(200), nullable=True))
    op.create_unique_constraint("uq_members_email", "members", ["email"])

    # Auth + email config on the singleton settings row.
    op.add_column("forum_settings", sa.Column("auth_enabled", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("forum_settings", sa.Column("email_api_key", sa.String(500), nullable=False, server_default=""))
    op.add_column("forum_settings", sa.Column("email_from_address", sa.String(200), nullable=False, server_default="onboarding@resend.dev"))
    op.add_column("forum_settings", sa.Column("email_from_name", sa.String(100), nullable=False, server_default=""))
    op.add_column("forum_settings", sa.Column("session_secret", sa.String(100), nullable=False, server_default=""))

    # Magic-link tokens. We store a sha256 hash, never the plain token.
    op.create_table(
        "login_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(200), nullable=False),
        sa.Column("token_hash", sa.String(100), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("requester_ip", sa.String(50), nullable=False, server_default=""),
    )
    op.create_index("ix_login_tokens_token_hash", "login_tokens", ["token_hash"])
    op.create_index("ix_login_tokens_email", "login_tokens", ["email"])


def downgrade():
    op.drop_index("ix_login_tokens_email", table_name="login_tokens")
    op.drop_index("ix_login_tokens_token_hash", table_name="login_tokens")
    op.drop_table("login_tokens")
    op.drop_column("forum_settings", "session_secret")
    op.drop_column("forum_settings", "email_from_name")
    op.drop_column("forum_settings", "email_from_address")
    op.drop_column("forum_settings", "email_api_key")
    op.drop_column("forum_settings", "auth_enabled")
    op.drop_constraint("uq_members_email", "members", type_="unique")
    op.drop_column("members", "email")

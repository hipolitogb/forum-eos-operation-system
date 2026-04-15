"""editable agenda, constitution and reflections

Revision ID: 003
Revises: 002
Create Date: 2026-04-15
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "forum_settings",
        sa.Column(
            "reflections_intro",
            sa.Text(),
            nullable=False,
            server_default=(
                "Each member rates four life areas from 1 to 10, then shares what's behind the number. "
                "The goal is to reach the uncomfortable 5%."
            ),
        ),
    )
    op.add_column(
        "forum_settings",
        sa.Column(
            "reflections_footer",
            sa.Text(),
            nullable=False,
            server_default="Timing: 5 minutes per person. The moderator starts.",
        ),
    )

    op.create_table(
        "agenda_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("time", sa.String(20), nullable=False, server_default=""),
        sa.Column("title", sa.String(200), nullable=False, server_default=""),
        sa.Column("duration", sa.String(50), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "constitution_pillars",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, server_default=""),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "constitution_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("topic", sa.String(100), nullable=False, server_default=""),
        sa.Column("rule", sa.Text(), nullable=False, server_default=""),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "reflection_areas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("icon", sa.String(20), nullable=False, server_default=""),
        sa.Column("label", sa.String(100), nullable=False, server_default=""),
        sa.Column("color_class", sa.String(50), nullable=False, server_default="text-brand-primary"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
    )

    # Seed defaults.
    agenda = [
        ("0:00", "Arrival + coffee", "15 min", ""),
        ("0:15", "Administrative items", "15 min", "Next meeting date, logistics, forum rules."),
        ("0:30", "5% Reflections", "45 min", "5 min per person. The moderator starts."),
        ("1:15", "Break", "10 min", ""),
        ("1:25", "Communication Starter", "25 min", "One question, everyone answers (~3 min each)."),
        ("1:50", "Parking Lot — Review", "20 min", "Each owner speaks for 2 min: still relevant? anything changed?"),
        ("2:10", "Break", "10 min", ""),
        ("2:20", "Deep Dive or Topical", "60 min", "Presentation → questions → experiences → reflection."),
        ("3:20", "Break", "10 min", ""),
        ("3:30", "Second block", "40 min", "Lifeline from 1-2 members, or group brainstorm."),
        ("4:10", "Close + commitments", "20 min", "One word about how you're leaving. Next date."),
        ("4:30", "Formal close", "", "Eat / hang out together."),
    ]
    conn = op.get_bind()
    for i, (t, ti, d, de) in enumerate(agenda, start=1):
        conn.execute(
            sa.text("INSERT INTO agenda_items (time, title, duration, description, display_order) VALUES (:t,:ti,:d,:de,:o)"),
            {"t": t, "ti": ti, "d": d, "de": de, "o": i},
        )

    pillars = [
        ("Vulnerability", "Be open and honest, especially about what's hard"),
        ("Confidentiality", "What's said in the Forum stays in the Forum. Period."),
        ("Gestalt", "Speak from your own experience, don't give advice"),
        ("Personal responsibility", "Each member owns their Forum experience"),
    ]
    for i, (n, de) in enumerate(pillars, start=1):
        conn.execute(
            sa.text("INSERT INTO constitution_pillars (name, description, display_order) VALUES (:n,:d,:o)"),
            {"n": n, "d": de, "o": i},
        )

    rules = [
        ("Confidentiality", "Breach = immediate expulsion. Readmission by unanimous vote."),
        ("Meetings", "11 meetings + 1 retreat per fiscal year."),
        ("Attendance", "Missing 2 or the retreat = out. Readmission by unanimous vote."),
        ("Punctuality", "Arriving late = half absence."),
        ("Forum Mindset", "Listen with curiosity. Speak from your own experience."),
        ("Phones", "None during meetings and retreat, except during breaks."),
        ("Alcohol", "None during sessions. At retreats, only during designated moments."),
        ("Business", "No material transactions between members."),
        ("Relationships", "Not between members. If one develops, one leaves."),
        ("Size", "8 to 10 members."),
        ("Departure", "An exit Deep Dive is expected."),
        ("Upskilling", "One training per year."),
    ]
    for i, (t, r) in enumerate(rules, start=1):
        conn.execute(
            sa.text("INSERT INTO constitution_rules (topic, rule, display_order) VALUES (:t,:r,:o)"),
            {"t": t, "r": r, "o": i},
        )

    areas = [
        ("👨‍👩‍👧", "Family / Friends", "text-pink-400"),
        ("🫀", "Health", "text-emerald-400"),
        ("🏗️", "Work", "text-blue-400"),
        ("💰", "Finance", "text-brand-primary"),
    ]
    for i, (ic, la, co) in enumerate(areas, start=1):
        conn.execute(
            sa.text("INSERT INTO reflection_areas (icon, label, color_class, display_order) VALUES (:i,:l,:c,:o)"),
            {"i": ic, "l": la, "c": co, "o": i},
        )


def downgrade():
    op.drop_table("reflection_areas")
    op.drop_table("constitution_rules")
    op.drop_table("constitution_pillars")
    op.drop_table("agenda_items")
    op.drop_column("forum_settings", "reflections_footer")
    op.drop_column("forum_settings", "reflections_intro")

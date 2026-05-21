"""init assessment tables

Revision ID: 0001
Revises:
Create Date: 2026-05-21 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "tests",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("module_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "pass_score",
            sa.Integer(),
            server_default="70",
            nullable=False,
        ),
        sa.Column("author_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("manager_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default="true",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "pass_score BETWEEN 0 AND 100",
            name="tests_pass_score_check",
        ),
    )
    op.create_index("idx_tests_module", "tests", ["module_id"])
    op.create_index("idx_tests_author", "tests", ["author_id"])
    op.create_index("idx_tests_manager", "tests", ["manager_id"])
    op.create_index("idx_tests_active", "tests", ["is_active"])

    op.create_table(
        "questions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "test_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "order_index",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "qtype",
            sa.String(length=20),
            server_default="single",
            nullable=False,
        ),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["test_id"], ["tests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("test_id", "order_index"),
        sa.CheckConstraint(
            "qtype IN ('single', 'multiple')",
            name="questions_qtype_check",
        ),
    )
    op.create_index("idx_questions_test", "questions", ["test_id"])

    op.create_table(
        "attempts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "test_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("manager_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("is_passed", sa.Boolean(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "finished_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["test_id"], ["tests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_attempts_test", "attempts", ["test_id"])
    op.create_index("idx_attempts_user", "attempts", ["user_id"])
    op.create_index("idx_attempts_manager", "attempts", ["manager_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_attempts_manager", table_name="attempts")
    op.drop_index("idx_attempts_user", table_name="attempts")
    op.drop_index("idx_attempts_test", table_name="attempts")
    op.drop_table("attempts")
    op.drop_index("idx_questions_test", table_name="questions")
    op.drop_table("questions")
    op.drop_index("idx_tests_active", table_name="tests")
    op.drop_index("idx_tests_manager", table_name="tests")
    op.drop_index("idx_tests_author", table_name="tests")
    op.drop_index("idx_tests_module", table_name="tests")
    op.drop_table("tests")

"""add module_assignments

Revision ID: 849f836ca67a
Revises: b9304461aab6
Create Date: 2026-05-31 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "849f836ca67a"
down_revision: str | None = "b9304461aab6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "module_assignments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "module_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "assigned_by", postgresql.UUID(as_uuid=True), nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["module_id"], ["modules.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("module_id", "user_id"),
    )
    op.create_index("idx_module_assignments_module", "module_assignments", ["module_id"])
    op.create_index("idx_module_assignments_user", "module_assignments", ["user_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("idx_module_assignments_user", table_name="module_assignments")
    op.drop_index("idx_module_assignments_module", table_name="module_assignments")
    op.drop_table("module_assignments")

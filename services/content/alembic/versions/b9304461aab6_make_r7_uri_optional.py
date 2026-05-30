"""make_r7_uri_optional

Revision ID: b9304461aab6
Revises: 1a7372850762
Create Date: 2026-05-30 22:54:14.948135

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b9304461aab6"
down_revision: str | Sequence[str] | None = "1a7372850762"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Make lessons.r7_uri nullable."""
    op.alter_column(
        "lessons",
        "r7_uri",
        existing_type=sa.TEXT(),
        nullable=True,
    )


def downgrade() -> None:
    """Revert lessons.r7_uri to non-nullable."""
    op.alter_column(
        "lessons",
        "r7_uri",
        existing_type=sa.TEXT(),
        nullable=False,
    )

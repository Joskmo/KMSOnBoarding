"""add pending_content to heuristics

Revision ID: 1a7372850762
Revises: 880eca4e904c
Create Date: 2026-05-21 09:43:48.729542

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a7372850762'
down_revision: Union[str, Sequence[str], None] = '880eca4e904c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('heuristics', sa.Column('pending_content', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('heuristics', 'pending_content')

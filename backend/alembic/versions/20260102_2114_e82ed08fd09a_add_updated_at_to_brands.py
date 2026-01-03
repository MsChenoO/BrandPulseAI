"""Add updated_at to brands

Revision ID: e82ed08fd09a
Revises: aba048a4661d
Create Date: 2026-01-02 21:14:04.555844

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e82ed08fd09a'
down_revision: Union[str, None] = 'aba048a4661d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add updated_at column, defaulting to created_at for existing rows
    op.add_column('brands', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.execute('UPDATE brands SET updated_at = created_at WHERE updated_at IS NULL')
    op.alter_column('brands', 'updated_at', nullable=False)


def downgrade() -> None:
    op.drop_column('brands', 'updated_at')

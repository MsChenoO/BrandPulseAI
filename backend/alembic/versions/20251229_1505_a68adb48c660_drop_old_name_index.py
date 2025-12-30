"""drop_old_name_index

Revision ID: a68adb48c660
Revises: e05187a4d632
Create Date: 2025-12-29 15:05:41.225494

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a68adb48c660'
down_revision: Union[str, None] = 'e05187a4d632'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Drop the old unique index on brand name that prevents users from having
    brands with the same name.
    """
    # Drop the old unique index on name column
    op.drop_index('ix_brands_name', table_name='brands')

    # Re-create it as a non-unique index (for query performance)
    op.create_index('ix_brands_name', 'brands', ['name'], unique=False)


def downgrade() -> None:
    """
    Restore the unique index on brand name.
    """
    # Drop the non-unique index
    op.drop_index('ix_brands_name', table_name='brands')

    # Re-create as unique index
    op.create_index('ix_brands_name', 'brands', ['name'], unique=True)

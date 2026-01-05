"""add_user_id_to_brands

Revision ID: e05187a4d632
Revises: 20251229_cascade_delete
Create Date: 2025-12-29 14:55:56.530687

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e05187a4d632'
down_revision: Union[str, None] = '20251229_cascade_delete'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add user_id to brands table to make brands per-user.

    This migration will:
    1. Delete all existing brands and mentions (clean slate)
    2. Drop unique constraint on brand name
    3. Add user_id column with foreign key to users table
    4. Add unique constraint on (user_id, name)
    """
    # Delete all existing mentions and brands (clean slate)
    op.execute("DELETE FROM mentions")
    op.execute("DELETE FROM brands")

    # Drop the unique constraint on name (find it dynamically)
    op.execute("""
        DO $$
        DECLARE
            constraint_name TEXT;
        BEGIN
            -- Find the unique constraint on the name column
            SELECT tc.constraint_name INTO constraint_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.constraint_column_usage AS ccu
                ON tc.constraint_name = ccu.constraint_name
            WHERE tc.table_name = 'brands'
            AND tc.constraint_type = 'UNIQUE'
            AND ccu.column_name = 'name';

            -- Drop the constraint if it exists
            IF constraint_name IS NOT NULL THEN
                EXECUTE format('ALTER TABLE brands DROP CONSTRAINT %I', constraint_name);
            END IF;
        END $$;
    """)

    # Add user_id column (not null, with foreign key)
    op.add_column('brands', sa.Column('user_id', sa.Integer(), nullable=False))
    op.create_foreign_key(
        'brands_user_id_fkey',
        'brands',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Add unique constraint on (user_id, name) so each user can't have duplicate brand names
    op.create_unique_constraint('brands_user_id_name_key', 'brands', ['user_id', 'name'])


def downgrade() -> None:
    """
    Remove user_id from brands table.
    """
    # Drop unique constraint
    op.drop_constraint('brands_user_id_name_key', 'brands', type_='unique')

    # Drop foreign key and column
    op.drop_constraint('brands_user_id_fkey', 'brands', type_='foreignkey')
    op.drop_column('brands', 'user_id')

    # Restore unique constraint on name
    op.create_unique_constraint('brands_name_key', 'brands', ['name'])

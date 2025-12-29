"""Add CASCADE DELETE to mentions.brand_id foreign key

Revision ID: 20251229_cascade_delete
Revises: 20251222_1236_aba048a4661d
Create Date: 2025-12-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251229_cascade_delete'
down_revision = 'aba048a4661d'
branch_labels = None
depends_on = None


def upgrade():
    """
    Update the foreign key constraint on mentions.brand_id to include CASCADE DELETE.

    This allows mentions to be automatically deleted when their parent brand is deleted.
    """
    # Drop the existing foreign key constraint
    # Note: The constraint name may vary depending on how it was created
    # We'll use a raw SQL command to find and drop it

    op.execute("""
        DO $$
        DECLARE
            constraint_name TEXT;
        BEGIN
            -- Find the constraint name
            SELECT tc.constraint_name INTO constraint_name
            FROM information_schema.table_constraints AS tc
            WHERE tc.table_name = 'mentions'
            AND tc.constraint_type = 'FOREIGN KEY'
            AND tc.constraint_name LIKE '%brand_id%';

            -- Drop the constraint if it exists
            IF constraint_name IS NOT NULL THEN
                EXECUTE format('ALTER TABLE mentions DROP CONSTRAINT %I', constraint_name);
            END IF;
        END $$;
    """)

    # Add the new foreign key constraint with CASCADE DELETE
    op.create_foreign_key(
        'mentions_brand_id_fkey',  # constraint name
        'mentions',  # source table
        'brands',  # target table
        ['brand_id'],  # source column
        ['id'],  # target column
        ondelete='CASCADE'
    )


def downgrade():
    """
    Revert to the original foreign key constraint without CASCADE DELETE.
    """
    # Drop the CASCADE DELETE constraint
    op.drop_constraint('mentions_brand_id_fkey', 'mentions', type_='foreignkey')

    # Re-create the original constraint without CASCADE
    op.create_foreign_key(
        'mentions_brand_id_fkey',
        'mentions',
        'brands',
        ['brand_id'],
        ['id']
    )

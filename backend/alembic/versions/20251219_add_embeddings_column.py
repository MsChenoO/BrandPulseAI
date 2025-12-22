"""Add embeddings column and entities JSON field

Revision ID: phase4_embeddings
Revises: 4fc5c474fb17
Create Date: 2025-12-19

Phase 4: Add vector embeddings column for semantic search and entities JSON for entity extraction
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = 'phase4_embeddings'
down_revision = '4fc5c474fb17'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable pgvector extension (idempotent)
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # Add embedding column (1536 dimensions for text-embedding-ada-002 / nomic-embed-text)
    # Using 768 dimensions for nomic-embed-text which is what Ollama uses
    op.add_column('mentions',
        sa.Column('embedding', Vector(768), nullable=True)
    )

    # Add entities JSON column for storing extracted entities
    op.add_column('mentions',
        sa.Column('entities', postgresql.JSON(astext_type=sa.Text()), nullable=True)
    )

    # Create index for vector similarity search (using cosine distance)
    # This significantly speeds up similarity queries
    op.execute(
        'CREATE INDEX mentions_embedding_idx ON mentions '
        'USING ivfflat (embedding vector_cosine_ops) '
        'WITH (lists = 100)'
    )


def downgrade() -> None:
    # Drop index first
    op.execute('DROP INDEX IF EXISTS mentions_embedding_idx')

    # Drop columns
    op.drop_column('mentions', 'entities')
    op.drop_column('mentions', 'embedding')

    # Note: Not dropping the pgvector extension as other tables might use it

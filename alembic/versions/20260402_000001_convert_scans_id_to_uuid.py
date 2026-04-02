"""Convert scans.id from string to UUID.

Revision ID: 20260402_000001
Revises:
Create Date: 2026-04-02 00:00:01
"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "20260402_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE scans
        ALTER COLUMN id TYPE UUID
        USING id::uuid
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE scans
        ALTER COLUMN id TYPE TEXT
        USING id::text
        """
    )

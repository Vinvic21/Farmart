"""confirm existing pending buyer orders

Revision ID: d7e8f9a0b1c2
Revises: c5a1d2e3f4b5
Create Date: 2026-09-02

"""
from alembic import op


revision = 'd7e8f9a0b1c2'
down_revision = 'c5a1d2e3f4b5'
branch_labels = None
depends_on = None


def upgrade():
    # Existing orders were created before checkout stopped requiring approval.
    # Keep paid/rejected records unchanged and make pending records payable.
    op.execute("UPDATE orders SET status = 'confirmed' WHERE status = 'pending'")
    op.execute("UPDATE order_items SET status = 'confirmed' WHERE status = 'pending'")


def downgrade():
    # The original status of each confirmed record cannot be recovered safely.
    pass
"""new models migrations

Revision ID: 2375571466e3
Revises: 9e0cf6bc2627
Create Date: 2026-08-26 23:36:15.720599

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2375571466e3'
down_revision = '9e0cf6bc2627'
branch_labels = None
depends_on = None


def upgrade():
    # No-op: every table this migration originally created (users, animals,
    # carts, orders, profiles, cart_items, order_items, payments) was already
    # created by 099f32fc1a9f and 9e0cf6bc2627. This migration was generated
    # against a database that wasn't properly tracked by alembic_version, so
    # autogenerate produced full CREATE TABLEs instead of a real diff.
    # Left as a no-op so the revision chain and everyone's local
    # alembic_version history stay intact.
    pass


def downgrade():
    pass
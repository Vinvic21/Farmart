"""add profile name and bio fields

Revision ID: c5a1d2e3f4b5
Revises: bba22ab434e2
Create Date: 2026-09-02

"""
from alembic import op
import sqlalchemy as sa


revision = 'c5a1d2e3f4b5'
down_revision = 'bba22ab434e2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('profiles', schema=None) as batch_op:
        batch_op.add_column(sa.Column('first_name', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('last_name', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('bio', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('profiles', schema=None) as batch_op:
        batch_op.drop_column('bio')
        batch_op.drop_column('last_name')
        batch_op.drop_column('first_name')
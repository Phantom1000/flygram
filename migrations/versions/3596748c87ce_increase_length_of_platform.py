"""increase length of platform

Revision ID: 3596748c87ce
Revises: 8ebc9870d286
Create Date: 2024-05-20 19:21:41.436770

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3596748c87ce'
down_revision = '8ebc9870d286'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('session', schema=None) as batch_op:
        batch_op.alter_column('platform',
               existing_type=sa.VARCHAR(length=100),
               type_=sa.String(length=200),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('session', schema=None) as batch_op:
        batch_op.alter_column('platform',
               existing_type=sa.String(length=200),
               type_=sa.VARCHAR(length=100),
               existing_nullable=True)

    # ### end Alembic commands ###

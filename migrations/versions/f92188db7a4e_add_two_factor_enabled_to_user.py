"""add two_factor_enabled to user

Revision ID: f92188db7a4e
Revises: 9642058b3a09
Create Date: 2024-08-10 16:20:45.161916

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f92188db7a4e'
down_revision = '9642058b3a09'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('two_factor_enabled', sa.Boolean(), server_default=sa.text('false'), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('two_factor_enabled')

    # ### end Alembic commands ###

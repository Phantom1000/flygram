"""add community fk

Revision ID: adf240b4bd42
Revises: 5d4fea096797
Create Date: 2024-06-06 15:50:24.909117

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'adf240b4bd42'
down_revision = '5d4fea096797'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.add_column(sa.Column('community_id', sa.Integer(), nullable=True))
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.create_index(batch_op.f('ix_post_community_id'), ['community_id'], unique=False)
        batch_op.create_foreign_key(None, 'community', ['community_id'], ['id'], ondelete='cascade')
        batch_op.drop_column('by_user')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('post', schema=None) as batch_op:
        batch_op.add_column(sa.Column('by_user', sa.BOOLEAN(), autoincrement=False, nullable=False))
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_post_community_id'))
        batch_op.alter_column('user_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.drop_column('community_id')

    # ### end Alembic commands ###

"""add messages

Revision ID: 67609222f411
Revises: 5dbe6f3ebb60
Create Date: 2024-06-12 08:53:15.380692

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '67609222f411'
down_revision = '5dbe6f3ebb60'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('message',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body', sa.String(length=200), nullable=False),
    sa.Column('date', sa.DateTime(), nullable=False),
    sa.Column('sender_id', sa.Integer(), nullable=False),
    sa.Column('recipient_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['recipient_id'], ['user.id'], ondelete='cascade'),
    sa.ForeignKeyConstraint(['sender_id'], ['user.id'], ondelete='cascade'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_message_date'), ['date'], unique=False)
        batch_op.create_index(batch_op.f('ix_message_recipient_id'), ['recipient_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_message_sender_id'), ['sender_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_message_sender_id'))
        batch_op.drop_index(batch_op.f('ix_message_recipient_id'))
        batch_op.drop_index(batch_op.f('ix_message_date'))

    op.drop_table('message')
    # ### end Alembic commands ###

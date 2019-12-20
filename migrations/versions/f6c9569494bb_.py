"""empty message

Revision ID: f6c9569494bb
Revises: a2ca5292a97b
Create Date: 2019-12-20 00:13:51.703627

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f6c9569494bb'
down_revision = 'a2ca5292a97b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('new_email', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_users_new_email'), 'users', ['new_email'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_users_new_email'), table_name='users')
    op.drop_column('users', 'new_email')
    # ### end Alembic commands ###
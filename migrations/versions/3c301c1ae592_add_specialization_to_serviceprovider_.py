"""Add specialization to ServiceProvider and add meal models

Revision ID: 3c301c1ae592
Revises: 05ae9c6283c0
Create Date: 2025-04-09 13:09:46.567875

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3c301c1ae592'
down_revision = '05ae9c6283c0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('payment', schema=None) as batch_op:
        batch_op.add_column(sa.Column('meal_order_id', sa.Integer(), nullable=True))
        batch_op.alter_column('booking_id',
               existing_type=sa.INTEGER(),
               nullable=True)
        batch_op.create_foreign_key(None, 'meal_order', ['meal_order_id'], ['id'])

    with op.batch_alter_table('service_provider', schema=None) as batch_op:
        batch_op.add_column(sa.Column('specialization', sa.String(length=50), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('service_provider', schema=None) as batch_op:
        batch_op.drop_column('specialization')

    with op.batch_alter_table('payment', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.alter_column('booking_id',
               existing_type=sa.INTEGER(),
               nullable=False)
        batch_op.drop_column('meal_order_id')

    # ### end Alembic commands ###

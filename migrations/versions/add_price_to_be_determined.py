
"""add price_to_be_determined column

Revision ID: add_price_to_be_determined
Revises: 3c301c1ae592
Create Date: 2025-04-10 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_price_to_be_determined'
down_revision = '3c301c1ae592'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('service', sa.Column('price_to_be_determined', sa.Boolean(), nullable=True, default=False))
    # تعيين القيمة الافتراضية لجميع السجلات القديمة
    op.execute("UPDATE service SET price_to_be_determined = FALSE WHERE price_to_be_determined IS NULL")
    op.alter_column('service', 'price_to_be_determined', nullable=False)


def downgrade():
    op.drop_column('service', 'price_to_be_determined')

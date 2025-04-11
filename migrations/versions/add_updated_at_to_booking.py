
"""add updated_at to booking table

Revision ID: 8c9db3712ef4
Revises: 3c301c1ae592
Create Date: 2025-04-11 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = '8c9db3712ef4'
down_revision = '3c301c1ae592'
branch_labels = None
depends_on = None


def upgrade():
    # إضافة عمود updated_at إلى جدول booking
    op.add_column('booking', sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now()))
    
    # تحديث القيم الموجودة لتكون مساوية لـ created_at
    connection = op.get_bind()
    connection.execute(sa.text("UPDATE booking SET updated_at = created_at"))


def downgrade():
    # حذف عمود updated_at من جدول booking
    op.drop_column('booking', 'updated_at')

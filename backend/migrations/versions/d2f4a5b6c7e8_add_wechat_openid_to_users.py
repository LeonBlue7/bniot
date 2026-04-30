"""add wechat_openid to users table

Revision ID: d2f4a5b6c7e8
Revises: c1e2f3a4b5d6
Create Date: 2024-04-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'd2f4a5b6c7e8'
down_revision = 'c1e2f3a4b5d6'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # 添加 wechat_openid 字段
    op.add_column('users', sa.Column('wechat_openid', sa.String(100), nullable=True, unique=True))
    # 创建索引
    op.create_index('ix_users_wechat_openid', 'users', ['wechat_openid'])

def downgrade() -> None:
    # 删除索引
    op.drop_index('ix_users_wechat_openid', table_name='users')
    # 删除字段
    op.drop_column('users', 'wechat_openid')

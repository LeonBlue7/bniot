"""add zone_tenants table for device permission

Revision ID: c1e2f3a4b5d6
Revises: b9f4d3e6f2c5
Create Date: 2024-04-20 10:00:00.000000

""" 
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c1e2f3a4b5d6'
down_revision = 'b9f4d3e6f2c5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 创建分区-租户授权关联表
    op.create_table(
        'zone_tenants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('zone_id', sa.Integer(), nullable=False),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['zone_id'], ['zones.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('zone_id', 'tenant_id', name='uq_zone_tenant'),
    )

    # 创建索引
    op.create_index('idx_zone_tenants_zone_id', 'zone_tenants', ['zone_id'])
    op.create_index('idx_zone_tenants_tenant_id', 'zone_tenants', ['tenant_id'])


def downgrade() -> None:
    # 删除索引
    op.drop_index('idx_zone_tenants_tenant_id', table_name='zone_tenants')
    op.drop_index('idx_zone_tenants_zone_id', table_name='zone_tenants')

    # 删除表
    op.drop_table('zone_tenants')

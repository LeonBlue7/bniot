"""Add device indexes for zone_id and protocol_version

Revision ID: a8f3c2d5e9b1
Revises: 7d2b1ebe5d86
Create Date: 2026-04-15 09:58:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'a8f3c2d5e9b1'
down_revision: Union[str, Sequence[str], None] = '7d2b1ebe5d86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加设备表索引以优化查询性能."""
    # Zone 关联索引 - 用于设备列表按分区筛选和分区名称关联查询
    op.create_index(
        'idx_devices_zone_id',
        'devices',
        ['zone_id'],
        unique=False
    )

    # 协议版本索引 - 用于设备列表按协议版本筛选
    op.create_index(
        'idx_devices_protocol_version',
        'devices',
        ['protocol_version'],
        unique=False
    )


def downgrade() -> None:
    """移除设备表索引."""
    op.drop_index('idx_devices_protocol_version', table_name='devices')
    op.drop_index('idx_devices_zone_id', table_name='devices')

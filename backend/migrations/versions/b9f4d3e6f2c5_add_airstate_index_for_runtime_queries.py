"""Add airstate index for runtime queries

Revision ID: b9f4d3e6f2c5
Revises: a8f3c2d5e9b1
Create Date: 2026-04-15 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b9f4d3e6f2c5'
down_revision: Union[str, Sequence[str], None] = 'a8f3c2d5e9b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """添加 airstate 复合索引以优化运行时间查询性能."""
    op.create_index(
        'idx_device_data_airstate',
        'device_data',
        ['device_id', 'tenant_id', 'airstate'],
        unique=False
    )


def downgrade() -> None:
    """移除 airstate 索引."""
    op.drop_index('idx_device_data_airstate', table_name='device_data')

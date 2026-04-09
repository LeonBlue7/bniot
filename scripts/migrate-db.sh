#!/bin/bash
# BNIoT 数据库迁移脚本
# 用于从旧版本 schema 迁移到新版本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "BNIoT 数据库迁移脚本"
echo "=========================================="

# 检查环境变量
if [ -z "$POSTGRES_HOST" ]; then
    POSTGRES_HOST="localhost"
fi

if [ -z "$POSTGRES_PORT" ]; then
    POSTGRES_PORT="5432"
fi

if [ -z "$POSTGRES_DB" ]; then
    echo -e "${RED}错误: POSTGRES_DB 环境变量未设置${NC}"
    exit 1
fi

if [ -z "$POSTGRES_USER" ]; then
    echo -e "${RED}错误: POSTGRES_USER 环境变量未设置${NC}"
    exit 1
fi

if [ -z "$POSTGRES_PASSWORD" ]; then
    echo -e "${RED}错误: POSTGRES_PASSWORD 环境变量未设置${NC}"
    exit 1
fi

# 设置 PGPASSWORD 环境变量
export PGPASSWORD="$POSTGRES_PASSWORD"

echo ""
echo "数据库连接信息:"
echo "  主机: $POSTGRES_HOST"
echo "  端口: $POSTGRES_PORT"
echo "  数据库: $POSTGRES_DB"
echo "  用户: $POSTGRES_USER"
echo ""

# 检查 devices 表是否存在 metadata 列
echo "检查 devices 表结构..."
METADATA_EXISTS=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "
    SELECT COUNT(*)
    FROM information_schema.columns
    WHERE table_name = 'devices'
    AND column_name = 'metadata';
")

if [ "$METADATA_EXISTS" = "1" ]; then
    echo -e "${YELLOW}发现旧版 metadata 列，开始迁移...${NC}"

    # 检查是否已存在 extra_data 列
    EXTRA_DATA_EXISTS=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "
        SELECT COUNT(*)
        FROM information_schema.columns
        WHERE table_name = 'devices'
        AND column_name = 'extra_data';
    ")

    if [ "$EXTRA_DATA_EXISTS" = "0" ]; then
        echo "添加 extra_data 列..."
        psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
            ALTER TABLE devices ADD COLUMN extra_data JSONB DEFAULT '{}';
        "

        echo "迁移 metadata 数据到 extra_data..."
        psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
            UPDATE devices SET extra_data = metadata WHERE metadata IS NOT NULL;
        "

        echo "删除 metadata 列..."
        psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
            ALTER TABLE devices DROP COLUMN metadata;
        "

        echo -e "${GREEN}✓ metadata 列迁移完成${NC}"
    else
        echo -e "${YELLOW}extra_data 列已存在，跳过迁移${NC}"
        echo "请手动检查数据一致性"
    fi
else
    echo -e "${GREEN}✓ devices 表结构已是最新版本${NC}"
fi

# 检查 TimescaleDB 扩展
echo ""
echo "检查 TimescaleDB 扩展..."
TIMESCALEDB_EXISTS=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "
    SELECT COUNT(*)
    FROM pg_extension
    WHERE extname = 'timescaledb';
")

if [ "$TIMESCALEDB_EXISTS" = "0" ]; then
    echo -e "${YELLOW}TimescaleDB 扩展未安装，尝试创建...${NC}"
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
        CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
    " || echo -e "${RED}警告: TimescaleDB 扩展创建失败，请确保使用 timescale/timescaledb 镜像${NC}"
else
    echo -e "${GREEN}✓ TimescaleDB 扩展已安装${NC}"
fi

# 检查 device_data 是否为 hypertable
echo ""
echo "检查 device_data hypertable 状态..."
IS_HYPERTABLE=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "
    SELECT COUNT(*)
    FROM timescaledb_information.hypertables
    WHERE hypertable_name = 'device_data';
" 2>/dev/null || echo "0")

if [ "$IS_HYPERTABLE" = "0" ]; then
    echo -e "${YELLOW}device_data 表尚未配置为 hypertable，开始配置...${NC}"

    # 创建 hypertable
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
        SELECT create_hypertable(
            'device_data',
            'time',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        );
    " || echo -e "${RED}警告: hypertable 创建失败${NC}"

    # 配置压缩
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
        ALTER TABLE device_data SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'device_id, tenant_id'
        );
    " || echo -e "${RED}警告: 压缩配置失败${NC}"

    # 添加压缩策略
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
        SELECT add_compression_policy(
            'device_data',
            INTERVAL '7 days',
            if_not_exists => TRUE
        );
    " || echo -e "${RED}警告: 压缩策略添加失败${NC}"

    # 添加保留策略
    psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
        SELECT add_retention_policy(
            'device_data',
            INTERVAL '365 days',
            if_not_exists => TRUE
        );
    " || echo -e "${RED}警告: 保留策略添加失败${NC}"

    echo -e "${GREEN}✓ TimescaleDB 配置完成${NC}"
else
    echo -e "${GREEN}✓ device_data 已配置为 hypertable${NC}"
fi

# 检查 RLS 策略
echo ""
echo "检查 Row Level Security 状态..."
RLS_TABLES=$(psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "
    SELECT COUNT(*)
    FROM pg_tables
    WHERE tablename IN ('users', 'zones', 'devices', 'device_data', 'alarms', 'operation_logs')
    AND rowsecurity = true;
")

if [ "$RLS_TABLES" -lt 6 ]; then
    echo -e "${YELLOW}RLS 策略未完全配置，请手动检查 init-db.sql 中的 RLS 配置${NC}"
else
    echo -e "${GREEN}✓ RLS 策略已配置${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}迁移检查完成${NC}"
echo "=========================================="
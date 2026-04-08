#!/bin/bash
# PostgreSQL 数据库恢复脚本
# 用法: ./restore.sh <backup_file.sql.gz>

set -e

# 配置
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-bniot}"
DB_USER="${POSTGRES_USER:-bniot}"

# 检查参数
if [ -z "$1" ]; then
    echo "用法: $0 <backup_file.sql.gz>"
    echo ""
    echo "可用备份文件:"
    ls -lh /var/lib/postgresql/backups/*.sql.gz 2>/dev/null || echo "无备份文件"
    exit 1
fi

BACKUP_FILE="$1"

# 检查备份文件是否存在
if [ ! -f "$BACKUP_FILE" ]; then
    echo "错误: 备份文件不存在: $BACKUP_FILE"
    exit 1
fi

echo "========================================="
echo "开始恢复: $(date)"
echo "数据库: $DB_NAME"
echo "备份文件: $BACKUP_FILE"
echo "========================================="

# 确认操作
read -p "警告: 这将覆盖当前数据库，是否继续? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "操作已取消"
    exit 0
fi

# 断开所有连接
echo "断开所有数据库连接..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c \
    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();"

# 删除并重建数据库
echo "重建数据库..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -c "CREATE DATABASE $DB_NAME;"

# 恢复数据
echo "恢复数据..."
gunzip -c "$BACKUP_FILE" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1

echo ""
echo "恢复完成: $(date)"
echo "请验证数据库完整性"
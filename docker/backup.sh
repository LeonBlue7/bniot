#!/bin/bash
# PostgreSQL 数据库备份脚本
# 用法: ./backup.sh [daily|weekly]
# 建议: 每日凌晨2点执行

set -e

# 配置
DB_HOST="${POSTGRES_HOST:-localhost}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-bniot}"
DB_USER="${POSTGRES_USER:-bniot}"
BACKUP_DIR="/var/lib/postgresql/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_TYPE="${1:-daily}"

# 备份保留策略
DAILY_RETENTION=7      # 每日备份保留7天
WEEKLY_RETENTION=30    # 每周备份保留30天

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 备份文件名
BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${BACKUP_TYPE}_${DATE}.sql.gz"

echo "========================================="
echo "开始备份: $(date)"
echo "数据库: $DB_NAME"
echo "类型: $BACKUP_TYPE"
echo "文件: $BACKUP_FILE"
echo "========================================="

# 执行备份
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --format=plain \
    --no-owner \
    --no-privileges \
    --verbose \
    | gzip > "$BACKUP_FILE"

# 检查备份是否成功
if [ -f "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "备份成功: $BACKUP_SIZE"
else
    echo "备份失败!"
    exit 1
fi

# 清理旧备份
echo "清理旧备份..."
if [ "$BACKUP_TYPE" = "daily" ]; then
    find "$BACKUP_DIR" -name "${DB_NAME}_daily_*.sql.gz" -type f -mtime +$DAILY_RETENTION -delete
    echo "已清理 $DAILY_RETENTION 天前的每日备份"
elif [ "$BACKUP_TYPE" = "weekly" ]; then
    find "$BACKUP_DIR" -name "${DB_NAME}_weekly_*.sql.gz" -type f -mtime +$WEEKLY_RETENTION -delete
    echo "已清理 $WEEKLY_RETENTION 天前的每周备份"
fi

# 列出当前备份
echo ""
echo "当前备份列表:"
ls -lh "$BACKUP_DIR"/*.sql.gz 2>/dev/null || echo "无备份文件"

echo ""
echo "备份完成: $(date)"
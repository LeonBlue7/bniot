#!/bin/bash
# BNIoT 快速诊断与修复脚本
# 用于生产环境常见问题的诊断和修复

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SUDO="sudo"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 清除登录速率限制
clear_rate_limit() {
    log_info "清除登录速率限制..."

    source .env

    # 获取所有速率限制 key
    KEYS=$($SUDO docker exec bniot-redis redis-cli -a "${REDIS_PASSWORD}" KEYS "rate_limit:*" 2>/dev/null | tr '\n' ' ')

    if [ -n "$KEYS" ]; then
        for KEY in $KEYS; do
            $SUDO docker exec bniot-redis redis-cli -a "${REDIS_PASSWORD}" DEL "$KEY" 2>/dev/null
        done
        log_success "速率限制已清除"
    else
        log_info "无速率限制记录"
    fi
}

# 检查并创建默认用户
check_default_user() {
    log_info "检查默认用户..."

    # 检查用户是否存在
    USER_COUNT=$($SUDO docker exec bniot-postgres psql -U bniot -d bniot -t -c "SELECT COUNT(*) FROM users WHERE username='admin';" 2>/dev/null | tr -d ' ')

    if [ "$USER_COUNT" = "0" ]; then
        log_warning "默认用户不存在，正在创建..."

        # 检查租户
        TENANT_COUNT=$($SUDO docker exec bniot-postgres psql -U bniot -d bniot -t -c "SELECT COUNT(*) FROM tenants WHERE code='default';" 2>/dev/null | tr -d ' ')

        if [ "$TENANT_COUNT" = "0" ]; then
            $SUDO docker exec bniot-postgres psql -U bniot -d bniot -c \
                "INSERT INTO tenants (name, code, settings) VALUES ('默认租户', 'default', '{\"timezone\": \"Asia/Shanghai\"}');" 2>/dev/null
        fi

        # 生成密码 hash
        log_info "生成密码 hash..."
        HASH=$($SUDO docker exec bniot-backend python3 -c \
            "from passlib.context import CryptContext; pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto'); print(pwd_context.hash('admin123'))" 2>/dev/null)

        # 创建用户
        $SUDO docker exec bniot-postgres psql -U bniot -d bniot -c \
            "INSERT INTO users (tenant_id, username, password_hash, role, is_active) VALUES (1, 'admin', '${HASH}', 'admin', true);" 2>/dev/null

        log_success "默认用户创建成功"
    else
        log_success "默认用户已存在"
    fi
}

# 重置数据库密码
reset_db_password() {
    log_info "重置数据库用户密码..."

    source .env

    $SUDO docker exec bniot-postgres psql -U bniot -d bniot -c \
        "ALTER USER bniot WITH PASSWORD '${POSTGRES_PASSWORD}';" 2>/dev/null

    log_success "数据库密码已重置"
}

# 检查服务健康
check_health() {
    log_info "服务健康检查..."

    # 后端
    BACKEND=$($SUDO docker exec bniot-backend curl -s http://localhost:5000/health 2>/dev/null || echo "failed")
    if echo "$BACKEND" | grep -q "healthy"; then
        log_success "后端: 健康"
    else
        log_error "后端: 异常"
        $SUDO docker logs bniot-backend --tail 20
    fi

    # PostgreSQL
    PG=$($SUDO docker exec bniot-postgres pg_isready -U bniot 2>/dev/null || echo "failed")
    if echo "$PG" | grep -q "accepting"; then
        log_success "PostgreSQL: 健康"
    else
        log_error "PostgreSQL: 异常"
    fi

    # Redis
    source .env
    REDIS=$($SUDO docker exec bniot-redis redis-cli -a "${REDIS_PASSWORD}" ping 2>/dev/null || echo "failed")
    if echo "$REDIS" | grep -q "PONG"; then
        log_success "Redis: 健康"
    else
        log_error "Redis: 异常"
    fi

    # EMQX
    EMQX=$($SUDO docker exec bniot-emqx emqx ctl status 2>/dev/null || echo "failed")
    if echo "$EMQX" | grep -q "is running"; then
        log_success "EMQX: 健康"
    else
        log_error "EMQX: 异常"
    fi
}

# 显示帮助
show_help() {
    echo ""
    echo "BNIoT 诊断与修复工具"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  health      - 检查所有服务健康状态"
    echo "  rate-limit  - 清除登录速率限制"
    echo "  user        - 检查并创建默认用户"
    echo "  password    - 重置数据库密码"
    echo "  all         - 执行所有诊断和修复"
    echo "  help        - 显示帮助信息"
    echo ""
}

# 主逻辑
case "$1" in
    health)
        check_health
        ;;
    rate-limit)
        clear_rate_limit
        ;;
    user)
        check_default_user
        ;;
    password)
        reset_db_password
        ;;
    all)
        check_health
        clear_rate_limit
        check_default_user
        reset_db_password
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        if [ -n "$1" ]; then
            log_error "未知命令: $1"
        fi
        show_help
        ;;
esac
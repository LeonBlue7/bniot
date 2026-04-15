#!/bin/bash
# BNIoT 一键部署脚本
# 用于生产环境快速部署

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为 root 用户或有 sudo 权限
check_permissions() {
    if [ "$EUID" -ne 0 ]; then
        if ! command -v sudo &> /dev/null; then
            log_error "需要 root 权限或 sudo"
            exit 1
        fi
        SUDO="sudo"
    else
        SUDO=""
    fi
}

# 检查 Docker 和 Docker Compose
check_docker() {
    log_info "检查 Docker 环境..."

    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi

    log_success "Docker 环境检查通过"
}

# 检查环境变量文件
check_env_file() {
    log_info "检查环境变量配置..."

    if [ ! -f ".env" ]; then
        log_warning ".env 文件不存在"

        if [ -f ".env.example" ]; then
            log_info "从 .env.example 创建 .env 文件..."
            cp .env.example .env

            log_warning "请修改 .env 文件中的以下变量："
            log_warning "  - POSTGRES_PASSWORD: 数据库密码"
            log_warning "  - REDIS_PASSWORD: Redis密码"
            log_warning "  - JWT_SECRET: JWT签名密钥"
            log_warning ""
            log_warning "运行: vi .env 编辑配置文件"

            read -p "是否现在编辑 .env 文件? [y/N]: " edit_env
            if [ "$edit_env" = "y" ] || [ "$edit_env" = "Y" ]; then
                ${EDITOR:-vi} .env
            else
                log_error "请手动编辑 .env 文件后再运行部署脚本"
                exit 1
            fi
        else
            log_error ".env.example 文件不存在，无法创建 .env"
            exit 1
        fi
    fi

    # 检查必要的环境变量
    source .env

    if [ -z "$POSTGRES_PASSWORD" ] || [ "$POSTGRES_PASSWORD" = "your_secure_password_here" ]; then
        log_error "POSTGRES_PASSWORD 未设置或使用了示例值"
        exit 1
    fi

    if [ -z "$REDIS_PASSWORD" ] || [ "$REDIS_PASSWORD" = "your_redis_password_here" ]; then
        log_error "REDIS_PASSWORD 未设置或使用了示例值"
        exit 1
    fi

    if [ -z "$JWT_SECRET" ] || [ "$JWT_SECRET" = "your_jwt_secret_here" ]; then
        log_error "JWT_SECRET 未设置或使用了示例值"
        exit 1
    fi

    log_success "环境变量检查通过"
}

# 检查 SSL 证书
check_ssl_certificates() {
    log_info "检查 SSL 证书..."

    SSL_DIR="./ssl"
    if [ ! -d "$SSL_DIR" ]; then
        log_warning "SSL 目录不存在，创建..."
        mkdir -p "$SSL_DIR"
    fi

    # 检查证书文件
    CERT_FILE=$(grep SSL_CERT_FILE .env 2>/dev/null | cut -d= -f2 || echo "jxbonner.cloud_bundle.pem")
    KEY_FILE=$(grep SSL_KEY_FILE .env 2>/dev/null | cut -d= -f2 || echo "jxbonner.cloud.key")

    if [ ! -f "$SSL_DIR/$CERT_FILE" ] || [ ! -f "$SSL_DIR/$KEY_FILE" ]; then
        log_warning "SSL 证书文件不完整"
        log_warning "请将证书文件放置在 $SSL_DIR 目录:"
        log_warning "  - $CERT_FILE (证书文件)"
        log_warning "  - $KEY_FILE (私钥文件)"

        read -p "是否继续部署（使用 HTTP）? [y/N]: " continue_http
        if [ "$continue_http" != "y" ] && [ "$continue_http" != "Y" ]; then
            exit 1
        fi
    else
        log_success "SSL 证书检查通过"
    fi
}

# 构建前端
build_frontend() {
    log_info "构建前端..."

    cd frontend

    # 检查 node_modules
    if [ ! -d "node_modules" ]; then
        log_info "安装前端依赖..."
        npm install
    fi

    # 构建生产版本
    log_info "执行前端构建..."
    npm run build

    if [ ! -d "dist" ]; then
        log_error "前端构建失败，dist 目录不存在"
        exit 1
    fi

    cd ..
    log_success "前端构建完成"
}

# 清理旧数据（可选）
clean_old_data() {
    log_info "检查旧数据..."

    if [ -d "./volumes/pgdata" ] && [ -d "./volumes/pgdata/base" ]; then
        log_warning "发现已存在的数据库数据"
        read -p "是否清理旧数据重新初始化? [y/N]: " clean_data

        if [ "$clean_data" = "y" ] || [ "$clean_data" = "Y" ]; then
            log_info "停止所有服务..."
            $SUDO docker-compose down

            log_info "清理数据目录..."
            $SUDO rm -rf ./volumes/pgdata
            $SUDO rm -rf ./volumes/redis/data
            $SUDO rm -rf ./volumes/emqx/data

            log_success "旧数据已清理"
        fi
    fi
}

# 部署服务
deploy_services() {
    log_info "部署 Docker 服务..."

    # 拉取基础镜像
    log_info "拉取 Docker 镜像..."
    $SUDO docker-compose pull

    # 构建自定义镜像
    log_info "构建应用镜像..."
    $SUDO docker-compose build

    # 启动服务
    log_info "启动服务..."
    $SUDO docker-compose up -d

    # 等待服务健康
    log_info "等待服务启动..."
    sleep 10

    # 检查服务状态
    $SUDO docker-compose ps

    log_success "服务部署完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."

    # 检查后端服务
    BACKEND_HEALTH=$(curl -s http://localhost:5000/health 2>/dev/null || echo "failed")
    if [ "$BACKEND_HEALTH" = "failed" ]; then
        log_warning "后端服务未响应，等待..."
        sleep 5
        BACKEND_HEALTH=$(curl -s http://localhost:5000/health 2>/dev/null || echo "failed")
    fi

    if echo "$BACKEND_HEALTH" | grep -q "healthy"; then
        log_success "后端服务健康"
    else
        log_error "后端服务异常，查看日志:"
        $SUDO docker-compose logs backend --tail 50
        exit 1
    fi

    # 检查数据库连接
    DB_CHECK=$($SUDO docker exec bniot-postgres pg_isready -U bniot 2>/dev/null || echo "failed")
    if echo "$DB_CHECK" | grep -q "accepting"; then
        log_success "数据库服务健康"
    else
        log_error "数据库服务异常"
        exit 1
    fi

    # 检查 Redis
    REDIS_CHECK=$($SUDO docker exec bniot-redis redis-cli -a "${REDIS_PASSWORD}" ping 2>/dev/null || echo "failed")
    if echo "$REDIS_CHECK" | grep -q "PONG"; then
        log_success "Redis 服务健康"
    else
        log_error "Redis 服务异常"
        exit 1
    fi

    log_success "所有服务健康检查通过"
}

# 显示部署信息
show_deploy_info() {
    source .env

    DOMAIN=${DOMAIN:-"localhost"}

    echo ""
    echo "=========================================="
    echo "       BNIoT 部署成功！"
    echo "=========================================="
    echo ""
    echo "访问地址:"
    echo "  - 前端: https://www.${DOMAIN}"
    echo "  - API 文档: https://www.${DOMAIN}/api/docs"
    echo "  - EMQX Dashboard: http://${DOMAIN}:18083"
    echo ""
    echo "默认登录凭据:"
    echo "  - 用户名: admin"
    echo "  - 密码: admin123"
    echo ""
    echo "⚠️  请在生产环境修改默认密码！"
    echo ""
    echo "常用命令:"
    echo "  - 查看日志: sudo docker-compose logs -f"
    echo "  - 重启服务: sudo docker-compose restart"
    echo "  - 停止服务: sudo docker-compose down"
    echo ""
    echo "=========================================="
}

# 主函数
main() {
    echo ""
    echo "=========================================="
    echo "    BNIoT 一键部署脚本"
    echo "=========================================="
    echo ""

    check_permissions
    check_docker
    check_env_file
    check_ssl_certificates
    build_frontend
    clean_old_data
    deploy_services
    health_check
    show_deploy_info

    log_success "部署完成！"
}

# 执行主函数
main
#!/bin/bash
# BNIoT 启动前环境变量检查脚本
# 用于验证生产环境必需的配置项

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "BNIoT 环境变量检查"
echo "=========================================="

# 检查 .env 文件是否存在
if [ ! -f ".env" ]; then
    echo -e "${RED}错误: .env 文件不存在${NC}"
    echo "请复制 .env.example 为 .env 并填写实际值:"
    echo "  cp .env.example .env"
    exit 1
fi

# 加载 .env 文件
set -a
source .env
set +a

# 必需的环境变量列表
REQUIRED_VARS=(
    "POSTGRES_PASSWORD:数据库密码"
    "REDIS_PASSWORD:Redis密码"
    "JWT_SECRET:JWT签名密钥"
)

# 建议设置的环境变量
SUGGESTED_VARS=(
    "POSTGRES_DB:数据库名称"
    "POSTGRES_USER:数据库用户"
    "EMQX_DASHBOARD_PASSWORD:EMQX仪表板密码"
)

# 错误计数
ERRORS=0
WARNINGS=0

# 检查必需变量
echo ""
echo "检查必需环境变量..."
for item in "${REQUIRED_VARS[@]}"; do
    IFS=':' read -r var desc <<< "$item"
    if [ -z "${!var}" ]; then
        echo -e "${RED}✗ $var ($desc) 未设置${NC}"
        ERRORS=$((ERRORS + 1))
    elif [[ "${!var}" == *"changeme"* ]] || [[ "${!var}" == *"your_"* ]] || [[ "${!var}" == *"password_here"* ]]; then
        echo -e "${RED}✗ $var ($desc) 使用了占位符值${NC}"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}✓ $var ($desc) 已设置${NC}"
    fi
done

# 检查建议变量
echo ""
echo "检查建议环境变量..."
for item in "${SUGGESTED_VARS[@]}"; do
    IFS=':' read -r var desc <<< "$item"
    if [ -z "${!var}" ]; then
        echo -e "${YELLOW}⚠ $var ($desc) 未设置，将使用默认值${NC}"
        WARNINGS=$((WARNINGS + 1))
    else
        echo -e "${GREEN}✓ $var ($desc) 已设置${NC}"
    fi
done

# 检查密码强度
echo ""
echo "检查密码强度..."
check_password_strength() {
    local var=$1
    local value="${!var}"
    local min_length=12

    if [ -n "$value" ]; then
        if [ ${#value} -lt $min_length ]; then
            echo -e "${YELLOW}⚠ $var 长度小于 $min_length 字符${NC}"
            WARNINGS=$((WARNINGS + 1))
        else
            echo -e "${GREEN}✓ $var 长度符合要求${NC}"
        fi
    fi
}

check_password_strength "POSTGRES_PASSWORD"
check_password_strength "REDIS_PASSWORD"
check_password_strength "JWT_SECRET"

# 检查 JWT_SECRET 是否为强密钥
if [ -n "$JWT_SECRET" ]; then
    if [ ${#JWT_SECRET} -lt 32 ]; then
        echo -e "${YELLOW}⚠ JWT_SECRET 建议长度至少 32 字符${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
fi

# 检查 SSL 证书
echo ""
echo "检查 SSL 证书..."
if [ -d "ssl" ]; then
    if [ -f "ssl/fullchain.pem" ] && [ -f "ssl/privkey.pem" ]; then
        echo -e "${GREEN}✓ SSL 证书文件存在${NC}"
    else
        echo -e "${YELLOW}⚠ SSL 目录存在但证书文件不完整${NC}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo -e "${YELLOW}⚠ SSL 目录不存在，HTTPS 可能无法使用${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

# 检查 Docker 和 Docker Compose
echo ""
echo "检查 Docker 环境..."
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker 已安装${NC}"
else
    echo -e "${RED}✗ Docker 未安装${NC}"
    ERRORS=$((ERRORS + 1))
fi

if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    echo -e "${GREEN}✓ Docker Compose 已安装${NC}"
else
    echo -e "${RED}✗ Docker Compose 未安装${NC}"
    ERRORS=$((ERRORS + 1))
fi

# 总结
echo ""
echo "=========================================="
echo "检查结果:"
echo -e "错误: ${RED}$ERRORS${NC}"
echo -e "警告: ${YELLOW}$WARNINGS${NC}"
echo "=========================================="

if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}环境检查失败，请修复上述错误后重试${NC}"
    exit 1
elif [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}环境检查通过，但存在警告建议处理${NC}"
    exit 0
else
    echo -e "${GREEN}环境检查通过${NC}"
    exit 0
fi
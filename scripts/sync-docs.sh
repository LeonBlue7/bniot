#!/bin/bash
# 文档同步脚本
# 根据代码变更自动更新相关文档
# 确保代码与文档功能描述保持一致

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "📚 检查文档同步状态..."

# 标记是否需要更新
NEED_UPDATE=false
UPDATE_FILES=""
UPDATE_REASONS=""

# 检查关键源文件的变更
check_and_update() {
    local source_file="$1"
    local doc_file="$2"
    local trigger_desc="$3"

    if [ -f "$PROJECT_DIR/$source_file" ]; then
        local source_mtime=$(stat -c %Y "$PROJECT_DIR/$source_file" 2>/dev/null || stat -f %m "$PROJECT_DIR/$source_file" 2>/dev/null)
        local doc_mtime=0

        if [ -f "$PROJECT_DIR/$doc_file" ]; then
            doc_mtime=$(stat -c %Y "$PROJECT_DIR/$doc_file" 2>/dev/null || stat -f %m "$PROJECT_DIR/$doc_file" 2>/dev/null)
        fi

        if [ "$source_mtime" -gt "$doc_mtime" ]; then
            echo "  ⚠️  $trigger_desc 已更新，需要同步 $doc_file"
            NEED_UPDATE=true
            UPDATE_FILES="$UPDATE_FILES\n  - $doc_file"
            UPDATE_REASONS="$UPDATE_REASONS\n  - $trigger_desc → $doc_file"
        fi
    fi
}

# ========================================
# 核心业务逻辑 → CLAUDE.md 映射
# ========================================

# 版本检测逻辑
check_and_update "backend/app/services/version_detector.py" "CLAUDE.md" "版本检测逻辑"

# 设备离线监控
check_and_update "backend/app/services/device_monitor.py" "CLAUDE.md" "设备离线监控逻辑"

# MQTT 消息处理
check_and_update "backend/app/mqtt/handlers.py" "CLAUDE.md" "MQTT 消息处理逻辑"

# 协议解析器
check_and_update "backend/app/services/protocol_parser.py" "CLAUDE.md" "协议解析器"

# 电流值转换逻辑
check_and_update "backend/app/mqtt/handlers.py" "docs/CODEMAPS/backend.md" "MQTT 处理器"

# ========================================
# 后端服务 → CODEMAPS/backend.md 映射
# ========================================

check_and_update "backend/app/services/__init__.py" "docs/CODEMAPS/backend.md" "后端服务模块导出"
check_and_update "backend/app/main.py" "docs/CODEMAPS/backend.md" "FastAPI 应用入口"
check_and_update "backend/app/services/version_detector.py" "docs/CODEMAPS/backend.md" "版本检测服务"
check_and_update "backend/app/services/device_monitor.py" "docs/CODEMAPS/backend.md" "设备监控服务"
check_and_update "backend/app/core/config.py" "docs/CODEMAPS/backend.md" "配置管理"
check_and_update "backend/app/models/models.py" "docs/CODEMAPS/backend.md" "数据模型"

# ========================================
# 前端组件 → CODEMAPS/frontend.md 映射
# ========================================

check_and_update "frontend/src/views/Devices.vue" "docs/CODEMAPS/frontend.md" "设备管理页面"
check_and_update "frontend/src/views/Reports.vue" "docs/CODEMAPS/frontend.md" "报表分析页面"
check_and_update "frontend/src/views/Dashboard.vue" "docs/CODEMAPS/frontend.md" "仪表盘页面"
check_and_update "frontend/src/api/devices.ts" "docs/CODEMAPS/frontend.md" "设备 API"
check_and_update "frontend/src/api/reports.ts" "docs/CODEMAPS/frontend.md" "报表 API"
check_and_update "frontend/src/utils/websocket.ts" "docs/CODEMAPS/frontend.md" "WebSocket 工具"

# ========================================
# 环境配置文档映射
# ========================================
# ========================================
# 环境配置文档映射
# ========================================

check_and_update ".env.example" "docs/ENV.md" ".env.example 配置模板"

# ========================================
# Docker 配置文档映射
# ========================================

check_and_update "docker-compose.yml" "docs/RUNBOOK.md" "Docker Compose 配置"
check_and_update "backend/Dockerfile" "docs/RUNBOOK.md" "后端 Dockerfile"
check_and_update "frontend/Dockerfile" "docs/RUNBOOK.md" "前端 Dockerfile"

# ========================================
# CLAUDE.md → README.md 映射
# ========================================

check_and_update "CLAUDE.md" "README.md" "CLAUDE.md 项目说明"

# ========================================
# 测试文件文档映射
# ========================================

check_and_update "backend/tests/unit/test_device_monitor.py" "docs/CODEMAPS/backend.md" "设备监控测试"
check_and_update "backend/tests/unit/test_version_detector.py" "docs/CODEMAPS/backend.md" "版本检测测试"
check_and_update "frontend/playwright.config.ts" "docs/CODEMAPS/frontend.md" "E2E 测试配置"
check_and_update "frontend/e2e/*.spec.ts" "docs/CODEMAPS/frontend.md" "E2E 测试用例"

# ========================================
# 目录级别批量检查（保持原有逻辑）
# ========================================

# 检查后端代码目录变更
if git diff --name-only HEAD~1 2>/dev/null | grep -q "backend/app/"; then
    backend_code_mtime=$(find "$PROJECT_DIR/backend/app" -type f -name "*.py" -exec stat -c %Y {} \; 2>/dev/null | sort -rn | head -1)
    backend_doc_mtime=0
    if [ -f "$PROJECT_DIR/docs/CODEMAPS/backend.md" ]; then
        backend_doc_mtime=$(stat -c %Y "$PROJECT_DIR/docs/CODEMAPS/backend.md" 2>/dev/null || stat -f %m "$PROJECT_DIR/docs/CODEMAPS/backend.md" 2>/dev/null)
    fi
    if [ -n "$backend_code_mtime" ] && [ "$backend_code_mtime" -gt "$backend_doc_mtime" ] 2>/dev/null; then
        # 检查是否已被前面的单文件检查捕获
        if ! echo "$UPDATE_FILES" | grep -q "docs/CODEMAPS/backend.md"; then
            echo "  ⚠️  后端代码目录已更新，需要同步 docs/CODEMAPS/backend.md"
            NEED_UPDATE=true
            UPDATE_FILES="$UPDATE_FILES\n  - docs/CODEMAPS/backend.md"
            UPDATE_REASONS="$UPDATE_REASONS\n  - backend/app/* → docs/CODEMAPS/backend.md"
        fi
    fi
fi

# 检查前端代码目录变更
if git diff --name-only HEAD~1 2>/dev/null | grep -q "frontend/src/"; then
    frontend_code_mtime=$(find "$PROJECT_DIR/frontend/src" -type f \( -name "*.ts" -o -name "*.vue" \) -exec stat -c %Y {} \; 2>/dev/null | sort -rn | head -1)
    frontend_doc_mtime=0
    if [ -f "$PROJECT_DIR/docs/CODEMAPS/frontend.md" ]; then
        frontend_doc_mtime=$(stat -c %Y "$PROJECT_DIR/docs/CODEMAPS/frontend.md" 2>/dev/null || stat -f %m "$PROJECT_DIR/docs/CODEMAPS/frontend.md" 2>/dev/null)
    fi
    if [ -n "$frontend_code_mtime" ] && [ "$frontend_code_mtime" -gt "$frontend_doc_mtime" ] 2>/dev/null; then
        if ! echo "$UPDATE_FILES" | grep -q "docs/CODEMAPS/frontend.md"; then
            echo "  ⚠️  前端代码目录已更新，需要同步 docs/CODEMAPS/frontend.md"
            NEED_UPDATE=true
            UPDATE_FILES="$UPDATE_FILES\n  - docs/CODEMAPS/frontend.md"
            UPDATE_REASONS="$UPDATE_REASONS\n  - frontend/src/* → docs/CODEMAPS/frontend.md"
        fi
    fi
fi

# ========================================
# 输出结果
# ========================================

if [ "$NEED_UPDATE" = true ]; then
    echo ""
    echo "❌ 文档同步检查失败"
    echo ""
    echo "📋 需要更新的文档:"
    echo -e "$UPDATE_FILES"
    echo ""
    echo "🔗 变更原因:"
    echo -e "$UPDATE_REASONS"
    echo ""
    echo "💡 请执行以下步骤:"
    echo "   1. 运行 claude /everything-claude-code:update-docs"
    echo "   2. git add docs/ CLAUDE.md README.md"
    echo "   3. git commit"
    echo ""
    echo "   或手动更新文档后重新提交"
    echo ""
    echo "⚠️  使用 --no-verify 跳过检查可能导致文档与代码不一致"
    exit 1
else
    echo "✅ 文档同步状态良好"
    exit 0
fi
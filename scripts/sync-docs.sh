#!/bin/bash
# 文档同步脚本
# 根据代码变更自动更新相关文档

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "📚 检查文档同步状态..."

# 标记是否需要更新
NEED_UPDATE=false
UPDATE_FILES=""

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
            echo "  ⚠️  $trigger_desc 已更新，需要同步文档"
            NEED_UPDATE=true
            UPDATE_FILES="$UPDATE_FILES\n  - $doc_file"
        fi
    fi
}

# 检查环境变量文档
check_and_update ".env.example" "docs/ENV.md" ".env.example"

# 检查前端脚本文档
check_and_update "frontend/package.json" "docs/CONTRIBUTING.md" "package.json"

# 检查后端代码结构
if git diff --name-only HEAD~1 2>/dev/null | grep -q "backend/app/"; then
    echo "  ⚠️  后端代码已更新，需要同步 docs/CODEMAPS/backend.md"
    NEED_UPDATE=true
    UPDATE_FILES="$UPDATE_FILES\n  - docs/CODEMAPS/backend.md"
fi

# 检查前端代码结构
if git diff --name-only HEAD~1 2>/dev/null | grep -q "frontend/src/"; then
    echo "  ⚠️  前端代码已更新，需要同步 docs/CODEMAPS/frontend.md"
    NEED_UPDATE=true
    UPDATE_FILES="$UPDATE_FILES\n  - docs/CODEMAPS/frontend.md"
fi

# 检查 Docker 配置
check_and_update "docker-compose.yml" "docs/RUNBOOK.md" "docker-compose.yml"

# 输出结果
if [ "$NEED_UPDATE" = true ]; then
    echo ""
    echo "📋 需要更新的文档:"
    echo -e "$UPDATE_FILES"
    echo ""
    echo "💡 请运行以下命令更新文档:"
    echo "   claude /everything-claude-code:update-docs"
    echo ""
    echo "   或手动更新后重新提交"
    exit 1
else
    echo "✅ 文档同步状态良好"
    exit 0
fi
#!/bin/bash
# Git pre-commit hook: 文档同步检查
# 此文件应链接到 .git/hooks/pre-commit

set -e

echo "🔍 Pre-commit: 检查文档同步..."

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SYNC_SCRIPT="$PROJECT_ROOT/scripts/sync-docs.sh"

# 检查脚本是否存在
if [ ! -f "$SYNC_SCRIPT" ]; then
    echo "⚠️  sync-docs.sh 不存在，跳过文档同步检查"
    exit 0
fi

# 运行文档同步检查
"$SYNC_SCRIPT"

# 如果同步检查失败，提示用户
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 提交被阻止：文档需要同步更新"
    echo ""
    echo "请执行以下步骤后重新提交:"
    echo "  1. 运行 claude /everything-claude-code:update-docs"
    echo "  2. git add docs/"
    echo "  3. git commit"
    echo ""
    echo "或使用 --no-verify 跳过检查（不推荐）:"
    echo "  git commit --no-verify"
    echo ""
    exit 1
fi

exit 0
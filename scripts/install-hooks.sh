#!/bin/bash
# 安装 Git Hooks
# 将项目的 hook 脚本链接到 .git/hooks/

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
GIT_HOOKS_DIR="$PROJECT_DIR/.git/hooks"

echo "🔗 安装 Git Hooks..."

# 创建 hooks 目录（如果不存在）
mkdir -p "$GIT_HOOKS_DIR"

# 链接 pre-commit hook
if [ -f "$PROJECT_DIR/scripts/pre-commit.sh" ]; then
    ln -sf "$PROJECT_DIR/scripts/pre-commit.sh" "$GIT_HOOKS_DIR/pre-commit"
    chmod +x "$GIT_HOOKS_DIR/pre-commit"
    echo "  ✅ pre-commit hook 已安装"
fi

# 链接其他 hooks（如有）
for hook in commit-msg post-commit pre-push; do
    if [ -f "$PROJECT_DIR/scripts/$hook.sh" ]; then
        ln -sf "$PROJECT_DIR/scripts/$hook.sh" "$GIT_HOOKS_DIR/$hook"
        chmod +x "$GIT_HOOKS_DIR/$hook"
        echo "  ✅ $hook hook 已安装"
    fi
done

echo ""
echo "✅ Git Hooks 安装完成"
echo ""
echo "已安装的 hooks:"
ls -la "$GIT_HOOKS_DIR" | grep -E "pre-commit|commit-msg|post-commit|pre-push" || true
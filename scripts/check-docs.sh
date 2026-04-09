#!/bin/bash
# 手动检查文档同步状态
# 用法: ./scripts/check-docs.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/sync-docs.sh"
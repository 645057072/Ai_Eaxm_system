#!/bin/bash
# 在 ECS 本机执行：等同于 remote-deploy.sh（保留此文件名便于文档引用）
set -euo pipefail

export DEPLOY_ROOT="${DEPLOY_ROOT:-/opt/exam-system}"
export BRANCH="${BRANCH:-main}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec bash "$SCRIPT_DIR/remote-deploy.sh"

#!/bin/bash
# 在 ECS（47.93.44.247）上部署本仓库：进入目录、加载环境变量、构建并启动
set -euo pipefail

DEPLOY_ROOT="${DEPLOY_ROOT:-/opt/exam-system}"
REPO_URL="${REPO_URL:-}"
BRANCH="${BRANCH:-main}"

cd /
if [[ ! -d "$DEPLOY_ROOT/.git" ]]; then
  echo "目录 $DEPLOY_ROOT 不是 git 仓库。请先: sudo mkdir -p $DEPLOY_ROOT && sudo chown \$USER $DEPLOY_ROOT"
  echo "然后: git clone <你的仓库地址> $DEPLOY_ROOT"
  exit 1
fi

cd "$DEPLOY_ROOT"
git fetch --all --prune
git checkout "$BRANCH"
git pull origin "$BRANCH"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

echo "构建并启动容器..."
docker compose build --no-cache
docker compose up -d

echo "健康检查: curl -s http://127.0.0.1/health"
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1/health || true
echo
echo "浏览器访问: http://47.93.44.247/ （Hash 路由，路径形如 #/login）"

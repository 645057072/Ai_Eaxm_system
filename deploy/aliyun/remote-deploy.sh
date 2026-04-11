#!/bin/bash
# 在 ECS 上执行：同步指定分支代码并 docker compose 构建启动（供本地 SSH 与 GitHub Actions 共用）
set -euo pipefail

DEPLOY_ROOT="${DEPLOY_ROOT:-/opt/exam-system}"
BRANCH="${BRANCH:-main}"

cd "$DEPLOY_ROOT"

if [[ ! -d .git ]]; then
  echo "错误: $DEPLOY_ROOT 不是 git 仓库，请先执行 deploy/aliyun/ecs-first-setup.sh"
  exit 1
fi

echo "[deploy] fetch origin, 分支=$BRANCH"
git fetch origin
git checkout "$BRANCH"
git reset --hard "origin/$BRANCH"

if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

echo "[deploy] docker compose up -d --build"
docker compose up -d --build

echo "[deploy] 健康检查"
if curl -sf http://127.0.0.1/health >/dev/null; then
  echo "OK /health"
else
  echo "警告: /health 未返回 200，请 docker compose logs api web"
  exit 1
fi

echo "[deploy] 完成。访问: http://47.93.44.247/#/login"

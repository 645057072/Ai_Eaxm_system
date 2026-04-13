#!/bin/sh
set -e
cd /app

python scripts/wait_for_db.py

n=0
until alembic upgrade head; do
  n=$((n + 1))
  if [ "$n" -ge 12 ]; then
    echo "alembic 迁移失败"
    exit 1
  fi
  echo "迁移重试 $n ..."
  sleep 3
done

# 种子脚本报错时不阻塞 API 启动（否则会话层 502）；上线后请根据日志补数据
python scripts/seed_data.py || echo "警告: seed_data 执行失败，API 仍将启动，请检查 docker logs api"

exec "$@"

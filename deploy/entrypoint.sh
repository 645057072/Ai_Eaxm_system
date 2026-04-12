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

python scripts/seed_data.py
exec "$@"

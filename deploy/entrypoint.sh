#!/bin/sh
set -e
cd /app
alembic upgrade head
python scripts/seed_data.py
exec "$@"

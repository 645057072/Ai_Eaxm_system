# -*- coding: utf-8 -*-
"""容器启动时等待 MySQL 可连接，减少迁移阶段连接拒绝。"""

import os
import sys
import time

import pymysql
from sqlalchemy.engine.url import make_url


def main() -> int:
    raw = os.environ.get("DATABASE_URL", "")
    if "mysql" not in raw:
        return 0
    try:
        u = make_url(raw)
    except Exception:
        print("无法解析 DATABASE_URL", file=sys.stderr)
        return 1
    host = u.host or "127.0.0.1"
    port = int(u.port or 3306)
    user = u.username or ""
    password = u.password or ""
    for i in range(90):
        try:
            conn = pymysql.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                connect_timeout=3,
            )
            conn.close()
            print(f"数据库已就绪（尝试 {i + 1}）")
            return 0
        except Exception:
            print(f"等待数据库... ({i + 1}/90)")
            time.sleep(2)
    print("等待数据库超时", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-
"""容器启动时等待 MySQL：先等 Docker 内 DNS 能解析主机名，再等端口可连。"""

import os
import socket
import sys
import time

import pymysql
from sqlalchemy.engine.url import make_url


def _is_ip(host: str) -> bool:
    try:
        socket.inet_aton(host.split("%")[0])
        return True
    except OSError:
        return False


def wait_dns(host: str, port: int, attempts: int = 60, interval: float = 2.0) -> bool:
    """非 IP 主机名时等待 getaddrinfo 成功（解决 api 早于 mysql 注册 DNS 的情况）。"""
    if _is_ip(host):
        return True
    for i in range(attempts):
        try:
            socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
            print(f"DNS 已解析 {host!r}（尝试 {i + 1}）")
            return True
        except socket.gaierror as e:
            print(f"等待 DNS：{host!r} ({e}) ({i + 1}/{attempts})")
            time.sleep(interval)
    return False


def main() -> int:
    raw = (os.environ.get("DATABASE_URL") or "").strip()
    if not raw:
        print("未设置 DATABASE_URL，跳过数据库等待", file=sys.stderr)
        return 0
    try:
        u = make_url(raw)
    except Exception:
        print("无法解析 DATABASE_URL", file=sys.stderr)
        return 1
    driver = (u.drivername or "").lower()
    if "mysql" not in driver and "mariadb" not in driver:
        return 0
    host = u.host or "127.0.0.1"
    port = int(u.port or 3306)
    user = u.username or ""
    password = u.password or ""
    if not wait_dns(host, port):
        print(f"无法解析数据库主机 {host!r}（请确认与 mysql 在同一 Docker 网络，或改用 RDS 内网地址）", file=sys.stderr)
        return 1
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
        except Exception as e:
            print(f"等待数据库连接... ({i + 1}/90) {e!s}")
            time.sleep(2)
    print("等待数据库超时", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())

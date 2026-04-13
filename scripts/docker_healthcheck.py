# -*- coding: utf-8 -*-
"""供 Docker Compose healthcheck 调用：带超时，避免 urllib 挂起导致误判 unhealthy。"""

import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def main() -> int:
    # 与数据库连通才算就绪，避免进程已起但登录仍 500（mysql 主机名无法解析等）
    try:
        with urlopen("http://127.0.0.1:8000/health/ready", timeout=10) as resp:
            return 0 if resp.getcode() == 200 else 1
    except (URLError, HTTPError, TimeoutError, OSError):
        return 1


if __name__ == "__main__":
    sys.exit(main())

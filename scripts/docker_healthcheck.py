# -*- coding: utf-8 -*-
"""供 Docker Compose healthcheck 调用：带超时，避免 urllib 挂起导致误判 unhealthy。

说明：进程级就绪用 /health（不访问数据库）。数据库在 entrypoint 中已通过 wait_for_db
与 alembic 验证；若在运行期断库，可人工查看日志或用 curl /health/ready排查。
"""

import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

# 与 uvicorn 监听一致；探活须读完响应体，避免部分环境下连接未正常结束被误判失败
_HEALTH_URL = "http://127.0.0.1:8000/health"
_TIMEOUT_SEC = 8


def main() -> int:
    try:
        with urlopen(_HEALTH_URL, timeout=_TIMEOUT_SEC) as resp:
            code = getattr(resp, "status", None) or resp.getcode()
            _ = resp.read()
            return 0 if int(code) == 200 else 1
    except HTTPError as e:
        print(f"healthcheck HTTP {e.code}: {e.reason}", file=sys.stderr)
        return 1
    except (URLError, TimeoutError, OSError) as e:
        print(f"healthcheck 失败: {e!r}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

# -*- coding: utf-8 -*-

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1 import api_router
from app.core.config import get_cors_origins_list, get_settings

settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug)

# 开发环境 Vite 与生产同域 Nginx 反代均可；全为 * 时不携带 credentials 以符合浏览器规范
_origins = get_cors_origins_list()
_allow_cred = not (len(_origins) == 1 and _origins[0] == "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=_allow_cred,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health() -> dict:
    """负载均衡轻量探活（不访问数据库）。"""
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready() -> dict:
    """就绪探活：确认数据库可连；负载均衡深度探活或排障用（Compose 默认用 /health）。"""
    from app.db.session import engine

    try:
        with engine.begin() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"数据库不可用：{e!s}。请确认 api 与 mysql 在同一 Docker 网络，且 DATABASE_URL 主机名可解析（勿在 .env 中写空的 DATABASE_URL=）。",
        ) from e
    return {"status": "ok", "database": "connected"}

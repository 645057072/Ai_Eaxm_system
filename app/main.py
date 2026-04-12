# -*- coding: utf-8 -*-

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
    """负载均衡健康检查。"""
    return {"status": "ok"}

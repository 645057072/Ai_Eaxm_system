# -*- coding: utf-8 -*-
"""应用配置：从环境变量读取，便于 Docker / 阿里云部署。"""

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors_origins_env(value: str) -> List[str]:
    """将 CORS 环境变量转为列表。必须用字符串字段接收，避免 Pydantic Settings 对 List 型环境变量走 JSON 解析（逗号 URL 不是合法 JSON，会触发 json.decoder 异常导致进程起不来）。"""
    s = value.strip()
    if not s:
        return ["*"]
    if s == "*":
        return ["*"]
    return [x.strip() for x in s.split(",") if x.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "考试系统 API"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    # 跨域：逗号分隔 URL；环境变量 CORS_ORIGINS（勿用 List 字段，见 parse_cors_origins_env 说明）
    cors_origins: str = "*"

    # MySQL（阿里云 RDS）；环境变量 DATABASE_URL（勿在 .env 写 DATABASE_URL= 空行，否则会覆盖默认值）
    database_url: str = "mysql+pymysql://exam:exam@127.0.0.1:3306/exam_db?charset=utf8mb4"

    @field_validator("database_url", mode="before")
    @classmethod
    def _database_url_non_empty(cls, v: object) -> object:
        if v is None or (isinstance(v, str) and not v.strip()):
            return "mysql+pymysql://exam:exam@127.0.0.1:3306/exam_db?charset=utf8mb4"
        return v

    # JWT；环境变量 SECRET_KEY
    secret_key: str = "change-me-in-production-use-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # Redis（会话、限流、Celery broker 预留）；环境变量 REDIS_URL
    redis_url: str = "redis://127.0.0.1:6379/0"

    # 营业执照等附件存储目录（相对工作目录）；环境变量 UPLOAD_ROOT
    upload_root: str = "uploads"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_cors_origins_list() -> List[str]:
    return parse_cors_origins_env(get_settings().cors_origins)

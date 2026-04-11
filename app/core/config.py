# -*- coding: utf-8 -*-
"""应用配置：从环境变量读取，便于 Docker / 阿里云部署。"""

from functools import lru_cache
from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "考试系统 API"
    api_v1_prefix: str = "/api/v1"
    debug: bool = False

    # 跨域：逗号分隔，如 http://47.93.44.247,http://localhost:5173；环境变量 CORS_ORIGINS
    cors_origins: List[str] = ["*"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def split_cors(cls, v: object) -> List[str]:
        if v is None or v == "":
            return ["*"]
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        s = str(v).strip()
        if s == "*":
            return ["*"]
        return [x.strip() for x in s.split(",") if x.strip()]

    # MySQL（阿里云 RDS）；环境变量 DATABASE_URL
    database_url: str = "mysql+pymysql://exam:exam@127.0.0.1:3306/exam_db?charset=utf8mb4"

    # JWT；环境变量 SECRET_KEY
    secret_key: str = "change-me-in-production-use-long-random-string"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    # Redis（会话、限流、Celery broker 预留）；环境变量 REDIS_URL
    redis_url: str = "redis://127.0.0.1:6379/0"


@lru_cache
def get_settings() -> Settings:
    return Settings()

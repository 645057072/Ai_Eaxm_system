# -*- coding: utf-8 -*-
"""数据库会话工厂。"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()
# PyMySQL 默认连接可能长时间挂起，探活/请求易超时；仅对 MySQL 连接串附加 connect_timeout
_url = (settings.database_url or "").lower()
_connect_args: dict = {}
if "mysql" in _url or "mariadb" in _url or "pymysql" in _url:
    _connect_args["connect_timeout"] = 10

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.debug,
    connect_args=_connect_args,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

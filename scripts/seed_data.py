# -*- coding: utf-8 -*-
"""初始化角色与默认管理员（仅脚本执行一次）。"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import Role, User


def main() -> None:
    db = SessionLocal()
    try:
        roles_spec = [
            ("管理员", "admin", "系统管理、用户管理"),
            ("教师", "teacher", "题库、试卷、考试发布"),
            ("考生", "student", "参加考试"),
        ]
        for name, code, desc in roles_spec:
            if not db.scalars(select(Role).where(Role.code == code)).first():
                db.add(Role(name=name, code=code, description=desc))
        db.commit()

        admin_role = db.scalars(select(Role).where(Role.code == "admin")).first()
        if admin_role is None:
            raise RuntimeError("admin 角色未创建")

        def ensure_user(username: str, pwd: str, full_name: str, role_code: str) -> None:
            if db.scalars(select(User).where(User.username == username)).first():
                return
            role = db.scalars(select(Role).where(Role.code == role_code)).first()
            if role is None:
                return
            db.add(
                User(
                    username=username,
                    password_hash=hash_password(pwd),
                    full_name=full_name,
                    role_id=role.id,
                )
            )
            db.commit()
            print(f"已创建用户: {username} / {pwd}（角色 {role_code}）")

        ensure_user("admin", "Admin@123456", "系统管理员", "admin")
        ensure_user("teacher", "Teacher@123456", "演示教师", "teacher")
        ensure_user("student", "Student@123456", "演示考生", "student")
    finally:
        db.close()


if __name__ == "__main__":
    main()

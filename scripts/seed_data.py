# -*- coding: utf-8 -*-
"""初始化企业、角色、功能授权与默认账号（可重复执行：仅补缺）。"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import func, select

from app.core.permission_catalog import ALL_CODES
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.enterprise import Enterprise
from app.models.permission import RolePermission
from app.models.user import Role, User

# 教师：考试业务全权限
TEACHER_PERMISSIONS = [
    "menu.home",
    "menu.exam.qb_center",
    "menu.exam.question_manage",
    "menu.exam.paper_manage",
    "menu.exam.paper_publish",
    "menu.system.paper_level",
    "list.paper_level",
    "action.paper_level.manage",
    "menu.exam.sessions",
    "list.question",
    "list.paper",
    "list.session",
    "list.attempt",
    "list.course",
    "list.enterprise",
    "action.question.manage",
    "action.question.import",
    "action.question.batch",
    "action.paper.manage",
    "action.session.manage",
]

# 考生：参加考试
STUDENT_PERMISSIONS = [
    "menu.home",
    "menu.exam.available",
    "action.exam.take",
]


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

        ent = db.scalars(select(Enterprise).order_by(Enterprise.id.asc())).first()
        if ent is None:
            db.add(
                Enterprise(
                    name="默认企业",
                    tax_id="DEFAULT000000000000000",
                    license_file_path=None,
                    address_phone=None,
                    contact_person=None,
                    industry=None,
                )
            )
            db.commit()
            ent = db.scalars(select(Enterprise).order_by(Enterprise.id.asc())).first()
        eid = ent.id

        def ensure_role_permissions() -> None:
            n = db.scalar(select(func.count()).select_from(RolePermission)) or 0
            if n > 0:
                return
            admin = db.scalars(select(Role).where(Role.code == "admin")).first()
            teacher = db.scalars(select(Role).where(Role.code == "teacher")).first()
            student = db.scalars(select(Role).where(Role.code == "student")).first()
            if admin:
                for c in ALL_CODES:
                    db.add(RolePermission(role_id=admin.id, permission_code=c))
            if teacher:
                for c in TEACHER_PERMISSIONS:
                    db.add(RolePermission(role_id=teacher.id, permission_code=c))
            if student:
                for c in STUDENT_PERMISSIONS:
                    db.add(RolePermission(role_id=student.id, permission_code=c))
            db.commit()
            print("已写入内置角色功能授权")

        ensure_role_permissions()

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
                    enterprise_id=eid,
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

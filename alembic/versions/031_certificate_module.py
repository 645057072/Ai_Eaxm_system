# -*- coding: utf-8 -*-
"""证书管理：模板与颁发记录。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.db.migrate_compat import has_index, has_table, safe_create_index

revision: str = "031"
down_revision: Union[str, None] = "030"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    if not has_table("exam_cert_template"):
        op.create_table(
            "exam_cert_template",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("enterprise_id", sa.Integer(), nullable=False, comment="所属企业"),
            sa.Column("cert_code", sa.String(length=64), nullable=False, comment="模板编码（企业内唯一）"),
            sa.Column("name", sa.String(length=200), nullable=False, server_default="", comment="模板名称"),
            sa.Column("course_id", sa.Integer(), nullable=True, comment="关联课程；空表示全课程通用"),
            sa.Column("layout_json", sa.JSON(), nullable=False),
            sa.Column("status", sa.String(length=16), nullable=False, server_default="draft", comment="draft|published"),
            sa.Column("created_by", sa.Integer(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["course_id"], ["sys_course.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["created_by"], ["sys_user.id"]),
            sa.ForeignKeyConstraint(["enterprise_id"], ["sys_enterprise.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("enterprise_id", "cert_code", name="uq_cert_template_ent_code"),
        )
    safe_create_index("ix_exam_cert_template_enterprise_id", "exam_cert_template", ["enterprise_id"])
    safe_create_index("ix_exam_cert_template_course_id", "exam_cert_template", ["course_id"])
    safe_create_index("ix_exam_cert_template_status", "exam_cert_template", ["status"])

    if not has_table("exam_cert_record"):
        op.create_table(
            "exam_cert_record",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("enterprise_id", sa.Integer(), nullable=False),
            sa.Column("cert_template_id", sa.Integer(), nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False, comment="获证人"),
            sa.Column("exam_service_record_id", sa.Integer(), nullable=False),
            sa.Column("certificate_no", sa.String(length=64), nullable=False, comment="证书编号（全局唯一）"),
            sa.Column("student_display", sa.String(length=200), nullable=False, server_default=""),
            sa.Column("course_name", sa.String(length=200), nullable=False, server_default=""),
            sa.Column("paper_title", sa.String(length=200), nullable=False, server_default=""),
            sa.Column("score", sa.Numeric(10, 2), nullable=True),
            sa.Column("passed", sa.Boolean(), nullable=True),
            sa.Column("issued_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("issued_by", sa.Integer(), nullable=True, comment="颁发人"),
            sa.ForeignKeyConstraint(["cert_template_id"], ["exam_cert_template.id"], ondelete="RESTRICT"),
            sa.ForeignKeyConstraint(["enterprise_id"], ["sys_enterprise.id"]),
            sa.ForeignKeyConstraint(["exam_service_record_id"], ["exam_service_record.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["issued_by"], ["sys_user.id"]),
            sa.ForeignKeyConstraint(["user_id"], ["sys_user.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("certificate_no", name="uq_cert_record_no"),
            sa.UniqueConstraint("exam_service_record_id", "cert_template_id", name="uq_cert_record_svc_tpl"),
        )
    safe_create_index("ix_exam_cert_record_enterprise_id", "exam_cert_record", ["enterprise_id"])
    safe_create_index("ix_exam_cert_record_cert_template_id", "exam_cert_record", ["cert_template_id"])
    safe_create_index("ix_exam_cert_record_user_id", "exam_cert_record", ["user_id"])
    safe_create_index("ix_exam_cert_record_exam_service_record_id", "exam_cert_record", ["exam_service_record_id"])


def downgrade() -> None:
    if has_table("exam_cert_record"):
        if has_index("exam_cert_record", "ix_exam_cert_record_exam_service_record_id"):
            op.drop_index("ix_exam_cert_record_exam_service_record_id", table_name="exam_cert_record")
        if has_index("exam_cert_record", "ix_exam_cert_record_user_id"):
            op.drop_index("ix_exam_cert_record_user_id", table_name="exam_cert_record")
        if has_index("exam_cert_record", "ix_exam_cert_record_cert_template_id"):
            op.drop_index("ix_exam_cert_record_cert_template_id", table_name="exam_cert_record")
        if has_index("exam_cert_record", "ix_exam_cert_record_enterprise_id"):
            op.drop_index("ix_exam_cert_record_enterprise_id", table_name="exam_cert_record")
        op.drop_table("exam_cert_record")
    if has_table("exam_cert_template"):
        if has_index("exam_cert_template", "ix_exam_cert_template_status"):
            op.drop_index("ix_exam_cert_template_status", table_name="exam_cert_template")
        if has_index("exam_cert_template", "ix_exam_cert_template_course_id"):
            op.drop_index("ix_exam_cert_template_course_id", table_name="exam_cert_template")
        if has_index("exam_cert_template", "ix_exam_cert_template_enterprise_id"):
            op.drop_index("ix_exam_cert_template_enterprise_id", table_name="exam_cert_template")
        op.drop_table("exam_cert_template")

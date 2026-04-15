# -*- coding: utf-8 -*-
"""考试场次：场次编码、所属企业、关联课程。"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text

revision: str = "016"
down_revision: Union[str, None] = "015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, col: str) -> bool:
    bind = op.get_bind()
    insp = inspect(bind)
    cols = insp.get_columns(table)
    return any((c.get("name") == col) for c in cols)


def upgrade() -> None:
    if not _has_column("exam_session", "session_code"):
        op.add_column(
            "exam_session",
            sa.Column("session_code", sa.String(length=64), nullable=True, comment="场次编码"),
        )
    if not _has_column("exam_session", "enterprise_id"):
        op.add_column(
            "exam_session",
            sa.Column("enterprise_id", sa.Integer(), nullable=True, comment="所属企业"),
        )
    if not _has_column("exam_session", "course_id"):
        op.add_column(
            "exam_session",
            sa.Column("course_id", sa.Integer(), nullable=True, comment="关联课程"),
        )

    bind = op.get_bind()
    bind.execute(
        text(
            """
            UPDATE exam_session es
            INNER JOIN exam_paper p ON es.paper_id = p.id
            LEFT JOIN sys_course c ON p.course_id = c.id
            LEFT JOIN sys_user u ON p.created_by = u.id
            SET es.course_id = p.course_id,
                es.enterprise_id = COALESCE(c.enterprise_id, u.enterprise_id)
            """
        )
    )
    bind.execute(
        text(
            "UPDATE exam_session SET session_code = CONCAT('S', LPAD(id, 6, '0')) "
            "WHERE session_code IS NULL OR session_code = ''"
        )
    )
    bind.execute(
        text(
            "UPDATE exam_session SET enterprise_id = (SELECT id FROM sys_enterprise ORDER BY id ASC LIMIT 1) "
            "WHERE enterprise_id IS NULL"
        )
    )
    bind.execute(
        text(
            """
            UPDATE exam_session es
            INNER JOIN (
                SELECT enterprise_id, MIN(id) AS cid FROM sys_course GROUP BY enterprise_id
            ) x ON es.enterprise_id = x.enterprise_id
            SET es.course_id = x.cid
            WHERE es.course_id IS NULL
            """
        )
    )

    op.create_foreign_key(
        "fk_exam_session_enterprise_id",
        "exam_session",
        "sys_enterprise",
        ["enterprise_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_exam_session_course_id",
        "exam_session",
        "sys_course",
        ["course_id"],
        ["id"],
    )
    op.create_index("ix_exam_session_enterprise_id", "exam_session", ["enterprise_id"], unique=False)
    op.create_index("ix_exam_session_course_id", "exam_session", ["course_id"], unique=False)
    op.create_index("uq_exam_session_session_code", "exam_session", ["session_code"], unique=True)

    op.alter_column(
        "exam_session",
        "session_code",
        existing_type=sa.String(length=64),
        nullable=False,
        existing_comment="场次编码",
    )
    op.alter_column(
        "exam_session",
        "enterprise_id",
        existing_type=sa.Integer(),
        nullable=False,
        existing_comment="所属企业",
    )


def downgrade() -> None:
    op.drop_index("uq_exam_session_session_code", table_name="exam_session")
    op.drop_index("ix_exam_session_course_id", table_name="exam_session")
    op.drop_index("ix_exam_session_enterprise_id", table_name="exam_session")
    op.drop_constraint("fk_exam_session_course_id", "exam_session", type_="foreignkey")
    op.drop_constraint("fk_exam_session_enterprise_id", "exam_session", type_="foreignkey")
    op.drop_column("exam_session", "course_id")
    op.drop_column("exam_session", "enterprise_id")
    op.drop_column("exam_session", "session_code")

# -*- coding: utf-8 -*-
"""导出全部模型供 Alembic 与业务引用。"""

from app.models.course import Course
from app.models.enterprise import Enterprise
from app.models.exam import ExamAttempt, ExamAnswer, ExamPaper, ExamPaperItem, ExamSession
from app.models.exam_candidate import ExamCandidate
from app.models.exam_service_record import ExamServiceRecord
from app.models.exam_wrong_question import ExamWrongQuestion
from app.models.certificate import CertRecord, CertTemplate
from app.models.paper_level import PaperLevel
from app.models.print_template import PrintTemplate
from app.models.permission import RolePermission
from app.models.question import Question
from app.models.student import Student
from app.models.user import Role, User

__all__ = [
    "Course",
    "Enterprise",
    "PaperLevel",
    "PrintTemplate",
    "RolePermission",
    "Role",
    "User",
    "Question",
    "ExamPaper",
    "ExamPaperItem",
    "ExamSession",
    "ExamAttempt",
    "ExamAnswer",
    "Student",
    "ExamCandidate",
    "ExamServiceRecord",
    "ExamWrongQuestion",
    "CertTemplate",
    "CertRecord",
]

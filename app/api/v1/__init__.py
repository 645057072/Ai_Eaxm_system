# -*- coding: utf-8 -*-

from fastapi import APIRouter

from app.api.v1 import auth, users, roles, questions, papers, paper_levels, exam_sessions, attempts, enterprises, files, permissions, courses

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(permissions.router, prefix="/permissions", tags=["权限"])
api_router.include_router(roles.router, prefix="/roles", tags=["角色"])
api_router.include_router(enterprises.router, prefix="/enterprises", tags=["企业信息"])
api_router.include_router(courses.router, prefix="/courses", tags=["课程信息"])
api_router.include_router(files.router, prefix="/files", tags=["附件"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(questions.router, prefix="/questions", tags=["题库"])
api_router.include_router(papers.router, prefix="/papers", tags=["试卷"])
api_router.include_router(paper_levels.router, prefix="/paper-levels", tags=["试卷等级"])
api_router.include_router(exam_sessions.router, prefix="/exam-sessions", tags=["考试场次"])
api_router.include_router(attempts.router, tags=["考试作答"])

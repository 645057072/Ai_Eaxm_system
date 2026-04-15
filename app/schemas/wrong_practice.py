# -*- coding: utf-8 -*-

from typing import Any, Optional

from pydantic import BaseModel, Field


class WrongCourseRow(BaseModel):
    course_id: int
    course_name: str = "—"
    enterprise_id: int
    enterprise_name: str = "—"
    wrong_count: int = Field(0, ge=0)


class WrongQuestionOut(BaseModel):
    course_id: int
    question_id: int
    q_type: str
    stem: str
    options_json: Optional[Any] = None
    remaining: int = Field(0, ge=0)


class WrongAnswerIn(BaseModel):
    question_id: int
    user_answer_json: Any = None


class WrongAnswerResultOut(BaseModel):
    question_id: int
    correct: bool
    std_answer_json: Any = None
    analysis: Optional[str] = None
    removed_from_wrong_set: bool = False
    remaining: int = Field(0, ge=0)


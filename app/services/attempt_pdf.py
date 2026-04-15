# -*- coding: utf-8 -*-
"""考生答卷 PDF（管理端查看）：题干、选项、作答、得分与标准答案。"""

import json
import os
from decimal import Decimal
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.exam import ExamAnswer, ExamAttempt, ExamPaperItem, ExamSession
from app.services.practice_report import q_type_label_cn


def _register_zh_font() -> str:
    """注册中文字体；无可用字体时退回 Helvetica（中文可能无法显示，可配置环境变量 EXAM_PDF_FONT_TTF）。"""
    for p in (
        os.environ.get("EXAM_PDF_FONT_TTF"),
        os.environ.get("EXAM_PDF_FONT_TTC"),
        r"C:\Windows\Fonts\simsun.ttc",
        r"C:\Windows\Fonts\msyh.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ):
        if not p or not os.path.isfile(p):
            continue
        try:
            if p.lower().endswith(".ttc"):
                pdfmetrics.registerFont(TTFont("ZhExam", p, subfontIndex=0))
            else:
                pdfmetrics.registerFont(TTFont("ZhExam", p))
            return "ZhExam"
        except OSError:
            continue
    return "Helvetica"


def _p(text: str, style: ParagraphStyle) -> Paragraph:
    raw = text or ""
    safe = escape(raw).replace("\n", "<br/>")
    return Paragraph(safe, style)


def build_attempt_pdf_bytes(db: Session, attempt_id: int) -> bytes:
    att = db.scalars(
        select(ExamAttempt)
        .options(
            joinedload(ExamAttempt.session).joinedload(ExamSession.paper),
            joinedload(ExamAttempt.user),
        )
        .where(ExamAttempt.id == attempt_id)
    ).first()
    if att is None:
        raise ValueError("作答不存在")

    buf = BytesIO()
    font_name = _register_zh_font()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    base = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PdfTitle",
        parent=base["Title"],
        fontName=font_name,
        fontSize=16,
        leading=22,
        spaceAfter=12,
    )
    h2_style = ParagraphStyle(
        "PdfH2",
        parent=base["Heading2"],
        fontName=font_name,
        fontSize=12,
        leading=16,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "PdfBody",
        parent=base["Normal"],
        fontName=font_name,
        fontSize=10,
        leading=14,
    )

    story: list = []
    story.append(_p("考生答卷明细", title_style))
    sess = att.session
    paper = sess.paper if sess else None
    u = att.user
    story.append(_p(f"场次：{sess.title if sess else ''}", body_style))
    story.append(_p(f"试卷：{paper.title if paper else ''}", body_style))
    uname = u.username if u else ""
    fname = u.full_name if u else ""
    story.append(_p(f"考生用户：{uname} {fname or ''}", body_style))
    ts = str(att.total_score) if att.total_score is not None else "—"
    story.append(_p(f"状态：{att.status}  总分：{ts}", body_style))
    story.append(Spacer(1, 12))

    if paper is None:
        doc.build(story)
        return buf.getvalue()

    items = db.scalars(
        select(ExamPaperItem)
        .options(joinedload(ExamPaperItem.question))
        .where(ExamPaperItem.paper_id == paper.id)
    ).all()
    items = sorted(items, key=lambda x: (x.sort_order, x.id))
    ans_list = db.scalars(select(ExamAnswer).where(ExamAnswer.attempt_id == attempt_id)).all()
    ans_map = {a.question_id: a for a in ans_list}

    for n, it in enumerate(items, start=1):
        q = it.question
        if q is None:
            continue
        ea = ans_map.get(it.question_id)
        ua = ea.user_answer_json if ea else None
        sc: Decimal | str = ea.score_awarded if ea and ea.score_awarded is not None else Decimal("0")
        qt = q_type_label_cn(q.q_type)
        story.append(_p(f"第 {n} 题（{qt}，满分 {it.score}）", h2_style))
        story.append(_p(q.stem or "", body_style))
        opts_raw = q.options_json
        if isinstance(opts_raw, list):
            lines_o: list[str] = []
            for o in opts_raw:
                if isinstance(o, dict):
                    k = o.get("key", "")
                    t = o.get("text", "")
                    lines_o.append(f"{k}. {t}")
            if lines_o:
                story.append(_p("选项：" + "；".join(lines_o), body_style))
        ua_txt = json.dumps(ua, ensure_ascii=False) if ua is not None else "（未答）"
        story.append(_p(f"考生作答：{ua_txt}", body_style))
        story.append(_p(f"得分：{sc}", body_style))
        story.append(_p(f"标准答案：{json.dumps(q.answer_json, ensure_ascii=False)}", body_style))
        if q.analysis:
            story.append(_p(f"解析：{q.analysis}", body_style))
        story.append(Spacer(1, 10))

    doc.build(story)
    return buf.getvalue()

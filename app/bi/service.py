# -*- coding: utf-8 -*-
"""大屏数据聚合：企业树范围、IP 省份解析、图表用序列。"""

from __future__ import annotations

import ipaddress
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.enterprise import Enterprise
from app.models.exam import ExamAttempt, ExamSession
from app.models.exam_service_record import ExamServiceRecord
from app.services.data_scope import collect_descendant_enterprise_ids

# 单次大屏请求最多解析的独立 IP 数量（避免刷新过慢）
_MAX_IP_LOOKUP = 120

_SCORE_BINS = ("0-59", "60-69", "70-79", "80-89", "90-100")


def _score_bin(score: Decimal | float | int | None) -> str | None:
    if score is None:
        return None
    try:
        v = float(score)
    except (TypeError, ValueError):
        return None
    if v < 60:
        return _SCORE_BINS[0]
    if v < 70:
        return _SCORE_BINS[1]
    if v < 80:
        return _SCORE_BINS[2]
    if v < 90:
        return _SCORE_BINS[3]
    return _SCORE_BINS[4]


def _normalize_province_label(pro: str) -> str:
    """将接口返回的省级行政区名称规范为与 ECharts 中国地图一致的简称。"""
    p = pro.strip()
    if not p:
        return ""
    # 先匹配较长后缀，避免「市」误伤自治区
    for suf in (
        "壮族自治区",
        "维吾尔自治区",
        "回族自治区",
        "特别行政区",
        "自治区",
        "省",
        "市",
    ):
        if p.endswith(suf):
            p = p[: -len(suf)]
            break
    return p


def _ip_kind(ip: str) -> str:
    """返回 private / loopback / public / invalid。"""
    try:
        addr = ipaddress.ip_address(ip.strip())
    except ValueError:
        return "invalid"
    if addr.is_loopback:
        return "loopback"
    if addr.is_private:
        return "private"
    return "public"


def resolve_ip_province(ip: str, cache: dict[str, str], client: httpx.Client) -> str:
    """公网 IP 调用在线库解析省级行政区；内网归并为「内网」。"""
    ip = ip.strip()
    if not ip:
        return ""
    if ip in cache:
        return cache[ip]
    kind = _ip_kind(ip)
    if kind in ("private", "loopback"):
        cache[ip] = "内网"
        return cache[ip]
    if kind == "invalid":
        cache[ip] = ""
        return ""
    url = f"https://whois.pconline.com.cn/ipJson.jsp?ip={ip}&json=true"
    r = client.get(url, timeout=5.0)
    r.encoding = r.apparent_encoding or "gbk"
    data = r.json()
    pro = ""
    if isinstance(data, dict):
        pro = str(data.get("pro") or "")
    short = _normalize_province_label(pro)
    cache[ip] = short
    return short


def get_default_enterprise_id(db: Session) -> int | None:
    """未传 enterprise_id 时取一条顶级企业作为默认展示范围。"""
    row = db.scalars(select(Enterprise.id).where(Enterprise.parent_id.is_(None)).order_by(Enterprise.id).limit(1)).first()
    return int(row) if row is not None else None


def get_enterprise_banner_name(db: Session, enterprise_id: int) -> str:
    row = db.get(Enterprise, enterprise_id)
    return row.name if row is not None else "未知企业"


def build_dashboard_payload(db: Session, root_enterprise_id: int) -> dict[str, Any]:
    """生成大屏 JSON：含5 组图表所需数据结构。"""
    ent_ids = collect_descendant_enterprise_ids(db, root_enterprise_id)
    ent_list = list(ent_ids)

    banner = get_enterprise_banner_name(db, root_enterprise_id)
    title_text = f"{banner}考试服务数智中心"

    course_cnt = (
        db.scalar(select(func.count()).select_from(Course).where(Course.enterprise_id.in_(ent_list))) or 0
    )

    # 按客户端 IP 聚合人次，取访问量最高的若干 IP 做地域解析（控制外呼次数）
    ip_counts_rows = db.execute(
        select(ExamAttempt.client_ip, func.count().label("cnt"))
        .join(ExamSession, ExamSession.id == ExamAttempt.session_id)
        .where(
            ExamSession.enterprise_id.in_(ent_list),
            ExamAttempt.client_ip.is_not(None),
            ExamAttempt.client_ip != "",
        )
        .group_by(ExamAttempt.client_ip)
        .order_by(func.count().desc())
        .limit(_MAX_IP_LOOKUP)
    ).all()

    province_counts: dict[str, int] = defaultdict(int)
    intranet_hits = 0
    ip_cache: dict[str, str] = {}
    with httpx.Client(headers={"User-Agent": "AiExam-BI/1.0"}) as hclient:
        for ip, row_cnt in ip_counts_rows:
            ip_s = str(ip).strip()
            if not ip_s:
                continue
            cnt = int(row_cnt or 0)
            prov = resolve_ip_province(ip_s, ip_cache, hclient)
            if prov == "内网":
                intranet_hits += cnt
                continue
            if not prov:
                continue
            province_counts[prov] += cnt

    map_data = [{"name": k, "value": v} for k, v in sorted(province_counts.items(), key=lambda x: -x[1])]

    # 近 7 日每日 distinct参考人数
    today = datetime.now(timezone.utc).date()
    start_d = today - timedelta(days=6)
    daily_labels: list[str] = []
    daily_counts: list[int] = []
    for i in range(7):
        d = start_d + timedelta(days=i)
        daily_labels.append(d.strftime("%m-%d"))
        c = (
            db.scalar(
                select(func.count(func.distinct(ExamAttempt.user_id)))
                .select_from(ExamAttempt)
                .join(ExamSession, ExamSession.id == ExamAttempt.session_id)
                .where(
                    ExamSession.enterprise_id.in_(ent_list),
                    func.date(ExamAttempt.started_at) == d,
                )
            )
            or 0
        )
        daily_counts.append(int(c))

    total_distinct_examinees = (
        db.scalar(
            select(func.count(func.distinct(ExamAttempt.user_id)))
            .select_from(ExamAttempt)
            .join(ExamSession, ExamSession.id == ExamAttempt.session_id)
            .where(ExamSession.enterprise_id.in_(ent_list))
        )
        or 0
    )

    # 课程维度：分数段人数（取记录数最多的前 4 门课，避免系列过多）
    course_names_rows = db.execute(
        select(ExamServiceRecord.course_name, func.count().label("cnt"))
        .where(ExamServiceRecord.enterprise_id.in_(ent_list))
        .group_by(ExamServiceRecord.course_name)
        .order_by(func.count().desc())
        .limit(4)
    ).all()
    top_courses = [str(r[0]) for r in course_names_rows if r[0]]

    course_score_matrix: dict[str, list[int]] = {c: [0] * len(_SCORE_BINS) for c in top_courses}
    if top_courses:
        recs = db.execute(
            select(ExamServiceRecord.course_name, ExamServiceRecord.score).where(
                ExamServiceRecord.enterprise_id.in_(ent_list),
                ExamServiceRecord.course_name.in_(top_courses),
            )
        ).all()
        for row in recs:
            cn = row[0]
            sc = row[1]
            b = _score_bin(sc)
            if cn not in course_score_matrix or b is None:
                continue
            idx = _SCORE_BINS.index(b)
            course_score_matrix[cn][idx] += 1

    # 学员整体分数段（全部服务记录）
    student_bins = [0] * len(_SCORE_BINS)
    scores = db.scalars(select(ExamServiceRecord.score).where(ExamServiceRecord.enterprise_id.in_(ent_list))).all()
    for sc in scores:
        b = _score_bin(sc)
        if b is None:
            continue
        student_bins[_SCORE_BINS.index(b)] += 1

    gauge_max = max(int(course_cnt * 1.2) + 10, 50)

    return {
        "title": title_text,
        "courseTotal": int(course_cnt),
        "gaugeMax": gauge_max,
        "mapData": map_data,
        "intranetHits": intranet_hits,
        "dailyLabels": daily_labels,
        "dailyOnline": daily_counts,
        "totalDistinctExaminees": int(total_distinct_examinees),
        "scoreBins": list(_SCORE_BINS),
        "courseScoreCourses": top_courses,
        "courseScoreSeries": [{"name": c, "data": course_score_matrix[c]} for c in top_courses],
        "studentScoreData": student_bins,
    }

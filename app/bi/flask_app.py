# -*- coding: utf-8 -*-
"""Flask：数智 BI 可视化大屏入口。"""

from pathlib import Path

from flask import Flask, jsonify, render_template, request

from app.bi.service import build_dashboard_payload, get_default_enterprise_id
from app.db.session import SessionLocal

_PKG_DIR = Path(__file__).resolve().parent


def create_app() -> Flask:
    # 静态资源挂在 /bi/static，便于与 Nginx location ^~ /bi/ 一并反代，避免与前端根路径 /static 冲突
    app = Flask(
        __name__,
        template_folder=str(_PKG_DIR / "templates"),
        static_folder=str(_PKG_DIR / "static"),
        static_url_path="/bi/static",
    )

    @app.get("/bi/screen")
    def bi_screen():
        # 大屏页面：查询参数 enterprise_id 指定根企业（含下级），由前端请求 /bi/api/data 时传入
        return render_template("bi_screen.html")

    @app.get("/bi/api/data")
    def bi_api_data():
        db = SessionLocal()
        try:
            eid = request.args.get("enterprise_id", type=int)
            if eid is None:
                eid = get_default_enterprise_id(db)
            if eid is None:
                return jsonify({"error": "无企业数据，请先创建企业"}), 400
            try:
                payload = build_dashboard_payload(db, eid)
                return jsonify(payload)
            except Exception as e:
                # 统一返回 JSON，避免前端 res.json() 解析 HTML 500 失败后误判为地图加载失败
                return jsonify({"error": f"数据接口异常：{e!s}"}), 500
        finally:
            db.close()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 国内/ECS 构建时默认使用镜像源，避免访问 files.pythonhosted.org 被断开导致 pip 失败
# 可在构建时覆盖：docker compose build --build-arg PIP_INDEX_URL=... --build-arg PIP_TRUSTED_HOST=...
ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    -i "${PIP_INDEX_URL}" --trusted-host "${PIP_TRUSTED_HOST}" \
    && pip install --no-cache-dir -r requirements.txt \
    -i "${PIP_INDEX_URL}" --trusted-host "${PIP_TRUSTED_HOST}" \
    --timeout 300 --retries 15

COPY alembic.ini alembic.ini
COPY alembic alembic
COPY app app
COPY scripts scripts
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

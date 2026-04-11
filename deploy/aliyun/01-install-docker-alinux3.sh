#!/bin/bash
# Alibaba Cloud Linux 3.2104 LTS 64 位：安装 Docker 引擎与 Compose 插件
set -euo pipefail

echo "[1/3] 安装 Docker..."
if command -v docker >/dev/null 2>&1; then
  echo "Docker 已安装: $(docker --version)"
else
  sudo dnf -y install docker
  sudo systemctl enable --now docker
  sudo usermod -aG docker "${USER}" || true
  echo "Docker 安装完成。若需无 sudo 使用 docker，请重新登录 SSH。"
fi

echo "[2/3] 安装 Docker Compose 插件..."
if docker compose version >/dev/null 2>&1; then
  echo "docker compose 已可用: $(docker compose version)"
else
  if sudo dnf -y install docker-compose-plugin 2>/dev/null; then
    echo "已通过 dnf 安装 docker-compose-plugin"
  else
    echo "请手动安装 compose 插件，或使用独立 docker-compose 二进制。"
    exit 1
  fi
fi

echo "[3/3] 放行防火墙 HTTP（可选）..."
if sudo firewall-cmd --state >/dev/null 2>&1; then
  sudo firewall-cmd --permanent --add-service=http || true
  sudo firewall-cmd --reload || true
fi

echo "完成。请重新登录后再执行 docker ps 验证。"

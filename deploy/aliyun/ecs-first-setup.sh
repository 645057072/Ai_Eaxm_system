#!/bin/bash
# 阿里云 ECS 首次准备：Git、Docker、克隆仓库、生成 .env
# 用法一（推荐）：本机已能 ssh 登录 ECS 后执行
#   sudo mkdir -p /opt/exam-system && sudo chown "$USER" /opt/exam-system
#   git clone git@github.com:645057072/Ai_Eaxm_system.git /opt/exam-system
#   cd /opt/exam-system && bash deploy/aliyun/ecs-first-setup.sh
# 用法二：仅上传本脚本到 ECS，并设置 REPO_URL、DEPLOY_ROOT 后执行（将自动 clone）

set -euo pipefail

REPO_URL="${REPO_URL:-git@github.com:645057072/Ai_Eaxm_system.git}"
DEPLOY_ROOT="${DEPLOY_ROOT:-/opt/exam-system}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[1/5] 安装 Git..."
if ! command -v git >/dev/null 2>&1; then
  sudo dnf -y install git 2>/dev/null || sudo yum -y install git
fi

echo "[2/5] 安装 Docker..."
if [[ -f "$SCRIPT_DIR/01-install-docker-alinux3.sh" ]]; then
  bash "$SCRIPT_DIR/01-install-docker-alinux3.sh"
else
  echo "未找到 01-install-docker-alinux3.sh，请手动安装 Docker"
  exit 1
fi

echo "[3/5] 目录 $DEPLOY_ROOT ..."
sudo mkdir -p "$DEPLOY_ROOT"
sudo chown "$(whoami):$(whoami)" "$DEPLOY_ROOT"

echo "[4/5] 克隆仓库（若已存在 .git 则只校正 remote）..."
if [[ ! -d "$DEPLOY_ROOT/.git" ]]; then
  git clone "$REPO_URL" "$DEPLOY_ROOT"
else
  echo "已存在 git 仓库，跳过 clone。"
  cd "$DEPLOY_ROOT"
  git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"
fi

cd "$DEPLOY_ROOT"

echo "[5/5] 环境文件..."
if [[ ! -f .env ]]; then
  if [[ -f deploy/env.aliyun.example ]]; then
    cp deploy/env.aliyun.example .env
    echo "已复制 deploy/env.aliyun.example -> .env，请编辑 SECRET_KEY 等配置。"
  else
    echo "警告: 未找到 deploy/env.aliyun.example，请手动创建 .env"
  fi
else
  echo ".env 已存在，未覆盖。"
fi

echo ""
echo "=== 首次准备完成 ==="
echo "1) 确保 ECS 能通过 SSH 拉取 GitHub：Deploy Key 或账户公钥已配置。"
echo "2) 编辑: $DEPLOY_ROOT/.env"
echo "3) 首次部署: cd $DEPLOY_ROOT && bash deploy/aliyun/remote-deploy.sh"
echo "4) GitHub Actions 仓库 Secrets: ALIYUN_SSH_USER、ALIYUN_SSH_PRIVATE_KEY（见 .github/workflows/deploy-aliyun-ecs.yml）"

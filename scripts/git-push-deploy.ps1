# 推送 main 分支到 GitHub，触发 Actions 自动部署到阿里云 ECS（47.93.44.247）
# 用法: .\scripts\git-push-deploy.ps1
param(
    [string]$Branch = "main"
)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

git push origin $Branch
Write-Host ""
Write-Host "已执行: git push origin $Branch"
Write-Host "请在浏览器打开 Actions 查看部署进度:"
Write-Host "  https://github.com/645057072/Ai_Eaxm_system/actions"

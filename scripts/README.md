# QuantOL Deployment Scripts

## Overview

自动化部署脚本用于管理 QuantOL 应用的开发和生产环境。

## 环境说明

### 开发环境 (Development)
- 后端: `quantol-backend-dev` (端口 8000)
- 前端: `quantol-nextjs-dev` (端口 3000, Next.js dev mode)
- 启动命令: `./scripts/start-dev.sh` 或 `pm2 start quantol-backend-dev quantol-nextjs-dev`

### 生产环境 (Production)
- 后端: `quantol-backend` (端口 8000)
- 前端: `quantol-nextjs` (端口 3000, Next.js start)
- Streamlit: `quantol-streamlit` (端口 8501)
- Nginx: `quantol-nginx` (端口 8087)
- 启动命令: `pm2 start` (使用 ecosystem.config.js 默认环境)

## 脚本列表

### `start-dev.sh` - 启动开发环境
本地开发时使用，自动启动后端和前端（需要先克隆前端仓库）。

### `deploy-backend.sh` - 部署后端
用于 CI/CD 自动部署，从 GitHub 拉取最新代码并重启服务。

### `deploy-frontend.sh` - 部署前端
用于 CI/CD 自动部署，从私有仓库克隆或拉取前端代码，构建后重启。

### `stop.sh` - 停止所有服务
停止所有 PM2 管理的 QuantOL 服务。

### `start.sh` - 启动生产环境
使用 PM2 启动所有生产服务。

## 使用方法

```bash
# 开发
./scripts/start-dev.sh

# 生产
./scripts/stop.sh && ./scripts/start.sh

# 手动部署后端
./scripts/deploy-backend.sh

# 手动部署前端
./scripts/deploy-frontend.sh
```

## 注意事项

1. **前端私有仓库**：首次使用前需要配置 GitHub Personal Access Token
2. **环境变量**：确保 `.env` 文件配置正确
3. **日志管理**：开发环境和生产环境使用不同的日志文件

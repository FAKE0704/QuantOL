# QuantOL Deployment Scripts

## 目录结构

```
scripts/
├── deploy/              # CI/CD 部署脚本
│   ├── deploy-backend.sh    # 部署后端服务
│   └── deploy-frontend.sh   # 部署前端服务（从私有仓库）
├── pm2/                  # PM2 管理脚本
│   ├── start.sh             # 启动生产环境
│   ├── stop.sh              # 停止所有服务
│   ├── restart.sh           # 重启所有服务
│   └── status.sh            # 查看服务状态
├── start-dev.sh         # 本地开发环境启动脚本
└── README.md            # 本文件
```

## 快速开始

### 本地开发
```bash
# 启动开发环境
./scripts/start-dev.sh

# 或手动启动各组件
cd /home/user0704/QuantOL-frontend && npm run dev  # 前端
cd /home/user0704/QuantOL && uv run uvicorn src.main:app --reload  # 后端
```

### 生产部署
```bash
# 启动生产环境
./scripts/pm2/start.sh

# 停止所有服务
./scripts/pm2/stop.sh

# 重启所有服务
./scripts/pm2/restart.sh

# 查看服务状态
./scripts/pm2/status.sh
```

### 手动部署（非 CI/CD）
```bash
# 部署后端
./scripts/deploy/deploy-backend.sh

# 部署前端
./scripts/deploy/deploy-frontend.sh
```

## 环境说明

### 开发环境 (Development)
- 后端: `quantol-backend-dev` (端口 8000)
- 前端: `quantol-nextjs-dev` (端口 3000, Next.js dev mode)

### 生产环境 (Production)
- 后端: `quantol-backend` (端口 8000)
- 前端: `quantol-nextjs` (端口 3000, Next.js start)
- Streamlit: `quantol-streamlit` (端口 8501)
- Nginx: `quantol-nginx` (端口 8087)

## 仓库说明

- **公开仓库** (https://github.com/FAKE0704/QuantOL): 后端、测试、文档
- **私有仓库** (https://github.com/FAKE0704/QuantOL-frontend): 前端代码

## 注意事项

1. 首次使用前需要克隆前端仓库：
   ```bash
   git clone https://github.com/FAKE0704/QuantOL-frontend.git /home/user0704/QuantOL-frontend
   ```

2. 确保 `.env` 文件配置正确

3. 开发环境和生产环境使用不同的日志文件

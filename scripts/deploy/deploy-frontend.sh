#!/bin/bash
set -e

# Configuration
BACKEND_DIR="/home/user0704/QuantOL"
FRONTEND_DIR="/home/user0704/QuantOL-frontend"
REPO_URL="https://github.com/FAKE0704/QuantOL-frontend.git"
# 如果你有 SSH 访问私有仓库的权限，可以用这个：
# REPO_URL="git@github.com:FAKE0704/QuantOL-frontend.git"

echo "🚀 Deploying QuantOL Frontend..."

# Clone or update frontend
if [ -d "$FRONTEND_DIR" ]; then
    echo "📦 Updating existing frontend..."
    cd "$FRONTEND_DIR"
    git pull
else
    echo "📦 Cloning frontend from private repo..."
    git clone "$REPO_URL" "$FRONTEND_DIR"
fi

# Install dependencies and build
cd "$FRONTEND_DIR"
echo "📦 Installing dependencies..."
npm ci

echo "🔨 Building frontend..."
npm run build

# Start or restart Next.js with environment variables
export QUANTOL_BACKEND_PATH="$BACKEND_DIR"
export QUANTOL_FRONTEND_PATH="$FRONTEND_DIR"

cd "$BACKEND_DIR"
if pm2 describe quantol-nextjs >/dev/null 2>&1; then
    echo "🔄 Restarting quantol-nextjs..."
    pm2 restart quantol-nextjs --update-env
else
    echo "🚀 Starting quantol-nextjs..."
    pm2 start ecosystem.config.js --only quantol-nextjs
fi

# Save PM2 process list
pm2 save

echo "✅ Frontend deployed successfully!"
pm2 list

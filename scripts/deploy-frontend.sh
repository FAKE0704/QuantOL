#!/bin/bash
set -e

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

# Restart Next.js with environment
pm2 restart quantol-nextjs --env production

echo "✅ Frontend deployed successfully!"
pm2 list

#!/bin/bash
set -e

# Add uv and npm global binaries to PATH
export PATH="$HOME/.local/bin:$HOME/.npm-global/bin:$HOME/.local/share/npm/bin:$PATH"

echo "🚀 Deploying QuantOL Backend..."

# Pull latest code
git pull origin main

# Install/update dependencies using uv
echo "📦 Syncing dependencies with uv..."
uv sync

# Helper function to start or restart a service
restart_or_start() {
    local app_name=$1
    if pm2 describe "$app_name" >/dev/null 2>&1; then
        echo "🔄 Restarting $app_name..."
        pm2 restart "$app_name"
    else
        echo "🚀 Starting $app_name..."
        pm2 start ecosystem.config.js --only "$app_name"
    fi
}

# Start or restart backend services
restart_or_start quantol-backend
restart_or_start quantol-streamlit

# Nginx may need special handling (requires root)
if pm2 describe quantol-nginx >/dev/null 2>&1; then
    pm2 restart quantol-nginx
else
    echo "⚠️  Nginx not running in PM2. Skip or configure manually."
fi

# Save PM2 process list
pm2 save

echo "✅ Backend deployed successfully!"
pm2 list

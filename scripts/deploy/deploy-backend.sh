#!/bin/bash
set -e

# Add uv to PATH
export PATH="$HOME/.local/bin:$PATH"

# Load nvm and Node.js
export NVM_DIR="$HOME/.nvm"
if [ -s "$NVM_DIR/nvm.sh" ]; then
    source "$NVM_DIR/nvm.sh"
fi

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
        pm2 restart "$app_name" --update-env
    else
        echo "🚀 Starting $app_name..."
        pm2 start ecosystem.config.js --only "$app_name"
    fi
}

# Start or restart backend services
restart_or_start quantol-backend
restart_or_start quantol-streamlit

# Nginx
restart_or_start quantol-nginx

# Save PM2 process list
pm2 save

echo "✅ Backend deployed successfully!"
pm2 list

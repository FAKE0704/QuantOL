#!/bin/bash
set -e

echo "🚀 Deploying QuantOL Backend..."

# Pull latest code
git pull origin main

# Activate virtual environment
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
fi

# Install/update dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Restart services with environment flag
pm2 restart quantol-backend --env production
pm2 restart quantol-streamlit --env production
pm2 restart quantol-nginx --env production

echo "✅ Backend deployed successfully!"
pm2 list

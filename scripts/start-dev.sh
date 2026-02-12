#!/bin/bash
set -e

echo "🔧 Starting QuantOL Development Environment..."

# Start backend (from public repo)
echo "📦 Starting backend..."
cd /home/user0704/QuantOL
if [ -f .venv/bin/activate ]; then
    source .venv/bin/activate
fi
uv run uvicorn src.main:app --reload --port 8000 &

# Start frontend (from private repo)
if [ -d /home/user0704/QuantOL-frontend ]; then
    echo "📦 Starting frontend..."
    cd /home/user0704/QuantOL-frontend
    npm run dev &
else
    echo "⚠️  Frontend repo not found!"
    echo "   Clone it first: git clone https://github.com/FAKE0704/QuantOL-frontend.git /home/user0704/QuantOL-frontend"
    exit 1
fi

echo ""
echo "✅ Development environment started!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all services..."
echo "Stopping: pm2 stop quantol-backend-dev quantol-nextjs-dev"

# Handle Ctrl+C gracefully
trap 'echo ""; echo "🛑 Stopping services..."; pm2 stop quantol-backend-dev quantol-nextjs-dev; exit 0' INT

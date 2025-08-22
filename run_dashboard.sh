#!/bin/bash
# OBSERVATORIO ETS Dashboard Launch Script

echo "🚀 Starting OBSERVATORIO ETS Dashboard..."
echo "========================================"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "⚠️  Virtual environment not found. Running uv sync..."
    uv sync
fi

# Install/update dependencies
echo "📦 Updating dependencies..."
uv sync

# Check database connections
echo "🔍 Testing database connections..."
uv run python test/test_connections.py

echo ""
echo "🌐 Starting dashboard server..."
echo "========================================"
echo "Dashboard will be available at:"
echo "  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================"

# Start the dashboard
uv run python dashboard.py
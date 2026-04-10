#!/bin/bash
# Stop all Aurex services

echo "Stopping Aurex services..."

# Stop Docker containers
if [ -f docker-compose.yml ]; then
    docker-compose down
    echo "✓ Docker containers stopped"
fi

# Stop any running Python API processes
pkill -f "uvicorn api.main:app" || true
echo "✓ API server stopped"

# Stop any running PHP servers
pkill -f "php -S" || true
echo "✓ PHP server stopped (if running)"

echo ""
echo "All Aurex services stopped."

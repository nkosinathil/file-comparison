#!/bin/bash
# Aurex - Development Startup Script
# For local development without Docker

set -e

echo "========================================="
echo "Aurex - Development Mode"
echo "========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Check Python version
log_info "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    log_warn "Python 3 not found. Please install Python 3.11+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
log_info "Python version: $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    log_info "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
log_info "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
log_info "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Create necessary directories
log_info "Creating directories..."
mkdir -p data logs uploads

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    log_info "Creating .env file..."
    cp .env.example .env
fi

# Start API server in background
log_info "Starting API server..."
cd api
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!
cd ..

log_info "API server started (PID: $API_PID)"
log_info "API available at: http://localhost:8000"
log_info "API docs at: http://localhost:8000/docs"

echo ""
echo "========================================="
echo "Development server is running!"
echo ""
echo "API Server: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "For PHP web interface, run:"
echo "  cd web/public && php -S localhost:8080"
echo ""
echo "For desktop app, run:"
echo "  python run_aurex.py"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================="
echo ""

# Wait for API server
wait $API_PID

#!/bin/bash
# Aurex Deployment Script
# Production-ready deployment automation

set -e

echo "========================================="
echo "Aurex Bank Statement Intelligence"
echo "Production Deployment Script"
echo "========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    log_error "Please run as root or with sudo"
    exit 1
fi

# Check Docker installation
log_info "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

log_info "Docker and Docker Compose are installed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    log_warn ".env file not found. Creating from template..."
    cp .env.example .env
    log_info "Please edit .env file with your configuration before continuing."
    read -p "Press Enter to continue after editing .env file..."
fi

# Create necessary directories
log_info "Creating necessary directories..."
mkdir -p data logs uploads
chmod 755 data logs uploads

# Pull latest code (optional)
if [ "$1" == "--pull" ]; then
    log_info "Pulling latest code from repository..."
    git pull origin main
fi

# Stop existing containers
log_info "Stopping existing containers..."
docker-compose down || true

# Build images
log_info "Building Docker images..."
docker-compose build --no-cache

# Start services
log_info "Starting services..."
docker-compose up -d

# Wait for services to be ready
log_info "Waiting for services to start..."
sleep 10

# Health check
log_info "Performing health checks..."

# Check API
if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
    log_info "✓ API server is healthy"
else
    log_error "✗ API server health check failed"
fi

# Check Web
if curl -f http://localhost > /dev/null 2>&1; then
    log_info "✓ Web server is healthy"
else
    log_error "✗ Web server health check failed"
fi

# Show running containers
log_info "Running containers:"
docker-compose ps

# Show logs
echo ""
log_info "Deployment complete!"
echo ""
echo "========================================="
echo "Access URLs:"
echo "  Web Interface: http://localhost"
echo "  API Server: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "========================================="
echo ""
echo "Initial admin credentials:"
echo "  Username: admin"
echo "  Password: Check initial_admin_password.txt file"
echo "           or API server logs for randomly generated password"
echo "  ⚠️  CHANGE PASSWORD IMMEDIATELY!"
echo "========================================="
echo ""
log_info "To view logs, run: docker-compose logs -f"
log_info "To stop services, run: docker-compose down"
echo ""

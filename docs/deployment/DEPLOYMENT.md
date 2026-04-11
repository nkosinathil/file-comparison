# Deployment Guide

## Prerequisites

### System Requirements

- Ubuntu 22.04 LTS or later
- 4 CPU cores minimum
- 8 GB RAM minimum
- 100 GB disk space
- PostgreSQL 15+
- Redis 7+
- Python 3.11+
- PHP 8.2+
- Apache 2.4+

### Software Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y

# Install Redis
sudo apt install redis-server -y

# Install Python
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install PHP and Apache
sudo apt install apache2 php8.2 php8.2-cli php8.2-pgsql php8.2-curl -y

# Install system tools
sudo apt install tesseract-ocr poppler-utils git curl -y
```

## Installation

### 1. Clone Repository

```bash
sudo mkdir -p /var/www
cd /var/www
sudo git clone <repository-url> aurex
cd aurex
```

### 2. Setup Database

```bash
# Create database user
sudo -u postgres psql <<EOF
CREATE USER aurex WITH PASSWORD 'your_secure_password';
CREATE DATABASE aurex OWNER aurex;
GRANT ALL PRIVILEGES ON DATABASE aurex TO aurex;
EOF

# Run migrations
psql -U aurex -d aurex -f database/migrations/001_initial_schema.sql
psql -U aurex -d aurex -f database/migrations/002_audit_logs.sql
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

Update these critical values:
- `DB_PASS` - Database password
- `PYTHON_API_KEY` - Random secure string
- `OIDC_*` - Your OIDC provider details

### 4. Setup Python Backend

```bash
cd /var/www/aurex/python-backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Test application
uvicorn app.main:app --host 0.0.0.0 --port 8000
# Press Ctrl+C after verifying it starts
```

### 5. Setup Systemd Services

```bash
# Copy service files
sudo cp deploy/systemd/aurex-backend.service /etc/systemd/system/
sudo cp deploy/systemd/aurex-worker.service /etc/systemd/system/

# Create aurex user
sudo useradd -r -s /bin/false aurex

# Set ownership
sudo chown -R aurex:aurex /var/www/aurex

# Create data directories
sudo mkdir -p /var/aurex/{uploads,cases}
sudo chown -R aurex:aurex /var/aurex

# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable aurex-backend aurex-worker
sudo systemctl start aurex-backend aurex-worker

# Check status
sudo systemctl status aurex-backend
sudo systemctl status aurex-worker
```

### 6. Setup Apache

```bash
# Enable required modules
sudo a2enmod rewrite headers proxy proxy_http

# Copy vhost configuration
sudo cp deploy/apache/aurex.conf /etc/apache2/sites-available/

# Edit vhost (update ServerName)
sudo nano /etc/apache2/sites-available/aurex.conf

# Disable default site
sudo a2dissite 000-default

# Enable Aurex site
sudo a2ensite aurex

# Test configuration
sudo apache2ctl configtest

# Reload Apache
sudo systemctl reload apache2
```

### 7. Setup SSL (Production)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-apache -y

# Obtain certificate
sudo certbot --apache -d aurex.example.com

# Auto-renewal is configured by default
sudo systemctl status certbot.timer
```

## Docker Deployment (Alternative)

### Prerequisites

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y
```

### Deploy with Docker

```bash
cd /var/www/aurex/deploy/docker

# Copy environment
cp ../../.env.example ../../.env
nano ../../.env

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f

# Check status
docker-compose ps
```

## Post-Installation

### 1. Verify Services

```bash
# Check backend API
curl http://localhost:8000/health

# Check Redis
redis-cli ping

# Check PostgreSQL
psql -U aurex -d aurex -c "SELECT version();"
```

### 2. Create Admin User

```bash
# TODO: Run user creation script
python3 scripts/create_admin.py
```

### 3. Test Upload

1. Navigate to http://aurex.example.com
2. Login with admin credentials
3. Create a test case
4. Upload a sample PDF
5. Verify processing completes

## Monitoring

### Log Locations

```bash
# Application logs
sudo journalctl -u aurex-backend -f
sudo journalctl -u aurex-worker -f

# Apache logs
tail -f /var/log/apache2/aurex-access.log
tail -f /var/log/apache2/aurex-error.log

# PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-15-main.log
```

### Health Checks

```bash
# Backend API
curl http://localhost:8000/health

# PHP Frontend
curl http://localhost/api/health

# Database
psql -U aurex -d aurex -c "SELECT 1;"

# Redis
redis-cli ping
```

## Backup

### Database Backup

```bash
# Create backup script
cat > /usr/local/bin/backup-aurex-db.sh <<'EOF'
#!/bin/bash
BACKUP_DIR=/var/backups/aurex
mkdir -p $BACKUP_DIR
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U aurex aurex | gzip > $BACKUP_DIR/aurex_$DATE.sql.gz
find $BACKUP_DIR -name "aurex_*.sql.gz" -mtime +7 -delete
EOF

chmod +x /usr/local/bin/backup-aurex-db.sh

# Add to cron (daily at 2 AM)
echo "0 2 * * * /usr/local/bin/backup-aurex-db.sh" | sudo crontab -
```

### File Backup

```bash
# Backup uploads and cases
tar -czf /var/backups/aurex_files_$(date +%Y%m%d).tar.gz \
  /var/aurex/uploads \
  /var/aurex/cases
```

## Troubleshooting

### Backend Not Starting

```bash
# Check logs
sudo journalctl -u aurex-backend -n 50

# Check Python environment
cd /var/www/aurex/python-backend
source venv/bin/activate
python -c "import fastapi; print(fastapi.__version__)"

# Test manually
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Database Connection Issues

```bash
# Test connection
psql -U aurex -d aurex -h localhost

# Check PostgreSQL status
sudo systemctl status postgresql

# Check pg_hba.conf
sudo nano /etc/postgresql/15/main/pg_hba.conf
```

### Apache Issues

```bash
# Check Apache status
sudo systemctl status apache2

# Test configuration
sudo apache2ctl configtest

# Check error log
sudo tail -f /var/log/apache2/error.log
```

### Worker Not Processing

```bash
# Check worker status
sudo systemctl status aurex-worker

# Check Redis connection
redis-cli ping

# Check Celery queue
cd /var/www/aurex/python-backend
source venv/bin/activate
celery -A app.celery inspect active
```

## Scaling

### Horizontal Scaling

1. **Setup Load Balancer**:
   - HAProxy or Nginx
   - SSL termination
   - Health checks

2. **Add PHP Servers**:
   - Clone application
   - Point to same database
   - Use shared Redis for sessions

3. **Add Python Workers**:
   - Deploy on multiple servers
   - Connect to same Redis queue
   - Scale based on queue depth

### Database Replication

```bash
# Setup streaming replication
# On primary:
sudo nano /etc/postgresql/15/main/postgresql.conf
# Set: wal_level = replica

# Create replication user
CREATE USER replicator REPLICATION LOGIN PASSWORD 'password';

# Configure pg_hba.conf
host replication replicator <replica-ip>/32 md5
```

## Security Hardening

### Firewall

```bash
# Allow only necessary ports
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Fail2Ban

```bash
# Install Fail2Ban
sudo apt install fail2ban -y

# Configure for Apache
sudo cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

### Regular Updates

```bash
# Create update script
cat > /usr/local/bin/update-aurex.sh <<'EOF'
#!/bin/bash
cd /var/www/aurex
git pull
sudo systemctl restart aurex-backend aurex-worker
sudo systemctl reload apache2
EOF

chmod +x /usr/local/bin/update-aurex.sh
```

## Support

For deployment assistance:
- Email: ops@example.com
- Documentation: https://docs.aurex.example.com
- Issue Tracker: https://github.com/org/aurex/issues

# Aurex Web Application - Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Aurex web application across the three-server architecture.

## Prerequisites

### Server Requirements

#### SSO Server (192.168.1.59)
- **OS**: Linux (Ubuntu 22.04 LTS recommended)
- **RAM**: 2GB minimum
- **Software**: Keycloak 21+
- **Network**: Accessible from application server

#### Application Server (192.168.1.66)
- **OS**: Linux (Ubuntu 22.04 LTS recommended)
- **RAM**: 4GB minimum
- **Disk**: 50GB minimum
- **Software**:
  - Apache 2.4+
  - PHP 8.1+
  - PHP-FPM
  - PostgreSQL 13+
  - Composer

#### Python Server (192.168.1.90)
- **OS**: Linux (Ubuntu 22.04 LTS recommended)
- **RAM**: 8GB minimum (for PDF processing)
- **Disk**: 100GB+ (for MinIO storage)
- **Software**:
  - Python 3.10+
  - Redis 7+
  - MinIO
  - Tesseract OCR

## Deployment Steps

### 1. SSO Server Setup (Keycloak)

Keycloak should already be configured. You need to:

#### 1.1 Create Realm (if not exists)

```bash
# Log into Keycloak admin console
# http://192.168.1.59:8080/admin

# Create or select your realm
```

#### 1.2 Create Client for Aurex

```
Client ID: aurex-web
Client Protocol: openid-connect
Access Type: confidential
Valid Redirect URIs: http://192.168.1.66/auth/callback
Web Origins: http://192.168.1.66
```

#### 1.3 Create Roles

```
Roles to create:
- admin
- analyst
- client
- viewer
```

#### 1.4 Assign Roles to Users

Map users to appropriate roles based on their access level.

#### 1.5 Get Client Credentials

Note down:
- Realm name
- Client ID
- Client Secret (from Credentials tab)

### 2. Python Server Setup (192.168.1.90)

#### 2.1 Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and build tools
sudo apt install -y python3.10 python3.10-venv python3-pip \
    build-essential libpq-dev tesseract-ocr \
    poppler-utils

# Install Redis
sudo apt install -y redis-server
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Install MinIO (as binary)
wget https://dl.min.io/server/minio/release/linux-amd64/minio
chmod +x minio
sudo mv minio /usr/local/bin/
```

#### 2.2 Set Up MinIO

```bash
# Create MinIO user
sudo useradd -r -s /bin/false minio

# Create data directory
sudo mkdir -p /opt/minio/data
sudo chown minio:minio /opt/minio/data

# Create MinIO systemd service
sudo tee /etc/systemd/system/minio.service << 'EOF'
[Unit]
Description=MinIO
After=network.target

[Service]
Type=simple
User=minio
Group=minio
Environment="MINIO_ROOT_USER=admin"
Environment="MINIO_ROOT_PASSWORD=<secure_password>"
ExecStart=/usr/local/bin/minio server /opt/minio/data --console-address ":9001"
Restart=always
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

# Start MinIO
sudo systemctl daemon-reload
sudo systemctl enable minio
sudo systemctl start minio

# Create buckets
# Access MinIO console: http://192.168.1.90:9001
# Create buckets: aurex-uploads, aurex-results, aurex-exports
```

#### 2.3 Deploy Python Backend

```bash
# Create application user
sudo useradd -r -m -s /bin/bash aurex

# Create application directory
sudo mkdir -p /opt/aurex
sudo chown aurex:aurex /opt/aurex

# Switch to aurex user
sudo -u aurex -i

# Clone/copy application code
cd /opt/aurex
git clone <repository_url> python-backend
# OR: copy files from deployment package

# Create virtual environment
cd python-backend
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
cp /opt/aurex/python-backend/deploy/env-examples/.env.python-backend.example .env
nano .env  # Edit with actual values

# Create log directory
sudo mkdir -p /var/log/aurex
sudo chown aurex:aurex /var/log/aurex

# Create run directory for PID files
sudo mkdir -p /var/run/aurex
sudo chown aurex:aurex /var/run/aurex

# Exit aurex user
exit
```

#### 2.4 Install Systemd Services

```bash
# Copy service files
sudo cp /opt/aurex/python-backend/deploy/systemd/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable aurex-api
sudo systemctl enable aurex-celery-worker

# Start services
sudo systemctl start aurex-api
sudo systemctl start aurex-celery-worker

# Check status
sudo systemctl status aurex-api
sudo systemctl status aurex-celery-worker

# View logs
sudo journalctl -u aurex-api -f
sudo journalctl -u aurex-celery-worker -f
```

#### 2.5 Verify Python Backend

```bash
# Test API health
curl http://192.168.1.90:8001/api/health

# Expected response:
# {"status":"healthy","timestamp":"...","version":"1.0.0",...}

# Test ping
curl http://192.168.1.90:8001/api/ping

# Expected response:
# {"ping":"pong"}
```

### 3. Application Server Setup (192.168.1.66)

#### 3.1 Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Apache, PHP, and extensions
sudo apt install -y apache2 \
    php8.1 php8.1-fpm php8.1-cli php8.1-common \
    php8.1-pgsql php8.1-mbstring php8.1-xml \
    php8.1-curl php8.1-zip php8.1-gd php8.1-redis \
    composer

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Start services
sudo systemctl enable apache2 php8.1-fpm postgresql
sudo systemctl start apache2 php8.1-fpm postgresql
```

#### 3.2 Set Up PostgreSQL

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE aurex_db;
CREATE USER aurex_app_user WITH PASSWORD '<secure_password>';
GRANT ALL PRIVILEGES ON DATABASE aurex_db TO aurex_app_user;

# Enable UUID extension
\c aurex_db
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

# Exit psql
\q

# Import schema
sudo -u postgres psql -d aurex_db -f /path/to/database/schema.sql
```

#### 3.3 Deploy PHP Application

```bash
# Create application directory
sudo mkdir -p /var/www/gismartanalytics
sudo chown www-data:www-data /var/www/gismartanalytics

# Copy application code
sudo -u www-data mkdir -p /var/www/gismartanalytics/php-app
# Copy files from repository to /var/www/gismartanalytics/php-app

# Install PHP dependencies (if using Composer)
cd /var/www/gismartanalytics/php-app
sudo -u www-data composer install --no-dev --optimize-autoloader

# Create .env file
sudo -u www-data cp deploy/env-examples/.env.php-app.example .env
sudo -u www-data nano .env  # Edit with actual values

# Create storage directories
sudo -u www-data mkdir -p storage/logs storage/sessions storage/cache
sudo chmod 775 storage/logs storage/sessions storage/cache
```

#### 3.4 Configure Apache

```bash
# Copy virtual host configuration
sudo cp deploy/apache/aurex.conf /etc/apache2/sites-available/

# Enable required modules
sudo a2enmod rewrite proxy_fcgi setenvif headers

# Enable PHP-FPM
sudo a2enconf php8.1-fpm

# Disable default site (optional)
sudo a2dissite 000-default

# Enable Aurex site
sudo a2ensite aurex

# Test Apache configuration
sudo apache2ctl configtest

# Reload Apache
sudo systemctl reload apache2
```

#### 3.5 Configure PHP

```bash
# Edit PHP-FPM pool configuration
sudo nano /etc/php/8.1/fpm/pool.d/www.conf

# Ensure these settings:
# user = www-data
# group = www-data
# listen = /var/run/php/php8.1-fpm.sock

# Edit PHP settings
sudo nano /etc/php/8.1/fpm/php.ini

# Set these values:
upload_max_filesize = 100M
post_max_size = 100M
max_execution_time = 300
max_input_time = 300
memory_limit = 256M

# Restart PHP-FPM
sudo systemctl restart php8.1-fpm
```

#### 3.6 Verify PHP Application

```bash
# Test Apache is serving
curl http://192.168.1.66/

# Check PHP processing
echo "<?php phpinfo(); ?>" | sudo tee /var/www/gismartanalytics/public/info.php
curl http://192.168.1.66/info.php

# Remove info.php after verification
sudo rm /var/www/gismartanalytics/public/info.php
```

### 4. Initial Configuration

#### 4.1 Create Admin User in PostgreSQL

```sql
-- Connect to database
sudo -u postgres psql -d aurex_db

-- Insert admin user (replace with real Keycloak user)
INSERT INTO users (keycloak_sub, username, email, full_name, is_active)
VALUES ('keycloak-admin-sub-id', 'admin', 'admin@aurex.local', 'Administrator', true);

-- Assign admin role
INSERT INTO user_roles (user_id, role_name)
SELECT id, 'admin'
FROM users
WHERE username = 'admin';
```

#### 4.2 Test End-to-End Flow

1. Visit `http://192.168.1.66` in browser
2. Should redirect to Keycloak login
3. Log in with Keycloak credentials
4. Should redirect back to application
5. Verify you can see dashboard

### 5. Security Hardening

#### 5.1 Firewall Rules

```bash
# Python Server (192.168.1.90)
sudo ufw allow from 192.168.1.66 to any port 8001  # FastAPI
sudo ufw allow from 192.168.1.66 to any port 9000  # MinIO
sudo ufw enable

# Application Server (192.168.1.66)
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS (future)
sudo ufw enable
```

#### 5.2 Secure File Permissions

```bash
# Python server
sudo chmod 600 /opt/aurex/python-backend/.env
sudo chmod 600 /opt/minio/.env

# Application server
sudo chmod 600 /var/www/gismartanalytics/php-app/.env
```

#### 5.3 PostgreSQL Security

```bash
# Edit pg_hba.conf
sudo nano /etc/postgresql/13/main/pg_hba.conf

# Ensure only local connections:
# local   aurex_db    aurex_app_user                md5
# host    aurex_db    aurex_app_user    127.0.0.1/32      md5
# host    aurex_db    aurex_app_user    ::1/128           md5

# Restart PostgreSQL
sudo systemctl restart postgresql
```

### 6. Monitoring and Logging

#### 6.1 Log Locations

```
Python Server:
- FastAPI: /var/log/aurex/backend.log
- Celery Worker: /var/log/aurex/celery-worker.log
- Systemd: journalctl -u aurex-api
- Systemd: journalctl -u aurex-celery-worker

Application Server:
- Apache Access: /var/log/apache2/aurex_access.log
- Apache Error: /var/log/apache2/aurex_error.log
- PHP Application: /var/www/gismartanalytics/storage/logs/app.log
- PHP-FPM: /var/log/php8.1-fpm.log
```

#### 6.2 Log Rotation

```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/aurex << 'EOF'
/var/log/aurex/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 aurex aurex
    sharedscripts
    postrotate
        systemctl reload aurex-api aurex-celery-worker
    endscript
}
EOF
```

### 7. Backup Configuration

#### 7.1 PostgreSQL Backup

```bash
# Create backup script
sudo tee /usr/local/bin/backup_aurex_db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/aurex/postgresql"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
pg_dump -U aurex_app_user -d aurex_db -F c -f $BACKUP_DIR/aurex_db_$DATE.dump
find $BACKUP_DIR -name "aurex_db_*.dump" -mtime +7 -delete
EOF

sudo chmod +x /usr/local/bin/backup_aurex_db.sh

# Schedule with cron
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup_aurex_db.sh
```

#### 7.2 MinIO Backup

```bash
# Configure MinIO mirroring or use mc mirror command
# See MinIO documentation for details
```

### 8. SSL/TLS Configuration (Future)

When ready to enable HTTPS:

1. Obtain SSL certificate (Let's Encrypt, commercial CA, or self-signed)
2. Update Apache vhost to enable SSL
3. Update Keycloak redirect URIs to HTTPS
4. Update environment variables to use HTTPS URLs
5. Test thoroughly

### 9. Troubleshooting Deployment

#### Issue: FastAPI won't start

```bash
# Check logs
sudo journalctl -u aurex-api -n 50

# Common causes:
# - Port already in use
# - Missing environment variables
# - Python dependencies not installed

# Test manually
sudo -u aurex -i
cd /opt/aurex/python-backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

#### Issue: Celery worker won't start

```bash
# Check Redis is running
sudo systemctl status redis-server
redis-cli ping  # Should return PONG

# Check logs
sudo journalctl -u aurex-celery-worker -n 50

# Test manually
sudo -u aurex -i
cd /opt/aurex/python-backend
source venv/bin/activate
celery -A app.tasks worker --loglevel=DEBUG
```

#### Issue: PHP page shows error

```bash
# Check Apache error log
sudo tail -f /var/log/apache2/aurex_error.log

# Check PHP-FPM status
sudo systemctl status php8.1-fpm

# Check file permissions
ls -la /var/www/gismartanalytics/

# Test PHP syntax
php -l /var/www/gismartanalytics/public/index.php
```

#### Issue: Can't connect to PostgreSQL

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Test connection
psql -U aurex_app_user -d aurex_db -h localhost

# Check pg_hba.conf
sudo nano /etc/postgresql/13/main/pg_hba.conf
```

### 10. Health Checks

Create monitoring script:

```bash
#!/bin/bash
# /usr/local/bin/check_aurex_health.sh

echo "=== Aurex Health Check ==="

# Check FastAPI
echo -n "FastAPI: "
curl -s http://192.168.1.90:8001/api/ping | grep -q "pong" && echo "OK" || echo "FAIL"

# Check Celery (via Python script)
echo -n "Celery: "
# ... implement Celery inspection

# Check PostgreSQL
echo -n "PostgreSQL: "
PGPASSWORD=<password> psql -U aurex_app_user -d aurex_db -h localhost -c "SELECT 1" > /dev/null 2>&1 && echo "OK" || echo "FAIL"

# Check Redis
echo -n "Redis: "
redis-cli ping | grep -q "PONG" && echo "OK" || echo "FAIL"

# Check MinIO
echo -n "MinIO: "
curl -s http://192.168.1.90:9000/minio/health/live && echo "OK" || echo "FAIL"

# Check Apache
echo -n "Apache: "
systemctl is-active --quiet apache2 && echo "OK" || echo "FAIL"
```

## Post-Deployment

### Verify Checklist

- [ ] All services running (systemctl status)
- [ ] Can access web UI
- [ ] Can log in via Keycloak
- [ ] Can create a case
- [ ] Can upload a PDF
- [ ] Processing job completes successfully
- [ ] Can view results
- [ ] Can download exports
- [ ] Logs are being written
- [ ] Backups are configured

### Next Steps

1. Import initial data (if migrating from Qt app)
2. Create user accounts in Keycloak
3. Assign roles to users
4. Train users on new web interface
5. Monitor for errors in first week
6. Set up automated monitoring/alerting
7. Plan for HTTPS migration

## Rollback Plan

If deployment fails:

1. Stop new services
2. Restore previous state
3. Document what went wrong
4. Fix issues in development
5. Retry deployment

## Support

For deployment issues:
- Check logs first
- Review troubleshooting section
- Verify prerequisites
- Contact system administrator

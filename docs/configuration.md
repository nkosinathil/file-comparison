# Aurex Configuration Reference

## Overview

Aurex is configured through environment variables stored in `.env` files. This approach keeps sensitive information out of source code and allows easy configuration per environment.

## Configuration Files

### PHP Application (.env)

**Location**: `/var/www/gismartanalytics/php-app/.env`

**Template**: `deploy/env-examples/.env.php-app.example`

#### Application Settings

```env
APP_NAME="Aurex Bank Statement Intelligence"
APP_ENV=production
APP_DEBUG=false
APP_URL=http://192.168.1.66
APP_TIMEZONE=UTC
```

- `APP_NAME`: Application display name
- `APP_ENV`: Environment (`development`, `staging`, `production`)
- `APP_DEBUG`: Enable debug mode (never in production!)
- `APP_URL`: Public URL of the application
- `APP_TIMEZONE`: Default timezone for date/time operations

#### Security

```env
APP_KEY=<32-byte-hex-string>
SESSION_DRIVER=file
SESSION_LIFETIME=60
SESSION_SECURE_COOKIE=false
SESSION_SAME_SITE=lax
CSRF_TOKEN_NAME=_token
```

- `APP_KEY`: Encryption key (generate with `php -r "echo bin2hex(random_bytes(32));`)
- `SESSION_DRIVER`: Where sessions are stored (`file`, `database`, `redis`)
- `SESSION_LIFETIME`: Session timeout in minutes
- `SESSION_SECURE_COOKIE`: `true` when using HTTPS
- `SESSION_SAME_SITE`: Cookie SameSite attribute (`lax`, `strict`, `none`)

#### Database

```env
DB_CONNECTION=pgsql
DB_HOST=localhost
DB_PORT=5432
DB_DATABASE=aurex_db
DB_USERNAME=aurex_app_user
DB_PASSWORD=<secure-password>
```

#### Python Backend API

```env
PYTHON_API_BASE_URL=http://192.168.1.90:8001
PYTHON_API_TIMEOUT=30
PYTHON_API_KEY=<shared-secret>
```

#### Keycloak SSO

```env
KEYCLOAK_BASE_URL=http://192.168.1.59:8080
KEYCLOAK_REALM=<realm-name>
KEYCLOAK_CLIENT_ID=aurex-web
KEYCLOAK_CLIENT_SECRET=<client-secret>
KEYCLOAK_REDIRECT_URI=${APP_URL}/auth/callback
```

#### MinIO

```env
MINIO_ENDPOINT=192.168.1.90:9000
MINIO_ACCESS_KEY=<access-key>
MINIO_SECRET_KEY=<secret-key>
MINIO_USE_SSL=false
MINIO_BUCKET_UPLOADS=aurex-uploads
MINIO_BUCKET_RESULTS=aurex-results
MINIO_BUCKET_EXPORTS=aurex-exports
```

#### File Upload

```env
UPLOAD_MAX_SIZE=104857600  # 100MB
UPLOAD_ALLOWED_EXTENSIONS=pdf
```

#### Logging

```env
LOG_CHANNEL=daily
LOG_LEVEL=info
LOG_PATH=/var/www/gismartanalytics/storage/logs
```

### Python Backend (.env)

**Location**: `/opt/aurex/python-backend/.env`

**Template**: `deploy/env-examples/.env.python-backend.example`

#### Application

```env
APP_NAME=Aurex Python Backend
APP_VERSION=1.0.0
APP_ENV=production
DEBUG=false
LOG_LEVEL=INFO
```

#### FastAPI

```env
API_HOST=0.0.0.0
API_PORT=8001
API_WORKERS=4
API_RELOAD=false
```

- `API_HOST`: Bind address (`0.0.0.0` for all interfaces)
- `API_PORT`: HTTP port
- `API_WORKERS`: Number of Uvicorn workers
- `API_RELOAD`: Auto-reload on code changes (development only)

#### Security

```env
API_SECRET_KEY=<64-char-hex>
INTERNAL_API_KEY=<shared-secret>
API_CORS_ORIGINS=http://192.168.1.66,https://192.168.1.66
```

**Generate keys**:
```bash
openssl rand -hex 32  # For API_SECRET_KEY
openssl rand -hex 32  # For INTERNAL_API_KEY
```

#### Database

```env
DB_HOST=192.168.1.66
DB_PORT=5432
DB_NAME=aurex_db
DB_USER=aurex_app_user
DB_PASSWORD=<password>
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

#### Redis

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=<password>
REDIS_DB=0
```

#### Celery

```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_WORKER_CONCURRENCY=4
CELERY_TASK_TIME_LIMIT=3600
CELERY_TASK_SOFT_TIME_LIMIT=3300
```

#### MinIO

```env
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=<access-key>
MINIO_SECRET_KEY=<secret-key>
MINIO_SECURE=false
MINIO_BUCKET_UPLOADS=aurex-uploads
MINIO_BUCKET_RESULTS=aurex-results
MINIO_BUCKET_EXPORTS=aurex-exports
```

#### File Processing

```env
MAX_UPLOAD_SIZE_MB=100
ALLOWED_FILE_EXTENSIONS=pdf
TEMP_UPLOAD_DIR=/tmp/aurex/uploads
TEMP_PROCESSING_DIR=/tmp/aurex/processing
```

#### AI Chat

```env
ENABLE_AI_CHAT=true
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_TIMEOUT=120
```

#### PDF Processing

```env
PDF_DPI=300
TESSERACT_PATH=/usr/bin/tesseract
ENABLE_OCR_FALLBACK=true
```

## Security Best Practices

### 1. Never Commit .env Files

Add to `.gitignore`:
```
.env
.env.*
!.env.example
```

### 2. Use Strong Random Keys

```bash
# Generate secure random keys
openssl rand -hex 32
php -r "echo bin2hex(random_bytes(32));"
python -c "import secrets; print(secrets.token_hex(32))"
```

### 3. Restrict File Permissions

```bash
# .env files should be readable only by the application user
chmod 600 .env
```

### 4. Use Separate Credentials Per Environment

- Development: Weak passwords are OK
- Staging: Moderate security
- Production: Strong passwords, rotated regularly

### 5. Avoid Hardcoding

Never hardcode values in source code:
```php
// Bad
$dbHost = "192.168.1.66";

// Good
$dbHost = getenv('DB_HOST');
```

## Environment-Specific Configuration

### Development

```env
APP_ENV=development
APP_DEBUG=true
LOG_LEVEL=DEBUG
API_RELOAD=true
```

### Staging

```env
APP_ENV=staging
APP_DEBUG=false
LOG_LEVEL=INFO
# Use production-like settings but separate infrastructure
```

### Production

```env
APP_ENV=production
APP_DEBUG=false
LOG_LEVEL=WARNING
SESSION_SECURE_COOKIE=true
MINIO_SECURE=true
```

## Configuration Validation

### PHP

Create a config test script:

```php
// scripts/test-config.php
<?php
$required = ['DB_HOST', 'DB_PASSWORD', 'KEYCLOAK_CLIENT_SECRET'];
$missing = [];
foreach ($required as $key) {
    if (empty(getenv($key))) {
        $missing[] = $key;
    }
}
if ($missing) {
    echo "Missing required config: " . implode(', ', $missing) . "\n";
    exit(1);
}
echo "Configuration valid\n";
```

### Python

Config validation happens automatically via Pydantic in `app/core/config.py`.

Test with:
```bash
python -c "from app.core.config import settings; print('Config OK')"
```

## Changing Configuration

### Runtime Changes (No Restart)

Some settings can be changed in the database:

```sql
UPDATE app_settings SET setting_value = 'new_value' WHERE setting_key = 'max_upload_size_mb';
```

### Requires Service Restart

Changes to `.env` files require restarting services:

```bash
# PHP (restart PHP-FPM and Apache)
sudo systemctl restart php8.1-fpm apache2

# Python (restart FastAPI and Celery)
sudo systemctl restart aurex-api aurex-celery-worker
```

## Configuration Secrets Management

For production, consider using a secrets manager:

### Option 1: Ansible Vault

```bash
# Encrypt .env file
ansible-vault encrypt .env

# Edit
ansible-vault edit .env

# Decrypt
ansible-vault decrypt .env
```

### Option 2: HashiCorp Vault

Integrate with Vault to fetch secrets at runtime.

### Option 3: AWS Secrets Manager / Azure Key Vault

For cloud deployments.

## Troubleshooting Configuration

### Check Current Config

```php
// PHP
var_dump(getenv('DB_HOST'));
```

```python
# Python
from app.core.config import settings
print(settings.DB_HOST)
```

### Common Issues

**Issue**: Changes to `.env` not taking effect  
**Solution**: Restart services

**Issue**: "Missing environment variable" error  
**Solution**: Check `.env` file exists and has correct variable names

**Issue**: Database connection fails  
**Solution**: Verify `DB_*` settings, test PostgreSQL connection manually

**Issue**: Keycloak redirect fails  
**Solution**: Verify `KEYCLOAK_REDIRECT_URI` matches exactly what's in Keycloak client config

## Configuration Checklist

Before deployment:

- [ ] All `.env` files created from templates
- [ ] All placeholder values replaced with real values
- [ ] Secrets are strong and unique
- [ ] File permissions set to 600
- [ ] Database credentials tested
- [ ] API keys match between PHP and Python
- [ ] Keycloak client configuration matches
- [ ] MinIO buckets created
- [ ] Services can start successfully
- [ ] No secrets committed to git

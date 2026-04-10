# Aurex Bank Statement Intelligence

## Complete Production-Ready System

This repository contains a full-stack web application for bank statement analysis with Single Sign-On (SSO) authentication, Python API, and PHP web interface.

## 🚀 Features

### Core Functionality
- **Bank Statement Processing**: Automated PDF parsing and analysis
- **AI-Powered Chat**: Intelligent assistant for querying transaction data
- **Network Visualization**: Visual representation of transaction patterns
- **Case Management**: Organize and track multiple investigations
- **Real-time Progress**: WebSocket-based live updates

### Security & Authentication
- **SSO Support**: OAuth2 and SAML 2.0 integration
- **JWT Authentication**: Secure token-based API access
- **Role-Based Access Control**: Admin, Investigator, and User roles
- **CSRF Protection**: Built-in protection against cross-site attacks

### Technology Stack
- **Backend API**: Python FastAPI with async support
- **Web Interface**: PHP 8.2 with modern responsive design
- **Database**: SQLite for simplicity, easily upgradable to PostgreSQL
- **Web Server**: Nginx with optimized configuration
- **Containerization**: Docker and Docker Compose for easy deployment

## 📋 Requirements

### For Docker Deployment (Recommended)
- Docker 20.10+
- Docker Compose 1.29+
- 4GB RAM minimum
- 10GB disk space

### For Manual Deployment
- Python 3.11+
- PHP 8.2+
- Nginx 1.20+
- Tesseract OCR
- Poppler Utils

## 🔧 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/nkosinathil/file-comparison.git
cd file-comparison
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
nano .env
```

### 3. Deploy with Docker
```bash
sudo ./deploy.sh
```

### 4. Access the Application
- **Web Interface**: http://localhost
- **API Documentation**: http://localhost:8000/docs
- **Default Credentials**: 
  - Username: `admin`
  - Password: `admin123`
  - ⚠️ **Change immediately after first login!**

## 📁 Project Structure

```
file-comparison/
├── api/                      # Python FastAPI backend
│   ├── main.py              # Main API server
│   ├── auth.py              # Authentication & SSO
│   ├── processing.py        # Processing manager
│   └── websocket_manager.py # WebSocket connections
│
├── web/                      # PHP web interface
│   ├── public/              # Public web pages
│   │   ├── login.php        # Login page
│   │   ├── dashboard.php    # Main dashboard
│   │   └── ...
│   ├── includes/            # PHP includes
│   │   ├── config.php       # Configuration
│   │   ├── auth.php         # Authentication helpers
│   │   └── api_client.php   # API client
│   ├── templates/           # HTML templates
│   └── assets/              # CSS, JS, images
│
├── aurex_bank_analyzer/     # Core analysis engine
│   ├── app.py               # Desktop application
│   ├── core/                # Core functionality
│   └── ui/                  # UI components
│
├── docker/                   # Docker configuration
│   ├── Dockerfile.api       # API container
│   ├── Dockerfile.web       # Web container
│   ├── Dockerfile.nginx     # Nginx container
│   ├── nginx/               # Nginx configs
│   └── supervisor/          # Supervisor configs
│
├── docker-compose.yml       # Docker Compose config
├── deploy.sh                # Deployment script
├── .env.example             # Environment template
└── README.md                # This file
```

## 🔐 SSO Configuration

### OAuth2 Setup
1. Register your application with OAuth provider
2. Update `.env` with:
   ```
   SSO_ENABLED=true
   SSO_PROVIDER=oauth
   OAUTH_CLIENT_ID=your-client-id
   OAUTH_CLIENT_SECRET=your-client-secret
   OAUTH_REDIRECT_URI=https://your-domain.com/oauth/callback
   ```

### SAML Setup
1. Configure your SAML Identity Provider
2. Update `.env` with:
   ```
   SSO_ENABLED=true
   SSO_PROVIDER=saml
   SAML_IDP_URL=https://idp.provider.com/saml
   SAML_SP_ENTITY_ID=https://your-domain.com
   ```

## 🌐 API Endpoints

### Authentication
- `POST /api/auth/token` - Login with username/password
- `POST /api/auth/register` - Register new user (admin only)
- `GET /api/auth/me` - Get current user info
- `GET /api/sso/oauth/authorize` - Initiate OAuth flow
- `POST /api/sso/oauth/callback` - OAuth callback
- `POST /api/sso/saml/login` - SAML login

### Case Management
- `GET /api/cases` - List all cases
- `POST /api/cases` - Create new case
- `GET /api/cases/{id}` - Get case details
- `DELETE /api/cases/{id}` - Delete case

### Processing
- `POST /api/cases/{id}/process` - Start processing
- `POST /api/cases/{id}/cancel` - Cancel processing
- `GET /api/cases/{id}/status` - Get processing status
- `POST /api/cases/{id}/upload` - Upload files

### Analysis
- `POST /api/analysis/chat` - AI chat query
- `POST /api/analysis/insights` - Get insights

### WebSocket
- `WS /ws/cases/{id}/progress` - Real-time progress updates

## 🚀 Production Deployment

### SSL/TLS Configuration
1. Obtain SSL certificates (Let's Encrypt recommended)
2. Place certificates in `docker/nginx/ssl/`
3. Update `docker/nginx/conf.d/default.conf` to enable HTTPS
4. Set `SECURE_COOKIES=true` in `.env`

### Environment Variables
Key production settings:
```env
SSO_ENABLED=true
SECURE_COOKIES=true
LOG_LEVEL=warning
API_WORKERS=8
```

### Scaling
To scale API workers:
```bash
docker-compose up -d --scale api=4
```

### Monitoring
1. Enable monitoring in `.env`:
   ```
   ENABLE_MONITORING=true
   ```
2. Configure Sentry (optional):
   ```
   SENTRY_DSN=your-sentry-dsn
   ```

### Backup
Regular backups recommended:
```bash
# Backup data directory
tar -czf aurex-backup-$(date +%Y%m%d).tar.gz data/

# Backup user database
cp api/users.json users-backup-$(date +%Y%m%d).json
```

## 📊 Usage

### Creating a Case
1. Log in to web interface
2. Click "New Case"
3. Fill in case details
4. Upload PDF bank statements
5. Click "Start Processing"

### Analyzing Data
1. Open completed case
2. View insights and statistics
3. Use AI chat for queries
4. Explore network visualization
5. Export results

### Managing Users
1. Log in as admin
2. Navigate to Administration
3. Add/remove users
4. Assign roles
5. Manage permissions

## 🐛 Troubleshooting

### API Connection Issues
```bash
# Check API status
curl http://localhost:8000/api/health

# View API logs
docker-compose logs api
```

### Web Interface Issues
```bash
# Check web server status
curl http://localhost

# View web logs
docker-compose logs web
```

### Permission Issues
```bash
# Fix permissions
sudo chown -R www-data:www-data web/data
sudo chmod -R 755 web/data
```

## 📝 License

This project is proprietary software. All rights reserved.

## 👤 Author

Developed for production deployment with enterprise-grade security and scalability.

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Check application logs

## 🔄 Updates

To update to the latest version:
```bash
git pull origin main
sudo ./deploy.sh --pull
```

---

**⚠️ Important Security Notes:**
- Change default admin password immediately
- Use HTTPS in production
- Keep secrets in `.env` file
- Regular security audits recommended
- Enable monitoring for production use

# Aurex - Bank Statement Intelligence

Complete production-ready system for bank statement analysis with web interface, SSO authentication, and Python API.

## 🌟 Overview

Aurex is an enterprise-grade bank statement analysis platform featuring:
- **Web Interface**: Modern PHP-based responsive UI
- **Python API**: FastAPI backend with WebSocket support
- **Desktop App**: PySide6 GUI for local analysis
- **SSO Authentication**: OAuth2 and SAML 2.0 support
- **AI-Powered Analysis**: Intelligent transaction querying
- **Real-time Processing**: Live progress updates via WebSocket

## 🚀 Quick Start (Docker)

```bash
# Clone repository
git clone https://github.com/nkosinathil/file-comparison.git
cd file-comparison

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Deploy
sudo ./deploy.sh
```

**Access:**
- Web Interface: http://localhost
- API Docs: http://localhost:8000/docs
- Default Login: admin / admin123 (⚠️ change immediately!)

## 📚 Documentation

See [DEPLOYMENT.md](DEPLOYMENT.md) for:
- Complete deployment guide
- SSO configuration
- Production setup
- Scaling & monitoring
- Troubleshooting

## 🏗️ Architecture

### Components
1. **Python API Server** (FastAPI)
   - RESTful API endpoints
   - WebSocket support
   - JWT authentication
   - SSO integration

2. **PHP Web Interface**
   - Responsive dashboard
   - Case management
   - File upload
   - Real-time monitoring

3. **Desktop Application** (PySide6)
   - Local analysis
   - Offline processing
   - AI chat interface
   - Network visualization

### Technology Stack
- **Backend**: Python 3.11, FastAPI, SQLite
- **Frontend**: PHP 8.2, Bootstrap 5, JavaScript
- **Web Server**: Nginx
- **Container**: Docker, Docker Compose
- **Authentication**: JWT, OAuth2, SAML

## 🔐 Security Features

- SSO authentication (OAuth2/SAML)
- JWT token-based API access
- Role-based access control
- CSRF protection
- Security headers
- SSL/TLS support
- Input sanitization

## 📊 Key Features

### Case Management
- Create and organize investigation cases
- Track processing status
- Store case metadata
- Export results

### Statement Processing
- Automated PDF parsing
- Transaction extraction
- Data normalization
- Database storage

### Analysis Tools
- AI-powered chat assistant
- Transaction insights
- Network visualization
- Statistical analysis

### API Capabilities
- RESTful endpoints
- Real-time WebSocket updates
- File upload handling
- Authentication & authorization

## 🛠️ Development

### Desktop Application
```bash
python run_aurex.py
```

### API Server
```bash
cd api
python -m uvicorn main:app --reload
```

### Requirements
```bash
pip install -r requirements.txt
```

## 📦 Production Deployment

### Environment Configuration
```env
SSO_ENABLED=true
SECURE_COOKIES=true
API_WORKERS=8
LOG_LEVEL=warning
```

### SSL Setup
1. Obtain certificates
2. Configure nginx
3. Enable HTTPS redirect
4. Update environment

### Scaling
```bash
docker-compose up -d --scale api=4
```

## 🔧 API Endpoints

### Authentication
- POST `/api/auth/token` - Login
- POST `/api/auth/register` - Register user
- GET `/api/auth/me` - Get current user

### Cases
- GET `/api/cases` - List cases
- POST `/api/cases` - Create case
- GET `/api/cases/{id}` - Get case
- DELETE `/api/cases/{id}` - Delete case

### Processing
- POST `/api/cases/{id}/process` - Start processing
- POST `/api/cases/{id}/cancel` - Cancel
- GET `/api/cases/{id}/status` - Get status

### Analysis
- POST `/api/analysis/chat` - AI chat
- POST `/api/analysis/insights` - Get insights

## 📝 License

Proprietary software. All rights reserved.

## 🤝 Support

For deployment assistance or issues, refer to:
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- API documentation at `/docs` endpoint
- Application logs in `logs/` directory

---

**Production Ready** ✅ Fully containerized ✅ SSO enabled ✅ API complete ✅ PHP web interface ready

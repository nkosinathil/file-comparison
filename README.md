# Aurex Web Application

A powerful web-based bank statement analysis platform with AI-powered insights, network visualization, and role-based access control.

## Overview

Aurex is a migrated and enhanced version of the original Aurex Python/Qt desktop application, now designed as a modern, multi-user web platform. The system analyzes FNB bank statements, extracts transactions, generates insights, and provides an intuitive interface for financial investigations.

## Features

- **Multi-User Web Access**: Browser-based interface accessible from anywhere
- **SSO Authentication**: Integrated with Keycloak for secure, centralized authentication
- **Role-Based Access**: Admin, Analyst, and Client/Viewer roles
- **Automated PDF Processing**: Extract and analyze transactions from bank statements
- **AI-Powered Chat**: Query your financial data using natural language
- **Network Visualization**: See relationships and patterns in transaction data
- **Insights Dashboard**: Categorized spending breakdowns with visual charts
- **Background Processing**: Handle large datasets without blocking the UI
- **Object Storage**: Secure file management with MinIO
- **Audit Logging**: Track all important actions for compliance

## Architecture

Aurex uses a distributed 3-server architecture:

1. **SSO Server** (192.168.1.59): Keycloak for authentication
2. **Application Server** (192.168.1.66): PHP web frontend + PostgreSQL database
3. **Python Server** (192.168.1.90): FastAPI + Celery + Redis + MinIO for processing

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

## Technology Stack

### Frontend
- **PHP 8.1+**: Server-side application logic
- **Apache**: Web server
- **HTML/CSS/JavaScript**: Clean, responsive UI with Roboto font

### Backend
- **Python 3.10+**: Core processing engine
- **FastAPI**: REST API framework
- **Celery**: Distributed task queue
- **Redis**: Message broker and caching

### Data & Storage
- **PostgreSQL**: Application database
- **MinIO**: Object storage for files
- **SQLite**: Legacy transaction storage (migrated to PostgreSQL)

### Authentication
- **Keycloak**: SSO and OIDC provider

## Project Structure

```
├── php-app/                    # PHP Web Application
│   ├── public/                 # Web root (Apache DocumentRoot)
│   ├── src/
│   │   ├── Controllers/        # HTTP request handlers
│   │   ├── Services/           # Business logic and integrations
│   │   ├── Repositories/       # Database access layer
│   │   ├── Middleware/         # Auth, CSRF, logging
│   │   ├── Views/              # HTML templates
│   │   └── Config/             # Application configuration
│   └── storage/logs/           # Application logs
│
├── python-backend/             # Python Processing Backend
│   └── app/
│       ├── main.py             # FastAPI entry point
│       ├── api/                # REST API routes
│       ├── services/           # Business logic
│       ├── tasks/              # Celery tasks
│       ├── models/             # Data models
│       ├── core/               # Core utilities
│       ├── adapters/           # External integrations
│       └── legacy_logic/       # Migrated Qt app logic
│
├── docs/                       # Documentation
│   ├── architecture.md         # System architecture
│   ├── deployment.md           # Deployment guide
│   ├── configuration.md        # Configuration reference
│   ├── database.md             # Database schema
│   ├── api.md                  # API documentation
│   ├── authentication.md       # Auth setup guide
│   ├── maintenance.md          # Maintenance procedures
│   ├── troubleshooting.md      # Common issues and solutions
│   └── migration-from-qt.md    # Qt to Web migration guide
│
├── database/                   # Database migrations and schema
│   ├── migrations/             # SQL migration files
│   └── schema.sql              # Complete schema definition
│
├── deploy/                     # Deployment configuration
│   ├── apache/                 # Apache vhost configs
│   ├── systemd/                # Service unit files
│   ├── nginx/                  # Reverse proxy configs (optional)
│   └── env-examples/           # Environment file templates
│
└── aurex_bank_analyzer/        # Original Qt application (reference)
    └── ...                     # Kept for logic migration reference
```

## Quick Start

### Prerequisites

- **SSO Server**: Keycloak instance running at 192.168.1.59
- **Application Server**: Apache, PHP 8.1+, PostgreSQL 13+
- **Python Server**: Python 3.10+, Redis, MinIO

### Installation

See [docs/deployment.md](docs/deployment.md) for complete installation instructions.

### Configuration

1. Copy environment templates:
   ```bash
   cp deploy/env-examples/.env.php-app.example php-app/.env
   cp deploy/env-examples/.env.python-backend.example python-backend/.env
   ```

2. Configure each `.env` file with your server details

3. Run database migrations:
   ```bash
   psql -U aurex -d aurex_db -f database/schema.sql
   ```

4. Start services (see deployment docs for details)

## User Roles

### Admin
- Full system access
- User management
- System configuration
- All case operations

### Analyst
- Create and manage cases
- Upload files
- Trigger processing
- View results and insights
- Download exports

### Client/Viewer
- View assigned cases
- View results and insights
- Download exports
- No upload or processing permissions

## Core Workflows

### 1. Creating a Case
1. Log in via Keycloak
2. Navigate to "Cases" → "New Case"
3. Enter case details (name, evidence number, description)
4. Save case

### 2. Processing Bank Statements
1. Open a case
2. Navigate to "Upload" tab
3. Select PDF bank statement files
4. Click "Upload and Process"
5. Monitor progress in "Jobs" view
6. View results when complete

### 3. Analyzing Results
1. Open a completed case
2. View insights dashboard
3. Use AI chat to query data
4. Explore network visualization
5. Download exports

## API Documentation

The Python backend provides a REST API for integration.

See [docs/api.md](docs/api.md) for complete API documentation.

## Development

### Running Locally (Development Mode)

#### PHP Application
```bash
cd php-app
php -S localhost:8000 -t public
```

#### Python Backend
```bash
cd python-backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

#### Celery Worker
```bash
cd python-backend
celery -A app.tasks worker --loglevel=info
```

### Testing

```bash
# PHP tests (if using PHPUnit)
cd php-app
vendor/bin/phpunit

# Python tests
cd python-backend
pytest
```

## Maintenance

See [docs/maintenance.md](docs/maintenance.md) for:
- Backup procedures
- Log rotation
- Database maintenance
- Performance tuning
- Monitoring setup

## Troubleshooting

See [docs/troubleshooting.md](docs/troubleshooting.md) for common issues and solutions.

## Migration from Qt Application

If you're migrating from the original Qt desktop application, see [docs/migration-from-qt.md](docs/migration-from-qt.md) for guidance.

## Security

- Never commit `.env` files or secrets to version control
- Use HTTPS in production
- Keep Keycloak and dependencies updated
- Follow principle of least privilege for database users
- Regularly review audit logs
- Implement rate limiting for production APIs

## Contributing

1. Create a feature branch
2. Make changes
3. Test thoroughly
4. Submit pull request
5. Update documentation as needed

## License

[Specify license here]

## Support

For issues and questions:
- Check [docs/troubleshooting.md](docs/troubleshooting.md)
- Review architecture documentation
- Contact system administrator

## Acknowledgments

- Original Aurex Qt application by the development team
- Keycloak for authentication infrastructure
- FastAPI and Celery communities
- PHP community for excellent tooling

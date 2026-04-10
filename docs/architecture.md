# Aurex Web Application - Architecture Documentation

## Overview

Aurex is a bank statement analysis platform migrated from a Python/Qt desktop application to a modern web-based architecture. The system uses a distributed 3-server setup to separate concerns and optimize performance.

## System Architecture

### Three-Server Model

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Browser                           │
│                    (Modern Web Browser)                          │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTPS
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              SSO Server (192.168.1.59)                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Keycloak                               │  │
│  │  - OIDC Authentication                                    │  │
│  │  - User Management                                        │  │
│  │  - Role-Based Access Control                             │  │
│  │  - Authorization Code Flow                               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                      ▲
                      │ OIDC Protocol
                      │
┌─────────────────────┴───────────────────────────────────────────┐
│           Application Server (192.168.1.66)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Apache + PHP 8.1                       │  │
│  │  - Web Frontend (MVC Architecture)                        │  │
│  │  - Session Management                                     │  │
│  │  - User Interface Rendering                              │  │
│  │  - OIDC Client Integration                               │  │
│  │  Path: /var/www/gismartanalytics/public                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    PostgreSQL                             │  │
│  │  - Application Metadata                                   │  │
│  │  - User Mappings                                          │  │
│  │  - Cases & Jobs                                           │  │
│  │  - Audit Logs                                             │  │
│  │  - Object References (MinIO)                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────┬───────────────────────────────────────────┘
                      │ HTTP API Calls
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│             Python Server (192.168.1.90)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    FastAPI                                │  │
│  │  - REST API Endpoints                                     │  │
│  │  - Request Validation                                     │  │
│  │  - Business Logic Orchestration                          │  │
│  │  - Task Queueing                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Celery Workers + Redis                       │  │
│  │  - Background Job Processing                              │  │
│  │  - PDF Parsing & Analysis                                │  │
│  │  - Transaction Categorization                            │  │
│  │  - Network Graph Generation                              │  │
│  │  - AI-Powered Insights                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                      MinIO                                │  │
│  │  - Uploaded PDF Files                                     │  │
│  │  - Generated Reports                                      │  │
│  │  - Export Archives                                        │  │
│  │  - Processing Artifacts                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Server Responsibilities

### 1. SSO Server (192.168.1.59)
**Technology:** Keycloak

**Purpose:**
- Centralized identity and access management
- Single sign-on across applications
- User authentication via OIDC
- Role and permission management
- Token issuance and validation

**Key Features:**
- Existing realm/client ecosystem
- Authorization Code Flow for web browsers
- JWT token generation
- Role-based access control
- User federation support

### 2. Application Server (192.168.1.66)
**Technology:** Apache, PHP 8.1, PostgreSQL

**Purpose:**
- Web frontend hosting
- User session management
- Business-facing web flows
- Application data persistence
- Integration orchestration

**Components:**

#### Apache + PHP-FPM
- Serves PHP web application
- Handles HTTP requests
- Manages static assets
- Vhost path: `/var/www/gismartanalytics/public`

#### PostgreSQL Database
Stores:
- User mappings from Keycloak
- Case metadata
- Job queue references
- Processing results metadata
- Audit logs
- Application settings
- MinIO object references

#### PHP Application (MVC Pattern)
- **Controllers**: Handle HTTP requests, validate input, orchestrate services
- **Services**: 
  - OIDC authentication service
  - Python API client
  - PostgreSQL repositories
  - MinIO object handling
- **Views**: Templated HTML pages with premium UI
- **Middleware**: Authentication, authorization, CSRF protection

### 3. Python Server (192.168.1.90)
**Technology:** Python, FastAPI, Celery, Redis, MinIO

**Purpose:**
- Heavy processing engine
- Background job execution
- File storage management
- Core business logic implementation

**Components:**

#### FastAPI Application
REST API providing:
- `/health` - Health check endpoint
- `/api/upload` - File upload intake
- `/api/process` - Trigger processing job
- `/api/jobs/{id}/status` - Poll job status
- `/api/jobs/{id}/results` - Retrieve results
- `/api/cases/{id}` - Case management

#### Celery Workers
Background tasks:
- PDF parsing and text extraction
- Transaction extraction and normalization
- Account analysis
- Network graph generation
- Category classification
- AI-powered insights generation

#### Redis
- Celery message broker
- Task result backend
- Caching layer for frequently accessed data

#### MinIO
Object storage for:
- Original uploaded PDF files
- Processed transaction databases
- Generated visualizations
- Export packages
- Temporary processing artifacts

## Data Flow

### User Login Flow

```
1. User visits PHP application
2. PHP redirects to Keycloak (Authorization Code Flow)
3. User authenticates with Keycloak
4. Keycloak redirects back with authorization code
5. PHP exchanges code for access token
6. PHP validates token and creates session
7. PHP maps user to local PostgreSQL record
8. User accesses protected resources
```

### Case Processing Flow

```
1. User creates case via PHP UI
2. PHP stores case metadata in PostgreSQL
3. User uploads PDF files
4. PHP validates files
5. PHP uploads files to MinIO
6. PHP calls Python API /api/upload with MinIO references
7. Python API creates Celery task
8. Python returns job_id
9. PHP stores job_id in PostgreSQL
10. Celery worker:
    a. Downloads files from MinIO
    b. Parses PDFs
    c. Extracts transactions
    d. Performs analysis
    e. Generates insights
    f. Uploads results to MinIO
    g. Updates job status
11. PHP polls /api/jobs/{id}/status
12. When complete, PHP retrieves results
13. PHP displays results to user
```

### Result Retrieval Flow

```
1. User navigates to completed case
2. PHP queries PostgreSQL for job results
3. PHP calls Python API /api/jobs/{id}/results
4. Python returns MinIO object references
5. PHP generates signed URLs for MinIO objects
6. User views/downloads results
```

## Security Model

### Authentication
- **Method**: OIDC Authorization Code Flow
- **Provider**: Keycloak on SSO server
- **Session**: PHP session with secure cookies
- **Token Storage**: Server-side only, never in client

### Authorization
- **Roles**: Admin, Analyst, Client/Viewer
- **Enforcement**: Both PHP (route level) and Python (API level)
- **Mapping**: Keycloak roles → PostgreSQL user records

### Data Protection
- **Secrets**: Stored in environment files, never in code
- **File Uploads**: Validated (type, size, content)
- **SQL**: Parameterized queries via PDO
- **CSRF**: Token validation on state-changing requests
- **HTTPS**: Designed for future HTTPS deployment

## Integration Points

### PHP ↔ Keycloak
- **Protocol**: OAuth 2.0 / OIDC
- **Library**: league/oauth2-client or similar
- **Configuration**: Client ID, Secret, Endpoints (all in .env)

### PHP ↔ Python API
- **Protocol**: HTTP/JSON
- **Client**: Guzzle or cURL wrapper
- **Endpoints**: Configurable base URL in .env
- **Authentication**: Internal API key or mutual TLS (future)

### PHP ↔ PostgreSQL
- **Driver**: PDO with pgsql driver
- **Connection**: DSN from .env
- **Pattern**: Repository pattern for data access

### PHP ↔ MinIO
- **SDK**: aws/aws-sdk-php (S3-compatible)
- **Operations**: Generate signed URLs for downloads
- **Configuration**: Endpoint, credentials in .env

### Python ↔ Redis
- **Purpose**: Celery broker and result backend
- **Library**: redis-py
- **Configuration**: Redis URL in .env

### Python ↔ MinIO
- **SDK**: minio-py
- **Operations**: Upload, download, list, delete
- **Configuration**: Endpoint, credentials in .env

## Scalability Considerations

### Current Phase (Single Server per Role)
- SSO server handles authentication
- App server handles 10-50 concurrent users
- Python server runs multiple Celery workers

### Future Scaling Options
1. **Horizontal Scaling**:
   - Add more Celery workers
   - Load balance PHP application servers
   - Replicate PostgreSQL with read replicas

2. **Caching**:
   - Redis for session storage
   - Cache frequently accessed results
   - MinIO CDN integration

3. **Async Updates**:
   - WebSocket or Server-Sent Events for real-time progress
   - Replace polling with push notifications

## Technology Stack Summary

| Component | Technology | Version | Purpose |
|-----------|-----------|---------|---------|
| SSO Server | Keycloak | Current | Authentication & Authorization |
| Web Server | Apache | 2.4+ | HTTP Server |
| App Language | PHP | 8.1+ | Frontend Application |
| App Database | PostgreSQL | 13+ | Application Data |
| API Framework | FastAPI | 0.100+ | REST API |
| Task Queue | Celery | 5.3+ | Background Jobs |
| Message Broker | Redis | 7+ | Task Queue & Cache |
| Object Storage | MinIO | Latest | File Storage |
| Processing | Python | 3.10+ | Core Logic |

## Migration from Qt Desktop App

### What Changed
- **UI**: Qt widgets → PHP HTML templates
- **Data Storage**: SQLite per case → PostgreSQL + MinIO
- **Processing**: Synchronous → Asynchronous (Celery)
- **Access**: Single user desktop → Multi-user web
- **Authentication**: None → Keycloak OIDC

### What Stayed the Same
- Core PDF parsing logic (fnb_statement_to_sqlite.py)
- Transaction analysis algorithms
- Account categorization rules
- Network graph generation
- AI chat integration (Ollama)

## Maintenance & Operations

### Deployment Model
- PHP: Deploy to `/var/www/gismartanalytics/public`
- Python: Systemd services for FastAPI + Celery
- Database: PostgreSQL migrations
- Configuration: Environment files per server

### Monitoring Points
- Keycloak login success/failure
- PHP application errors
- Python API response times
- Celery task queue depth
- Celery worker health
- MinIO storage capacity
- PostgreSQL query performance

### Backup Requirements
- PostgreSQL database (daily)
- MinIO objects (according to retention policy)
- Application configuration files
- Keycloak realm exports (periodic)

## Future Enhancements

1. **Real-time Updates**: WebSocket for job progress
2. **Advanced Analytics**: More ML-powered insights
3. **Multi-tenancy**: Organizational isolation
4. **API Rate Limiting**: Protect against abuse
5. **Audit Trail**: Enhanced compliance logging
6. **Export Formats**: PDF, Excel, CSV reports
7. **Scheduled Jobs**: Recurring analysis tasks
8. **Webhook Integration**: External system notifications

# Aurex Architecture Documentation

## System Overview

Aurex is a three-tier web application for bank statement analysis with AI-powered insights.

## High-Level Architecture

```
┌─────────────────┐
│   Web Browser   │
└────────┬────────┘
         │ HTTP/HTTPS
         ▼
┌─────────────────────────────────┐
│      Apache Web Server          │
│  ┌──────────────────────────┐  │
│  │   PHP Frontend (MVC)     │  │
│  │  - Controllers           │  │
│  │  - Views                 │  │
│  │  - Session Management    │  │
│  └──────────┬───────────────┘  │
└─────────────┼───────────────────┘
              │ API Calls
              ▼
┌─────────────────────────────────┐
│  Python Backend (FastAPI)       │
│  ┌──────────────────────────┐  │
│  │  API Routers             │  │
│  │  - Cases                 │  │
│  │  - Processing            │  │
│  │  - Analysis              │  │
│  │  - Chat (AI)             │  │
│  └──────────┬───────────────┘  │
│  ┌──────────┴───────────────┐  │
│  │  Services                │  │
│  │  - PDF Processing        │  │
│  │  - Transaction Analysis  │  │
│  │  - AI Integration        │  │
│  └──────────┬───────────────┘  │
└─────────────┼───────────────────┘
              │
    ┌─────────┼─────────┐
    ▼         ▼         ▼
┌─────────┐ ┌───────┐ ┌─────────┐
│PostgreSQL│ │ Redis │ │ Ollama  │
│ Database│ │ Cache │ │   AI    │
└─────────┘ └───────┘ └─────────┘
```

## Component Details

### 1. PHP Frontend Layer

**Purpose**: User interface and session management

**Responsibilities**:
- Serve HTML pages
- Handle user authentication (OIDC)
- Manage sessions
- Route requests
- Proxy API calls to Python backend

**Technology Stack**:
- PHP 8.2+
- Apache with mod_rewrite
- Custom MVC framework

**Security**:
- OIDC authentication
- Session-based authorization
- CSRF protection
- XSS prevention

### 2. Python Backend Layer

**Purpose**: Business logic and data processing

**Responsibilities**:
- PDF processing and parsing
- Transaction extraction
- Data analysis and insights
- AI chat integration
- Background job processing
- Database operations

**Technology Stack**:
- Python 3.11+
- FastAPI framework
- SQLAlchemy ORM
- Celery for background tasks
- Redis for job queue

**Security**:
- API key authentication
- Input validation
- Rate limiting
- SQL injection prevention

### 3. Data Layer

**Components**:

**PostgreSQL Database**:
- Primary data store
- Transactional consistency
- Full-text search
- JSON support for flexible data

**Redis Cache**:
- Session storage
- Job queue for Celery
- Result caching
- Rate limiting

**File Storage**:
- PDF uploads
- SQLite case databases
- Generated reports

## Data Flow

### Case Processing Flow

1. **User uploads PDFs** (PHP Frontend)
   - Validates file types
   - Stores in upload directory
   - Creates case record

2. **Processing initiated** (PHP → Python API)
   - PHP calls `/api/processing/{case_id}/start`
   - Python queues background job
   - Returns job ID

3. **Background processing** (Celery Worker)
   - Extracts text from PDFs
   - Parses transactions
   - Stores in database
   - Updates progress

4. **Status polling** (PHP → Python API)
   - PHP polls `/api/processing/{case_id}/status`
   - Gets current progress
   - Updates UI

5. **Analysis ready** (Python → PHP)
   - Processing completes
   - Analysis data generated
   - User redirected to results

### AI Chat Flow

1. **User asks question** (Frontend)
   - Question submitted via form
   - Sent to Python backend

2. **Context retrieval** (Python)
   - Load case transactions
   - Get relevant statistics
   - Build context for AI

3. **AI processing** (Ollama)
   - Send context + question
   - Receive AI response
   - Store in database

4. **Response delivery** (Python → Frontend)
   - Return AI answer
   - Display in chat interface

## Security Architecture

### Authentication Flow (OIDC)

```
User → PHP → OIDC Provider
         ↓
    Token stored in session
         ↓
    User info cached
         ↓
    Access granted
```

### Authorization (RBAC)

**Roles**:
- `admin` - Full system access
- `analyst` - Case creation and analysis
- `viewer` - Read-only access

**Permissions**:
- `case:create`
- `case:read`
- `case:update`
- `case:delete`
- `case:process`

### API Security

**PHP → Python**:
- API key in `X-API-Key` header
- IP whitelist (optional)
- Rate limiting

**User → PHP**:
- Session cookies
- CSRF tokens
- HTTPS required

## Scalability

### Horizontal Scaling

**PHP Frontend**:
- Stateless design
- Load balancer ready
- Shared session storage (Redis)

**Python Backend**:
- Multiple API workers
- Load balanced
- Shared cache and queue

**Celery Workers**:
- Auto-scaling based on queue depth
- Distributed processing
- Task retry logic

### Performance Optimization

1. **Caching Strategy**:
   - Redis for frequently accessed data
   - Result caching for expensive queries
   - CDN for static assets

2. **Database Optimization**:
   - Indexed queries
   - Connection pooling
   - Query optimization

3. **Async Processing**:
   - Background jobs for long operations
   - Non-blocking API calls
   - WebSocket for real-time updates

## Deployment Architecture

### Production Setup

```
Internet
    ↓
Load Balancer (SSL Termination)
    ↓
    ├─ Apache (PHP) Server 1
    ├─ Apache (PHP) Server 2
    └─ Apache (PHP) Server 3
         ↓
    ├─ Python API Server 1
    ├─ Python API Server 2
    └─ Python API Server 3
         ↓
    ├─ Celery Worker 1
    ├─ Celery Worker 2
    └─ Celery Worker 3
         ↓
    ┌──────────────────┐
    │  PostgreSQL HA   │
    │  (Primary/Replica)│
    └──────────────────┘
         ↓
    ┌──────────────────┐
    │  Redis Cluster   │
    └──────────────────┘
```

### High Availability

- Database replication
- Redis Sentinel
- Load balancer health checks
- Automatic failover
- Rolling deployments

## Monitoring

### Metrics to Track

- API response times
- Processing job duration
- Database query performance
- Cache hit rates
- Error rates
- Active users

### Logging

- Application logs (structured JSON)
- Access logs
- Error logs
- Audit logs
- Performance metrics

## Disaster Recovery

1. **Database backups**:
   - Daily full backups
   - Continuous WAL archiving
   - Point-in-time recovery

2. **File backups**:
   - Incremental backups of uploads
   - Case database archives

3. **Recovery procedures**:
   - Documented restore process
   - Regular DR testing
   - RTO: 4 hours
   - RPO: 1 hour

## Technology Choices Rationale

### PHP for Frontend
- Familiar to existing team
- Mature OIDC libraries
- Easy deployment
- Good performance with opcache

### Python for Backend
- Existing codebase in Python
- Excellent ML/AI libraries
- FastAPI for async support
- Rich PDF processing ecosystem

### PostgreSQL
- ACID compliance
- JSON support
- Full-text search
- Proven reliability

### Redis
- Fast in-memory operations
- Pub/sub for real-time
- Celery integration
- Session storage

## Future Enhancements

- GraphQL API
- WebSocket for real-time updates
- Microservices architecture
- Kubernetes deployment
- Multi-tenancy support
- Advanced analytics dashboard

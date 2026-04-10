# Migration from Qt Desktop Application to Web Platform

## Overview

This document explains how the original Aurex Python/Qt desktop application has been transformed into a modern web-based platform while preserving its core functionality and processing logic.

## Original Qt Application Structure

### Components
- **UI Layer**: PySide6 Qt widgets (Welcome, CaseInfo, Progress, Analysis tabs)
- **Processing Layer**: PDF parsing, transaction extraction, AI chat
- **Data Layer**: SQLite database per case, JSON case metadata
- **Execution Model**: Single-user desktop application

### Key Files (Original)
```
aurex_bank_analyzer/
├── app.py                    # Main Qt application
├── ui/                       # Qt widgets
│   ├── welcome.py
│   ├── case_info.py
│   ├── progress.py
│   └── analysis.py
├── core/
│   ├── case_manager.py       # Case CRUD operations
│   ├── workers.py            # Processing threads
│   ├── data_access.py        # SQLite queries
│   └── adapters.py           # Script loading
└── cases/                    # Case data storage
    └── {case_id}/
        ├── case.json
        └── fnb_statements.db

Processing Scripts (Root):
├── fnb_statement_to_sqlite.py   # PDF parsing
├── fnb_chat_assistant-v2.py     # AI chat
└── account_analyzer.py          # Account analysis
```

## New Web Application Structure

### Architecture
- **Frontend**: PHP web application (192.168.1.66)
- **Backend**: Python FastAPI + Celery (192.168.1.90)
- **Authentication**: Keycloak SSO (192.168.1.59)
- **Storage**: PostgreSQL + MinIO
- **Execution Model**: Multi-user web platform

### New Structure
```
php-app/                      # Web frontend
├── public/                   # Apache DocumentRoot
├── src/
│   ├── Controllers/          # HTTP handlers
│   ├── Services/             # Business logic
│   ├── Repositories/         # Database access
│   ├── Middleware/           # Auth, CSRF
│   └── Views/                # HTML templates

python-backend/               # Processing backend
├── app/
│   ├── main.py              # FastAPI app
│   ├── api/                 # REST endpoints
│   ├── tasks/               # Celery tasks
│   ├── services/            # Business logic
│   └── legacy_logic/        # Migrated Qt code
│       ├── fnb_statement_to_sqlite.py
│       ├── fnb_chat_assistant-v2.py
│       └── account_analyzer.py

database/                    # PostgreSQL schema
docs/                        # Documentation
deploy/                      # Deployment configs
```

## Migration Mapping

### UI Components → PHP Pages

| Qt Component | Web Equivalent | Purpose |
|--------------|----------------|---------|
| WelcomeTab | /cases (list view) | Browse existing cases |
| CaseInfoTab | /cases/new | Create new case |
| ProgressTab | /jobs/{id} | Monitor processing progress |
| AnalysisTab (Chat) | /cases/{id}/chat | AI-powered chat |
| AnalysisTab (Network) | /cases/{id}/network | Network visualization |
| AnalysisTab (Insights) | /cases/{id}/insights | Financial insights |

### Data Storage Migration

| Qt Storage | Web Storage | Migration Notes |
|------------|-------------|-----------------|
| cases/{id}/case.json | PostgreSQL: `cases` table | Relational data with foreign keys |
| cases/{id}/fnb_statements.db | PostgreSQL: `transactions` table | Centralized database |
| Local PDF files | MinIO: `aurex-uploads` bucket | Object storage with versioning |
| N/A | MinIO: `aurex-results` bucket | Generated visualizations |
| N/A | MinIO: `aurex-exports` bucket | Download packages |

### Processing Flow Migration

#### Qt Desktop Flow
```
1. User clicks "Start Processing"
2. Qt creates ProcessingWorker thread
3. Worker synchronously processes PDFs
4. Updates progress via Qt signals
5. Saves to local SQLite
6. Displays results in Analysis tab
```

#### Web Flow
```
1. User clicks "Start Processing" (PHP)
2. PHP calls Python API: POST /api/process
3. Python creates Celery task
4. Returns job_id to PHP
5. PHP polls GET /api/jobs/{id}/status
6. Celery worker processes PDFs in background
7. Saves to PostgreSQL + MinIO
8. PHP displays results when job completes
```

### Code Reuse Strategy

#### Preserved As-Is
✅ **fnb_statement_to_sqlite.py**: Core PDF parsing logic  
✅ **fnb_chat_assistant-v2.py**: AI chat logic  
✅ **account_analyzer.py**: Account identification  
✅ **data_access.py**: Query patterns (adapted for PostgreSQL)  
✅ **Category classification rules**: Exact same logic  
✅ **Network graph generation**: Same algorithm  

#### Adapted
🔄 **case_manager.py** → `php-app/src/Repositories/CaseRepository.php` + PostgreSQL  
🔄 **workers.py** → `python-backend/app/tasks/processing.py` + Celery  
🔄 **SQLite queries** → PostgreSQL queries (via SQLAlchemy)  

#### Replaced
❌ **Qt UI components** → PHP HTML templates  
❌ **Local file selection** → Web file upload  
❌ **Qt signals/slots** → HTTP API calls  
❌ **QThread** → Celery workers  
❌ **Local storage** → MinIO object storage  

## Feature Parity

### ✅ Fully Migrated

- [x] Case creation and management
- [x] PDF file upload
- [x] Background processing
- [x] Transaction extraction
- [x] Category classification
- [x] Network graph generation
- [x] Insights generation
- [x] AI-powered chat
- [x] Progress monitoring
- [x] Results display

### ➕ New Features (Web-Only)

- [x] Multi-user access
- [x] Role-based permissions (Admin, Analyst, Client)
- [x] SSO authentication via Keycloak
- [x] Audit logging
- [x] Export downloads (PDF, CSV, ZIP)
- [x] Case sharing between users
- [x] API for external integrations

### 📝 Future Enhancements

- [ ] Real-time progress updates (WebSocket/SSE)
- [ ] Scheduled/recurring analysis
- [ ] Email notifications
- [ ] Advanced reporting templates
- [ ] Multi-bank support
- [ ] Mobile-responsive UI

## Data Migration Process

### For Existing Qt App Users

If you have existing cases in the Qt application and want to migrate them to the web platform:

#### Option 1: Re-import PDFs
1. Export your original PDF files from the case folder
2. Create a new case in the web application
3. Upload the PDFs through the web interface
4. Re-run processing

**Pros**: Clean start, benefits from new features  
**Cons**: Loses original case metadata and timestamps

#### Option 2: Database Migration Script
1. Use the migration script (to be created): `scripts/migrate_qt_cases.py`
2. Script will:
   - Read `cases/*/case.json` files
   - Read `cases/*/fnb_statements.db` SQLite files
   - Insert data into PostgreSQL
   - Upload PDFs to MinIO
   - Preserve timestamps and metadata

**Pros**: Preserves all data and history  
**Cons**: Requires script execution, technical knowledge

#### Option 3: Hybrid Approach
Keep the Qt app for old cases, use web app for new work.

## Authentication Migration

### Qt App (No Authentication)
- Single user on local machine
- No login required
- Full access to all cases

### Web App (Keycloak SSO)
- Multi-user environment
- Keycloak login required
- Role-based access control
- User assignment to cases

**Migration Note**: There is no "user" concept in Qt app. When migrating cases, assign them to a default admin user.

## Configuration Migration

### Qt App Configuration
- Hardcoded paths in Python code
- No external configuration
- Ollama endpoint embedded

### Web App Configuration
- Environment files (`.env`)
- Separate configs per server
- No secrets in code

**Example Qt → Web Config Mapping**:

| Qt Setting | Web Config | Location |
|------------|------------|----------|
| `cases_root` = `aurex_bank_analyzer/cases` | `DB_NAME=aurex_db` | PHP `.env` |
| Ollama at `localhost:11434` | `OLLAMA_ENDPOINT=http://192.168.1.90:11434` | Python `.env` |
| N/A | `KEYCLOAK_*` | PHP `.env` |
| N/A | `MINIO_*` | Both `.env` files |

## Performance Comparison

### Qt App
- **Startup**: Instant (local app)
- **Processing**: Synchronous, blocks UI during long jobs
- **Concurrent Cases**: One at a time
- **Scalability**: Single machine only

### Web App
- **Startup**: Minimal (page load)
- **Processing**: Asynchronous, UI stays responsive
- **Concurrent Cases**: Multiple users, multiple cases simultaneously
- **Scalability**: Can add more Celery workers, horizontal scaling

## Troubleshooting Migration Issues

### Issue: "Results look different between Qt and web app"

**Cause**: Rounding differences, timezone handling, or database precision.

**Solution**: 
1. Compare transaction counts
2. Verify date parsing (check year rollovers)
3. Check category classification rules (should be identical)

### Issue: "PDF parsing fails in web app but worked in Qt"

**Cause**: File encoding, path issues, or missing dependencies.

**Solution**:
1. Verify tesseract is installed on Python server
2. Check file permissions on temp directories
3. Ensure pdfplumber version matches
4. Review logs for specific errors

### Issue: "AI chat gives different answers"

**Cause**: Different Ollama model or version.

**Solution**:
1. Use same Ollama model as Qt app
2. Check Ollama endpoint configuration
3. Verify model is downloaded: `ollama list`

## Testing Migration

### Validation Checklist

- [ ] Upload same PDFs to both Qt and web app
- [ ] Compare transaction counts (should match exactly)
- [ ] Compare date ranges (should match)
- [ ] Compare category breakdowns (should match)
- [ ] Test AI chat with same questions
- [ ] Verify network graph nodes and edges match
- [ ] Check export file contents

### Test Cases

1. **Single Month Statement**: Simple PDF with one month of data
2. **Year Rollover**: December → January statement
3. **Scanned PDF**: OCR fallback test
4. **Large File**: 100+ page statement
5. **Multiple Accounts**: Different account numbers in filenames
6. **Duplicate Upload**: Re-upload same file (should be detected)

## Rollback Plan

If migration issues occur:

1. **Keep Qt App Available**: Don't delete it immediately
2. **Parallel Operation**: Run both systems during transition
3. **Data Export**: Export critical data before full cutover
4. **Backup**: Maintain Qt app backups for 6 months

## Training and Adoption

### For Qt App Users

**Key Differences to Learn**:
1. Login required (Keycloak credentials)
2. Cases must be created before upload
3. Processing runs in background (check "Jobs" page)
4. Download exports instead of accessing local files
5. Share cases with colleagues

**Training Recommendations**:
- 1-hour hands-on session
- Side-by-side comparison demo
- Written quick start guide
- Video tutorials for key workflows

## Support During Migration

### Phase 1 (Weeks 1-2): Parallel Operation
- Both Qt and web app available
- Users test web app with non-critical cases
- Gather feedback

### Phase 2 (Weeks 3-4): Gradual Transition
- New cases created in web app only
- Qt app available for reference
- Data migration support

### Phase 3 (Week 5+): Full Cutover
- Qt app retired
- All work in web app
- Historical data migrated

## Success Metrics

Migration is complete when:
- [ ] 100% of users can log in via Keycloak
- [ ] All critical cases migrated to PostgreSQL
- [ ] Processing accuracy matches Qt app
- [ ] No blocking bugs in web UI
- [ ] User training completed
- [ ] Documentation finalized
- [ ] Support procedures established

## Conclusion

This migration transforms Aurex from a single-user desktop tool into a scalable, multi-user web platform while preserving the battle-tested processing logic that makes it valuable. The phased approach minimizes risk and ensures continuity of service.

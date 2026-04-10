# Aurex Database Documentation

## Overview

Aurex uses PostgreSQL as its primary application database. This document explains the database schema, design decisions, and usage patterns.

## Connection Information

- **Host**: Application Server (192.168.1.66)
- **Port**: 5432 (default PostgreSQL port)
- **Database**: `aurex_db`
- **User**: `aurex_app_user` (application) / `aurex_admin` (administration)

**Environment Configuration:**
Connection details are stored in `.env` files and never hardcoded.

```env
DB_HOST=192.168.1.66
DB_PORT=5432
DB_NAME=aurex_db
DB_USER=aurex_app_user
DB_PASSWORD=<stored_securely>
```

## Schema Overview

The database is organized into logical sections:

1. **Users & Authentication**: User accounts and roles
2. **Cases**: Investigation workspaces
3. **Uploads & Files**: File metadata (files stored in MinIO)
4. **Processing Jobs**: Background task tracking
5. **Transactions & Analysis**: Extracted data and insights
6. **Exports**: Generated reports and downloads
7. **Audit & Logging**: Security and debugging logs
8. **Settings**: Application configuration

## Table Relationships

```
users
  ├── user_roles (many roles per user)
  ├── cases (created_by)
  ├── case_access (access control)
  ├── uploads (uploaded_by)
  ├── processing_jobs (started_by)
  ├── exports (created_by)
  └── audit_logs (actions)

cases
  ├── case_access (who can access)
  ├── uploads (files in case)
  ├── processing_jobs (jobs for case)
  ├── transactions (extracted data)
  ├── insights (generated insights)
  ├── network_graphs (visualizations)
  └── exports (reports)

uploads
  └── transactions (transactions from file)

processing_jobs
  └── job_events (detailed logs)
```

## Table Descriptions

### users

**Purpose**: Maps Keycloak authenticated users to local application records.

**Why it exists**: While Keycloak handles authentication, we need local user records to:
- Associate data with specific users
- Store application-specific preferences
- Track user activity
- Provide faster queries without hitting Keycloak API

**Key Fields**:
- `keycloak_sub`: Unique identifier from Keycloak JWT (e.g., "f47ac10b-58cc-4372-a567-0e02b2c3d479")
- `username`: Display name
- `email`: Contact email
- `is_active`: Soft delete / account suspension flag

**Relations**:
- One user has many roles (`user_roles`)
- One user creates many cases (`cases.created_by`)
- One user has access to many cases (`case_access`)

### user_roles

**Purpose**: Assign roles to users for authorization.

**Roles**:
- `admin`: Full system access
- `analyst`: Can create cases, upload, process, analyze
- `client` / `viewer`: Read-only access to assigned cases

**Why it exists**: Keycloak provides roles via JWT, but we mirror them locally for:
- Faster authorization checks
- Audit trail of role assignments
- Flexibility for app-specific permissions

### cases

**Purpose**: Container for bank statement analysis investigations.

**Why it exists**: Each case represents an independent investigation with its own files, jobs, and results.

**Key Fields**:
- `case_name`: Human-readable identifier
- `evidence_number`: External tracking reference
- `status`: Lifecycle stage (created → processing → completed)
- `timezone`: For date/time interpretation
- `date_range_start/end`: Span of transactions in case

**Statuses**:
- `created`: Case initialized, no processing yet
- `processing`: Active job running
- `completed`: All processing done
- `error`: Processing failed
- `cancelled`: User-cancelled
- `archived`: Completed and archived

### case_access

**Purpose**: Control which users can access specific cases.

**Why it exists**: Not all users should see all cases. This provides:
- Privacy between investigations
- Multi-tenant support
- Delegation (share case with colleague)

**Access Levels**:
- `owner`: Full control, can delete case
- `editor`: Can upload, process, export
- `viewer`: Read-only access

### uploads

**Purpose**: Track uploaded PDF files with metadata.

**Why it exists**: Files are stored in MinIO, but we need metadata for:
- Display file lists
- Prevent duplicate uploads (via `file_hash`)
- Track processing status per file
- Link files to transactions

**Key Fields**:
- `file_hash`: SHA256 for deduplication
- `minio_bucket`, `minio_object_key`: Location in MinIO
- `upload_status`: Lifecycle tracking
- `file_size_bytes`: For quota management

**Design Decision**: We store file **metadata** in PostgreSQL and file **content** in MinIO. This separates concerns and prevents database bloat.

### processing_jobs

**Purpose**: Track background tasks executed by Celery workers.

**Why it exists**: Processing can take minutes/hours. This table:
- Provides job status for UI polling
- Stores progress for partial completion tracking
- Logs errors for debugging
- Links Celery tasks to cases

**Key Fields**:
- `celery_task_id`: Maps to Celery task
- `status`: Current state (queued → started → completed/failed)
- `progress_current/total`: For progress bars
- `result_data`: Structured JSON results

**Statuses**:
- `queued`: Task submitted to Celery
- `started`: Worker picked up task
- `processing`: Active execution
- `completed`: Success
- `failed`: Error occurred
- `cancelled`: User-requested cancellation
- `retry`: Automatic retry in progress

### job_events

**Purpose**: Detailed event log for job execution.

**Why it exists**: For debugging and transparency:
- Each progress update creates an event
- Errors log detailed tracebacks
- User can see "PDF 3 of 10 processed" type messages

**Event Types**:
- `started`: Job began
- `progress`: Update event
- `completed`: Job finished
- `error`: Error occurred
- `info`: Informational message

### transactions

**Purpose**: Normalized bank transactions extracted from PDFs.

**Why it exists**: Core data for analysis. Migrated from SQLite-per-case to centralized PostgreSQL for:
- Unified querying across cases
- Better performance with indexes
- Relationships to other tables
- Web-friendly data access

**Key Fields**:
- `txn_date`: Transaction date
- `description`: Raw transaction description
- `debit_amount/credit_amount`: Money flow
- `category`: Auto-assigned category (e.g., "Fuel", "Retail")
- `counterparty`: Extracted entity name

**Design Decision**: Each transaction links to both `case_id` and `upload_id` for traceability.

### insights

**Purpose**: Pre-computed analysis results (category breakdowns, trends, etc.).

**Why it exists**: Calculating insights on-the-fly for large datasets is slow. Pre-computing and caching:
- Speeds up dashboard loading
- Reduces database load
- Enables complex analysis without real-time computation

**Insight Types**:
- `category_breakdown`: Spending by category
- `monthly_trend`: Month-over-month analysis
- `top_counterparties`: Most frequent entities
- `outlier_detection`: Unusual transactions

**Design**: Results stored as JSONB for flexibility. Visualizations (charts) stored in MinIO, referenced here.

### network_graphs

**Purpose**: Pre-computed relationship graphs for visualization.

**Why it exists**: Generating network graphs from transactions is expensive. Pre-computing:
- Enables instant visualization loading
- Consistent layout between views
- Supports large transaction sets

**Structure**:
- `nodes`: JSON array of entities (accounts, counterparties)
- `edges`: JSON array of relationships (transaction flows)
- `layout_data`: Pre-computed positions for rendering

### exports

**Purpose**: Track generated export packages (reports, CSVs, etc.).

**Why it exists**:
- Users need downloadable outputs
- Track what was exported for audit
- Auto-delete old exports with `expires_at`
- Count downloads for analytics

**Export Types**:
- `full_report`: Complete case analysis (ZIP)
- `transactions_csv`: Raw transaction data
- `insights_pdf`: Summary report
- `network_graph`: Visualization export

### audit_logs

**Purpose**: Security and compliance audit trail.

**Why it exists**: Regulatory and security requirements. Tracks:
- Who logged in when
- Who created/accessed cases
- Who downloaded sensitive data
- What actions were taken

**Action Types**:
- `login`, `logout`
- `create_case`, `update_case`, `delete_case`
- `upload_file`, `start_job`
- `download_export`, `view_case`

**Design**: Immutable log (no updates or deletes). Retention policy applied separately.

### api_request_logs

**Purpose**: Log PHP → Python API calls for debugging.

**Why it exists**: When issues occur, we need to know:
- Which endpoints were called
- What parameters were sent
- Response times
- Error messages

**Use Cases**:
- Performance monitoring
- Debugging integration issues
- API usage analytics

### app_settings

**Purpose**: System-wide configuration stored in database.

**Why it exists**: Some settings need to be:
- Editable without code deploys
- Different per environment
- Accessible to both PHP and Python

**Examples**:
- `max_upload_size_mb`
- `session_timeout_minutes`
- `enable_ai_chat`
- `ollama_endpoint`

**Design**: `is_public` flag controls whether non-admin users can read setting.

## Views

### vw_users_with_roles

Combines users with their assigned roles for easier querying.

```sql
SELECT * FROM vw_users_with_roles WHERE 'admin' = ANY(roles);
```

### vw_case_summary

Case list with computed statistics (upload count, job count, etc.).

Used for dashboard and case listing pages.

### vw_active_jobs

Currently running jobs with real-time progress percentage.

Used for job monitoring page.

## Indexes

All foreign keys are indexed for join performance.

Additional indexes:
- `users.keycloak_sub`: Fast authentication lookup
- `uploads.file_hash`: Deduplication checks
- `transactions.txn_date`: Date range queries
- `audit_logs.occurred_at`: Recent activity queries

## Migrations

### Initial Setup

```bash
psql -U postgres -c "CREATE DATABASE aurex_db;"
psql -U postgres -d aurex_db -f database/schema.sql
```

### Future Migrations

Migrations are stored in `database/migrations/` with timestamp prefixes:

```
database/migrations/
  001_initial_schema.sql
  002_add_insights_expiry.sql
  003_add_user_preferences.sql
```

**Migration Pattern**:
1. Create new `.sql` file with changes
2. Test on development database
3. Apply to production with transaction:
   ```sql
   BEGIN;
   -- migration statements
   COMMIT;
   ```

## Backup and Restore

### Backup

```bash
# Full database dump
pg_dump -U aurex_admin -d aurex_db -F c -f aurex_backup_$(date +%Y%m%d).dump

# Schema only
pg_dump -U aurex_admin -d aurex_db --schema-only -f schema_backup.sql

# Data only
pg_dump -U aurex_admin -d aurex_db --data-only -f data_backup.sql
```

### Restore

```bash
pg_restore -U aurex_admin -d aurex_db -c aurex_backup.dump
```

### Scheduled Backups

Configure via cron:
```bash
0 2 * * * /usr/local/bin/backup_aurex_db.sh
```

## Performance Tuning

### Query Optimization

Most common queries:
1. **Case list for user**: Uses `vw_case_summary` + `case_access`
2. **Job status polling**: Uses `processing_jobs` index on `id` and `status`
3. **Transaction search**: Uses indexes on `case_id`, `txn_date`, `category`

### Connection Pooling

PHP uses persistent connections via PDO.

Recommended PostgreSQL settings:
```
max_connections = 100
shared_buffers = 256MB
effective_cache_size = 1GB
```

### Vacuuming

Enable auto-vacuum for busy tables:
```sql
ALTER TABLE audit_logs SET (autovacuum_vacuum_scale_factor = 0.05);
ALTER TABLE job_events SET (autovacuum_vacuum_scale_factor = 0.1);
```

## Security

### User Permissions

```sql
-- Application user (read/write access)
CREATE USER aurex_app_user WITH PASSWORD '<secure_password>';
GRANT CONNECT ON DATABASE aurex_db TO aurex_app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO aurex_app_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO aurex_app_user;

-- Admin user (full access)
CREATE USER aurex_admin WITH PASSWORD '<admin_password>';
GRANT ALL PRIVILEGES ON DATABASE aurex_db TO aurex_admin;
```

### Connection Security

- Use SSL/TLS for connections
- Restrict `pg_hba.conf` to application server IP
- Never expose PostgreSQL to public internet

Example `pg_hba.conf`:
```
# Allow app server only
host    aurex_db    aurex_app_user    192.168.1.66/32    md5
```

## Monitoring

### Query Performance

```sql
-- Slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Table sizes
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Active Connections

```sql
SELECT count(*) FROM pg_stat_activity WHERE datname = 'aurex_db';
```

## Troubleshooting

### Common Issues

**Issue**: Slow case list query
- **Solution**: Ensure `case_access` index exists, consider caching in Redis

**Issue**: Job status not updating
- **Solution**: Check Celery worker connectivity, verify `celery_task_id` matches

**Issue**: Duplicate file uploads
- **Solution**: Check `file_hash` uniqueness constraint, verify SHA256 calculation

**Issue**: Foreign key constraint violations
- **Solution**: Ensure related records exist before insert, use transactions

## Data Retention

Recommended retention policies:

- **audit_logs**: 2 years
- **api_request_logs**: 90 days
- **job_events**: 1 year
- **exports**: 30 days (auto-expire via `expires_at`)

Cleanup script example:
```sql
DELETE FROM audit_logs WHERE occurred_at < NOW() - INTERVAL '2 years';
DELETE FROM api_request_logs WHERE requested_at < NOW() - INTERVAL '90 days';
DELETE FROM exports WHERE expires_at < NOW();
```

## Schema Version

**Current Version**: 1.0.0  
**Last Updated**: 2026-04-10  
**Compatible With**: Aurex Web Application v1.0.0

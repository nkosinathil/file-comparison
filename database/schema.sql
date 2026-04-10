-- Aurex Web Application - PostgreSQL Schema
-- Version: 1.0.0
-- Description: Complete database schema for the Aurex bank statement analysis platform

-- Enable UUID extension for generating unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- USERS AND AUTHENTICATION
-- =============================================================================

-- Users table: Maps Keycloak users to local application records
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keycloak_sub VARCHAR(255) UNIQUE NOT NULL,  -- Keycloak subject identifier
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);

CREATE INDEX idx_users_keycloak_sub ON users(keycloak_sub);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);

COMMENT ON TABLE users IS 'Application users mapped from Keycloak authentication';
COMMENT ON COLUMN users.keycloak_sub IS 'Keycloak subject identifier from JWT token';

-- User roles table: Store role assignments (Admin, Analyst, Client/Viewer)
CREATE TABLE user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_name VARCHAR(50) NOT NULL CHECK (role_name IN ('admin', 'analyst', 'client', 'viewer')),
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, role_name)
);

CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_name ON user_roles(role_name);

COMMENT ON TABLE user_roles IS 'Role assignments for users';

-- =============================================================================
-- CASES
-- =============================================================================

-- Cases table: Investigation cases or workspaces
CREATE TABLE cases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_name VARCHAR(255) NOT NULL,
    evidence_number VARCHAR(255),
    case_description TEXT,
    timezone VARCHAR(50) DEFAULT 'UTC',
    status VARCHAR(50) DEFAULT 'created' CHECK (status IN ('created', 'processing', 'completed', 'error', 'cancelled', 'archived')),
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    total_files INTEGER DEFAULT 0,
    processed_files INTEGER DEFAULT 0,
    total_transactions INTEGER DEFAULT 0,
    date_range_start DATE,
    date_range_end DATE
);

CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_created_by ON cases(created_by);
CREATE INDEX idx_cases_created_at ON cases(created_at DESC);

COMMENT ON TABLE cases IS 'Investigation cases containing bank statement analysis';
COMMENT ON COLUMN cases.evidence_number IS 'External reference or evidence tracking number';

-- Case access control: Who can access which cases
CREATE TABLE case_access (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    access_level VARCHAR(50) DEFAULT 'viewer' CHECK (access_level IN ('owner', 'editor', 'viewer')),
    granted_by UUID REFERENCES users(id),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(case_id, user_id)
);

CREATE INDEX idx_case_access_case_id ON case_access(case_id);
CREATE INDEX idx_case_access_user_id ON case_access(user_id);

COMMENT ON TABLE case_access IS 'Controls which users can access specific cases';

-- =============================================================================
-- UPLOADS AND FILES
-- =============================================================================

-- Uploads table: Tracks uploaded files stored in MinIO
CREATE TABLE uploads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    uploaded_by UUID NOT NULL REFERENCES users(id),
    original_filename VARCHAR(255) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    file_hash VARCHAR(64) NOT NULL,  -- SHA256
    mime_type VARCHAR(100),
    minio_bucket VARCHAR(255) NOT NULL,
    minio_object_key VARCHAR(500) NOT NULL,
    upload_status VARCHAR(50) DEFAULT 'uploaded' CHECK (upload_status IN ('uploading', 'uploaded', 'validated', 'processing', 'processed', 'error')),
    validation_errors TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

CREATE INDEX idx_uploads_case_id ON uploads(case_id);
CREATE INDEX idx_uploads_file_hash ON uploads(file_hash);
CREATE INDEX idx_uploads_status ON uploads(upload_status);
CREATE UNIQUE INDEX idx_uploads_minio_location ON uploads(minio_bucket, minio_object_key);

COMMENT ON TABLE uploads IS 'Uploaded files stored in MinIO with metadata';
COMMENT ON COLUMN uploads.file_hash IS 'SHA256 hash for deduplication and integrity';

-- =============================================================================
-- PROCESSING JOBS
-- =============================================================================

-- Processing jobs table: Background tasks executed by Celery
CREATE TABLE processing_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    job_type VARCHAR(100) NOT NULL,  -- e.g., 'parse_statements', 'generate_insights', 'export_results'
    celery_task_id VARCHAR(255) UNIQUE,
    status VARCHAR(50) DEFAULT 'queued' CHECK (status IN ('queued', 'started', 'processing', 'completed', 'failed', 'cancelled', 'retry')),
    progress_current INTEGER DEFAULT 0,
    progress_total INTEGER DEFAULT 0,
    progress_message TEXT,
    started_by UUID NOT NULL REFERENCES users(id),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    error_traceback TEXT,
    retry_count INTEGER DEFAULT 0,
    result_data JSONB  -- Store structured results
);

CREATE INDEX idx_jobs_case_id ON processing_jobs(case_id);
CREATE INDEX idx_jobs_celery_task_id ON processing_jobs(celery_task_id);
CREATE INDEX idx_jobs_status ON processing_jobs(status);
CREATE INDEX idx_jobs_started_at ON processing_jobs(started_at DESC);

COMMENT ON TABLE processing_jobs IS 'Background processing jobs managed by Celery';
COMMENT ON COLUMN processing_jobs.celery_task_id IS 'Celery task identifier for tracking';

-- Job events: Detailed event log for job execution
CREATE TABLE job_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES processing_jobs(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,  -- 'started', 'progress', 'completed', 'error', 'info'
    event_message TEXT,
    event_data JSONB,
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_job_events_job_id ON job_events(job_id);
CREATE INDEX idx_job_events_occurred_at ON job_events(occurred_at DESC);

COMMENT ON TABLE job_events IS 'Detailed event log for job execution and debugging';

-- =============================================================================
-- TRANSACTIONS AND ANALYSIS RESULTS
-- =============================================================================

-- Transactions table: Extracted bank transactions
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    upload_id UUID NOT NULL REFERENCES uploads(id) ON DELETE CASCADE,
    txn_date DATE NOT NULL,
    description TEXT,
    debit_amount DECIMAL(15,2),
    credit_amount DECIMAL(15,2),
    balance DECIMAL(15,2),
    category VARCHAR(100),  -- Auto-categorized
    counterparty VARCHAR(255),  -- Extracted from description
    source_file VARCHAR(255),
    file_hash VARCHAR(64),
    statement_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transactions_case_id ON transactions(case_id);
CREATE INDEX idx_transactions_upload_id ON transactions(upload_id);
CREATE INDEX idx_transactions_txn_date ON transactions(txn_date);
CREATE INDEX idx_transactions_category ON transactions(category);

COMMENT ON TABLE transactions IS 'Extracted and normalized bank transactions';

-- Insights table: Generated analysis insights
CREATE TABLE insights (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    insight_type VARCHAR(100) NOT NULL,  -- 'category_breakdown', 'monthly_trend', 'top_counterparties'
    insight_data JSONB NOT NULL,
    minio_bucket VARCHAR(255),  -- For visualizations
    minio_object_key VARCHAR(500),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP  -- Optional TTL for cached insights
);

CREATE INDEX idx_insights_case_id ON insights(case_id);
CREATE INDEX idx_insights_type ON insights(insight_type);
CREATE INDEX idx_insights_generated_at ON insights(generated_at DESC);

COMMENT ON TABLE insights IS 'Pre-computed analysis insights and visualizations';

-- Network graph data: Relationship graphs
CREATE TABLE network_graphs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    graph_type VARCHAR(50) DEFAULT 'transaction_flow',
    nodes JSONB NOT NULL,
    edges JSONB NOT NULL,
    layout_data JSONB,  -- Pre-computed layout for faster rendering
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_network_graphs_case_id ON network_graphs(case_id);

COMMENT ON TABLE network_graphs IS 'Pre-computed network relationship graphs';

-- =============================================================================
-- EXPORTS
-- =============================================================================

-- Exports table: Generated export packages
CREATE TABLE exports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    case_id UUID NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    export_type VARCHAR(100) NOT NULL,  -- 'full_report', 'transactions_csv', 'insights_pdf'
    export_format VARCHAR(50) NOT NULL,  -- 'zip', 'pdf', 'csv', 'xlsx'
    file_size_bytes BIGINT,
    minio_bucket VARCHAR(255) NOT NULL,
    minio_object_key VARCHAR(500) NOT NULL,
    created_by UUID NOT NULL REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,  -- Auto-delete old exports
    download_count INTEGER DEFAULT 0,
    last_downloaded_at TIMESTAMP
);

CREATE INDEX idx_exports_case_id ON exports(case_id);
CREATE INDEX idx_exports_created_at ON exports(created_at DESC);
CREATE INDEX idx_exports_expires_at ON exports(expires_at);

COMMENT ON TABLE exports IS 'Generated export packages for download';

-- =============================================================================
-- AUDIT AND LOGGING
-- =============================================================================

-- Audit logs: Track important user actions
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    action_type VARCHAR(100) NOT NULL,  -- 'login', 'create_case', 'upload_file', 'start_job', 'download_export'
    resource_type VARCHAR(50),  -- 'case', 'upload', 'job', 'export'
    resource_id UUID,
    action_details JSONB,
    ip_address INET,
    user_agent TEXT,
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action_type ON audit_logs(action_type);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_occurred_at ON audit_logs(occurred_at DESC);

COMMENT ON TABLE audit_logs IS 'Audit trail for compliance and security';

-- API request logs: Track API calls from PHP to Python backend
CREATE TABLE api_request_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    endpoint VARCHAR(255) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    request_params JSONB,
    response_status INTEGER,
    response_time_ms INTEGER,
    error_message TEXT,
    requested_by UUID REFERENCES users(id) ON DELETE SET NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_logs_endpoint ON api_request_logs(endpoint);
CREATE INDEX idx_api_logs_requested_at ON api_request_logs(requested_at DESC);

COMMENT ON TABLE api_request_logs IS 'Log of Python API calls for debugging and monitoring';

-- =============================================================================
-- APPLICATION SETTINGS
-- =============================================================================

-- App settings: System-wide configuration
CREATE TABLE app_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    setting_key VARCHAR(255) UNIQUE NOT NULL,
    setting_value TEXT,
    setting_type VARCHAR(50) DEFAULT 'string' CHECK (setting_type IN ('string', 'integer', 'boolean', 'json')),
    description TEXT,
    is_public BOOLEAN DEFAULT false,  -- Can non-admin users read this?
    updated_by UUID REFERENCES users(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_app_settings_key ON app_settings(setting_key);

COMMENT ON TABLE app_settings IS 'System-wide configuration settings';

-- Insert default settings
INSERT INTO app_settings (setting_key, setting_value, setting_type, description, is_public) VALUES
('app_name', 'Aurex', 'string', 'Application display name', true),
('app_version', '1.0.0', 'string', 'Current application version', true),
('max_upload_size_mb', '100', 'integer', 'Maximum file upload size in megabytes', false),
('session_timeout_minutes', '60', 'integer', 'User session timeout', false),
('enable_ai_chat', 'true', 'boolean', 'Enable AI chat feature', false),
('ollama_endpoint', 'http://localhost:11434', 'string', 'Ollama API endpoint for AI chat', false);

-- =============================================================================
-- FUNCTIONS AND TRIGGERS
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cases_updated_at BEFORE UPDATE ON cases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_settings_updated_at BEFORE UPDATE ON app_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- VIEWS
-- =============================================================================

-- View: User summary with roles
CREATE VIEW vw_users_with_roles AS
SELECT 
    u.id,
    u.keycloak_sub,
    u.username,
    u.email,
    u.full_name,
    u.is_active,
    u.last_login_at,
    u.created_at,
    ARRAY_AGG(ur.role_name) FILTER (WHERE ur.role_name IS NOT NULL) AS roles
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
GROUP BY u.id, u.keycloak_sub, u.username, u.email, u.full_name, u.is_active, u.last_login_at, u.created_at;

-- View: Case summary with statistics
CREATE VIEW vw_case_summary AS
SELECT 
    c.id,
    c.case_name,
    c.evidence_number,
    c.status,
    c.created_by,
    u.username AS created_by_username,
    c.created_at,
    c.updated_at,
    c.total_files,
    c.processed_files,
    c.total_transactions,
    c.date_range_start,
    c.date_range_end,
    COUNT(DISTINCT up.id) AS upload_count,
    COUNT(DISTINCT j.id) AS job_count,
    SUM(CASE WHEN j.status = 'completed' THEN 1 ELSE 0 END) AS completed_jobs
FROM cases c
LEFT JOIN users u ON c.created_by = u.id
LEFT JOIN uploads up ON c.id = up.case_id
LEFT JOIN processing_jobs j ON c.id = j.case_id
GROUP BY c.id, c.case_name, c.evidence_number, c.status, c.created_by, u.username, 
         c.created_at, c.updated_at, c.total_files, c.processed_files, c.total_transactions,
         c.date_range_start, c.date_range_end;

-- View: Active jobs with progress
CREATE VIEW vw_active_jobs AS
SELECT 
    j.id,
    j.case_id,
    c.case_name,
    j.job_type,
    j.status,
    j.progress_current,
    j.progress_total,
    CASE 
        WHEN j.progress_total > 0 THEN ROUND((j.progress_current::NUMERIC / j.progress_total::NUMERIC) * 100, 2)
        ELSE 0 
    END AS progress_percentage,
    j.progress_message,
    j.started_at,
    u.username AS started_by_username,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - j.started_at)) AS running_seconds
FROM processing_jobs j
LEFT JOIN cases c ON j.case_id = c.id
LEFT JOIN users u ON j.started_by = u.id
WHERE j.status IN ('queued', 'started', 'processing');

-- =============================================================================
-- PERMISSIONS
-- =============================================================================

-- Grant permissions (adjust usernames as needed)
-- Example: GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO aurex_app_user;
-- Example: GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO aurex_app_user;

COMMENT ON SCHEMA public IS 'Aurex web application database schema v1.0.0';

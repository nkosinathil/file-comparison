-- Aurex Database Schema Migration
-- Version: 1.0.0
-- Description: Initial schema for Aurex web application

-- Cases table
CREATE TABLE IF NOT EXISTS cases (
    id VARCHAR(64) PRIMARY KEY,
    case_name VARCHAR(255) NOT NULL,
    evidence_number VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'UTC',
    status VARCHAR(50) DEFAULT 'pending',
    
    input_folder TEXT,
    output_folder TEXT,
    db_path TEXT,
    
    processed_files INTEGER DEFAULT 0,
    total_files INTEGER DEFAULT 0,
    total_transactions INTEGER DEFAULT 0,
    date_range VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cases_status ON cases(status);
CREATE INDEX idx_cases_created_at ON cases(created_at);


-- Processing logs table
CREATE TABLE IF NOT EXISTS processing_logs (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(64) REFERENCES cases(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20),
    message TEXT
);

CREATE INDEX idx_processing_logs_case_id ON processing_logs(case_id);
CREATE INDEX idx_processing_logs_timestamp ON processing_logs(timestamp);


-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(64) REFERENCES cases(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    question TEXT NOT NULL,
    answer TEXT,
    model VARCHAR(100)
);

CREATE INDEX idx_chat_messages_case_id ON chat_messages(case_id);
CREATE INDEX idx_chat_messages_timestamp ON chat_messages(timestamp);


-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(64) REFERENCES cases(id) ON DELETE CASCADE,
    
    account_number VARCHAR(50),
    transaction_date TIMESTAMP,
    description TEXT,
    amount NUMERIC(15, 2),
    balance NUMERIC(15, 2),
    transaction_type VARCHAR(50),
    category VARCHAR(100),
    counterparty VARCHAR(255),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transactions_case_id ON transactions(case_id);
CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_type ON transactions(transaction_type);
CREATE INDEX idx_transactions_category ON transactions(category);


-- Users table (for OIDC integration)
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(64) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'analyst',
    oidc_sub VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_oidc_sub ON users(oidc_sub);


-- Case permissions table (RBAC)
CREATE TABLE IF NOT EXISTS case_permissions (
    id SERIAL PRIMARY KEY,
    case_id VARCHAR(64) REFERENCES cases(id) ON DELETE CASCADE,
    user_id VARCHAR(64) REFERENCES users(id) ON DELETE CASCADE,
    permission VARCHAR(50) DEFAULT 'read',
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_case_permissions_case_id ON case_permissions(case_id);
CREATE INDEX idx_case_permissions_user_id ON case_permissions(user_id);
CREATE UNIQUE INDEX idx_case_permissions_unique ON case_permissions(case_id, user_id);

-- PR Agent Database Schema
-- Initial migration: core tables for PR Agent

CREATE EXTENSION IF NOT EXISTS vector;

-- Repositories table: tracks all discovered repositories
CREATE TABLE IF NOT EXISTS repositories (
    id SERIAL PRIMARY KEY,
    org VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    github_url TEXT NOT NULL UNIQUE,
    default_branch VARCHAR(100) DEFAULT 'main',
    language VARCHAR(50),
    repo_type VARCHAR(50),
    excluded BOOLEAN DEFAULT FALSE,
    last_indexed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_repositories_org ON repositories(org);
CREATE INDEX IF NOT EXISTS idx_repositories_excluded ON repositories(excluded);

-- Code chunks: indexed code snippets with embeddings for RAG
CREATE TABLE IF NOT EXISTS code_chunks (
    id SERIAL PRIMARY KEY,
    repository_id INT REFERENCES repositories(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    chunk_type VARCHAR(50),
    name VARCHAR(255),
    content TEXT NOT NULL,
    start_line INT,
    end_line INT,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repository_id, file_path, start_line, end_line)
);

CREATE INDEX IF NOT EXISTS idx_code_chunks_repo ON code_chunks(repository_id);
CREATE INDEX IF NOT EXISTS idx_code_chunks_file ON code_chunks(file_path);

-- HNSW index for vector similarity search
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE schemaname = 'public' AND indexname = 'code_chunks_embedding_hnsw'
    ) THEN
        CREATE INDEX code_chunks_embedding_hnsw
            ON code_chunks USING hnsw (embedding vector_cosine_ops)
            WITH (m=16, ef_construction=64);
    END IF;
END $$;

-- RepoSwarm analysis cache
CREATE TABLE IF NOT EXISTS repo_analysis_cache (
    id SERIAL PRIMARY KEY,
    repository_id INT REFERENCES repositories(id) ON DELETE CASCADE,
    repo_url TEXT NOT NULL,
    branch VARCHAR(255),
    repo_type VARCHAR(100),
    analysis_result JSONB,
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_commit_sha VARCHAR(40),
    UNIQUE(repository_id, branch)
);

CREATE INDEX IF NOT EXISTS idx_repo_analysis_repo ON repo_analysis_cache(repository_id);

-- Jira tickets: cached ticket data with embeddings
CREATE TABLE IF NOT EXISTS jira_tickets (
    id SERIAL PRIMARY KEY,
    ticket_key VARCHAR(50) NOT NULL UNIQUE,
    project_key VARCHAR(20) NOT NULL,
    summary TEXT,
    description TEXT,
    issue_type VARCHAR(50),
    status VARCHAR(50),
    priority VARCHAR(50),
    assignee VARCHAR(255),
    created_date TIMESTAMP,
    updated_date TIMESTAMP,
    embedding vector(1536),
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_jira_tickets_project ON jira_tickets(project_key);
CREATE INDEX IF NOT EXISTS idx_jira_tickets_status ON jira_tickets(status);

-- HNSW index for Jira ticket similarity search
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE schemaname = 'public' AND indexname = 'jira_tickets_embedding_hnsw'
    ) THEN
        CREATE INDEX jira_tickets_embedding_hnsw
            ON jira_tickets USING hnsw (embedding vector_cosine_ops)
            WITH (m=16, ef_construction=64);
    END IF;
END $$;

-- Internal NPM packages: @workiz packages from GitHub Packages
CREATE TABLE IF NOT EXISTS internal_packages (
    id SERIAL PRIMARY KEY,
    package_name VARCHAR(255) NOT NULL UNIQUE,
    latest_version VARCHAR(50),
    description TEXT,
    repository_id INT REFERENCES repositories(id),
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Custom review rules: configurable review rules
CREATE TABLE IF NOT EXISTS review_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    rule_type VARCHAR(50) NOT NULL,
    pattern TEXT,
    severity VARCHAR(20) DEFAULT 'warning',
    enabled BOOLEAN DEFAULT TRUE,
    config JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PR review history: audit trail of reviews
CREATE TABLE IF NOT EXISTS review_history (
    id SERIAL PRIMARY KEY,
    repository_id INT REFERENCES repositories(id),
    pr_number INT NOT NULL,
    pr_url TEXT,
    pr_title TEXT,
    author VARCHAR(255),
    review_result JSONB,
    issues_found INT DEFAULT 0,
    auto_fixes_applied INT DEFAULT 0,
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_review_history_repo ON review_history(repository_id);
CREATE INDEX IF NOT EXISTS idx_review_history_date ON review_history(reviewed_at);

-- GitHub activity: commits, PRs, reviews for Knowledge Assistant
CREATE TABLE IF NOT EXISTS github_activity (
    id SERIAL PRIMARY KEY,
    repository_id INT REFERENCES repositories(id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL,
    github_id VARCHAR(100),
    author VARCHAR(255),
    title TEXT,
    description TEXT,
    files_changed JSONB,
    created_at TIMESTAMP,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repository_id, activity_type, github_id)
);

CREATE INDEX IF NOT EXISTS idx_github_activity_repo ON github_activity(repository_id);
CREATE INDEX IF NOT EXISTS idx_github_activity_type ON github_activity(activity_type);
CREATE INDEX IF NOT EXISTS idx_github_activity_author ON github_activity(author);
CREATE INDEX IF NOT EXISTS idx_github_activity_date ON github_activity(created_at);

-- Knowledge Assistant conversation history
CREATE TABLE IF NOT EXISTS assistant_conversations (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    user_id VARCHAR(255),
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    context_used JSONB,
    tokens_used INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_assistant_conversations_session ON assistant_conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_assistant_conversations_user ON assistant_conversations(user_id);


-- Migration: 002_api_usage.sql
-- Description: Add API usage tracking table for cost monitoring

-- API Usage tracking for cost monitoring
CREATE TABLE IF NOT EXISTS api_usage (
    id SERIAL PRIMARY KEY,
    model VARCHAR(100) NOT NULL,
    input_tokens INT NOT NULL,
    output_tokens INT NOT NULL,
    latency_ms INT,
    estimated_cost DECIMAL(10, 6),
    pr_url TEXT,
    command VARCHAR(50),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_usage_model ON api_usage(model);
CREATE INDEX IF NOT EXISTS idx_api_usage_created ON api_usage(created_at);
CREATE INDEX IF NOT EXISTS idx_api_usage_pr_url ON api_usage(pr_url);

-- Review history tracking
CREATE TABLE IF NOT EXISTS review_history (
    id SERIAL PRIMARY KEY,
    pr_url TEXT NOT NULL,
    pr_number INT NOT NULL,
    repository VARCHAR(255) NOT NULL,
    pr_title TEXT,
    pr_author VARCHAR(255),
    review_type VARCHAR(50) NOT NULL,
    review_output JSONB,
    findings_count INT DEFAULT 0,
    suggestions_count INT DEFAULT 0,
    workiz_context_used JSONB,
    duration_ms INT,
    model_used VARCHAR(100),
    tokens_used INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_review_history_pr_url ON review_history(pr_url);
CREATE INDEX IF NOT EXISTS idx_review_history_repo ON review_history(repository);
CREATE INDEX IF NOT EXISTS idx_review_history_created ON review_history(created_at);
CREATE INDEX IF NOT EXISTS idx_review_history_author ON review_history(pr_author);

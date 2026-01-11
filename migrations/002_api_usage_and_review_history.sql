-- Migration 002: API Usage tracking and Review History enhancements
-- Run this after 001_init.sql

-- API Usage table: tracks all LLM API calls for cost monitoring
CREATE TABLE IF NOT EXISTS api_usage (
    id SERIAL PRIMARY KEY,
    model VARCHAR(255) NOT NULL,
    input_tokens INT NOT NULL,
    output_tokens INT NOT NULL,
    latency_ms INT,
    estimated_cost DECIMAL(10, 6) NOT NULL DEFAULT 0,
    pr_url TEXT,
    command VARCHAR(50),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_api_usage_model ON api_usage(model);
CREATE INDEX IF NOT EXISTS idx_api_usage_created_at ON api_usage(created_at);
CREATE INDEX IF NOT EXISTS idx_api_usage_pr_url ON api_usage(pr_url);

-- Add missing columns to review_history table if not present
ALTER TABLE review_history 
    ADD COLUMN IF NOT EXISTS pr_author VARCHAR(255),
    ADD COLUMN IF NOT EXISTS review_type VARCHAR(50) DEFAULT 'review',
    ADD COLUMN IF NOT EXISTS review_output JSONB,
    ADD COLUMN IF NOT EXISTS findings_count INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS suggestions_count INT DEFAULT 0,
    ADD COLUMN IF NOT EXISTS workiz_context_used JSONB,
    ADD COLUMN IF NOT EXISTS duration_ms INT,
    ADD COLUMN IF NOT EXISTS model_used VARCHAR(255),
    ADD COLUMN IF NOT EXISTS tokens_used INT;

-- Create index on pr_author if not exists
CREATE INDEX IF NOT EXISTS idx_review_history_author ON review_history(pr_author);

-- Update repositories table to match what save_review expects
ALTER TABLE repositories
    ADD COLUMN IF NOT EXISTS full_name VARCHAR(511),
    ADD COLUMN IF NOT EXISTS url TEXT;

-- Create unique index on name for upsert support
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes WHERE schemaname = 'public' AND indexname = 'idx_repositories_name_unique'
    ) THEN
        CREATE UNIQUE INDEX idx_repositories_name_unique ON repositories(name);
    END IF;
END $$;

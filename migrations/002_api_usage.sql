-- Migration: 002_api_usage.sql
-- Description: Add API usage tracking table and enhance review_history

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

-- Add new columns to existing review_history table
-- Using separate ALTER statements for compatibility
ALTER TABLE review_history ADD COLUMN IF NOT EXISTS review_type VARCHAR(50);
ALTER TABLE review_history ADD COLUMN IF NOT EXISTS findings_count INT DEFAULT 0;
ALTER TABLE review_history ADD COLUMN IF NOT EXISTS suggestions_count INT DEFAULT 0;
ALTER TABLE review_history ADD COLUMN IF NOT EXISTS workiz_context_used JSONB;
ALTER TABLE review_history ADD COLUMN IF NOT EXISTS duration_ms INT;
ALTER TABLE review_history ADD COLUMN IF NOT EXISTS model_used VARCHAR(100);
ALTER TABLE review_history ADD COLUMN IF NOT EXISTS tokens_used INT;

-- Update column names to match new schema (if they exist with old names)
-- Note: Using DO block to handle cases where columns may not exist
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'review_history' AND column_name = 'author') THEN
        ALTER TABLE review_history RENAME COLUMN author TO pr_author;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'review_history' AND column_name = 'review_result') THEN
        ALTER TABLE review_history RENAME COLUMN review_result TO review_output;
    END IF;
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'review_history' AND column_name = 'issues_found') THEN
        -- Copy data from issues_found to findings_count if both exist
        UPDATE review_history SET findings_count = issues_found WHERE findings_count IS NULL OR findings_count = 0;
    END IF;
END $$;

-- Add index on pr_author if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_review_history_author ON review_history(pr_author);

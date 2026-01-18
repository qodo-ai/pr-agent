-- Cursor Fix Prompts: stores prompts for "Fix in Cursor" feature
-- with full tracking for analytics and audit

CREATE TABLE IF NOT EXISTS cursor_fix_prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt TEXT NOT NULL,
    file_path TEXT,
    line_number INT,
    
    -- PR Context
    repository VARCHAR(255),
    pr_number INT,
    pr_url TEXT,
    
    -- Comment Context
    comment_type VARCHAR(50),
    severity VARCHAR(20),
    finding_id VARCHAR(255),
    
    -- Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP,
    access_count INT DEFAULT 0,
    accessed_by VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_cursor_fix_prompts_repository ON cursor_fix_prompts(repository);
CREATE INDEX IF NOT EXISTS idx_cursor_fix_prompts_pr_number ON cursor_fix_prompts(pr_number);
CREATE INDEX IF NOT EXISTS idx_cursor_fix_prompts_comment_type ON cursor_fix_prompts(comment_type);
CREATE INDEX IF NOT EXISTS idx_cursor_fix_prompts_created_at ON cursor_fix_prompts(created_at);

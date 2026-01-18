"""
Cursor Fix Prompts Storage Module

Stores prompts for "Fix in Cursor" feature with full tracking for analytics.
"""

import logging
import os
from datetime import datetime
from typing import Any
from uuid import UUID

logger = logging.getLogger(__name__)


def save_prompt(
    prompt: str,
    file_path: str | None = None,
    line_number: int | None = None,
    repository: str | None = None,
    pr_number: int | None = None,
    pr_url: str | None = None,
    comment_type: str | None = None,
    severity: str | None = None,
    finding_id: str | None = None,
) -> str | None:
    """
    Save a prompt for the "Fix in Cursor" feature.
    
    Args:
        prompt: The full prompt text
        file_path: Path to the file being fixed
        line_number: Line number in the file
        repository: Repository name (org/repo format)
        pr_number: PR number
        pr_url: Full PR URL
        comment_type: Type of comment ('static_analyzer', 'ai_suggestion')
        severity: Severity level ('critical', 'warning', 'info')
        finding_id: Original finding/suggestion ID
        
    Returns:
        The UUID of the saved prompt, or None if save failed
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.debug("DATABASE_URL not configured, cannot save prompt to DB", extra={"context": {}})
        return None
    
    try:
        from pr_agent.db import get_db_connection
        
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO cursor_fix_prompts (
                    prompt, file_path, line_number,
                    repository, pr_number, pr_url,
                    comment_type, severity, finding_id
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING id
                """,
                (
                    prompt,
                    file_path,
                    line_number,
                    repository,
                    pr_number,
                    pr_url,
                    comment_type,
                    severity,
                    finding_id,
                ),
            )
            conn.commit()
            result = cursor.fetchone()
            
            prompt_id = str(result[0]) if result else None
            
            logger.info(
                "Cursor fix prompt saved",
                extra={"context": {
                    "prompt_id": prompt_id,
                    "repository": repository,
                    "pr_number": pr_number,
                    "file_path": file_path,
                    "comment_type": comment_type,
                }}
            )
            
            return prompt_id
            
    except Exception as e:
        logger.error(
            "Failed to save cursor fix prompt",
            extra={"context": {
                "repository": repository,
                "pr_number": pr_number,
                "error": str(e),
            }}
        )
        return None


def get_prompt(
    prompt_id: str,
    accessed_by: str | None = None,
) -> dict[str, Any] | None:
    """
    Retrieve a prompt by ID and update access tracking.
    
    Args:
        prompt_id: UUID of the prompt
        accessed_by: GitHub username of who accessed (optional)
        
    Returns:
        Dict with prompt data, or None if not found
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.debug("DATABASE_URL not configured, cannot retrieve prompt from DB", extra={"context": {}})
        return None
    
    try:
        from pr_agent.db import get_db_connection
        
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                UPDATE cursor_fix_prompts
                SET 
                    accessed_at = %s,
                    access_count = access_count + 1,
                    accessed_by = COALESCE(%s, accessed_by)
                WHERE id = %s
                RETURNING id, prompt, file_path, line_number, repository, pr_number, 
                          pr_url, comment_type, severity, finding_id, created_at, 
                          accessed_at, access_count
                """,
                (datetime.utcnow(), accessed_by, prompt_id),
            )
            conn.commit()
            result = cursor.fetchone()
            
            if not result:
                logger.warning(
                    "Cursor fix prompt not found",
                    extra={"context": {"prompt_id": prompt_id}}
                )
                return None
            
            logger.info(
                "Cursor fix prompt retrieved",
                extra={"context": {
                    "prompt_id": prompt_id,
                    "access_count": result[12],
                    "accessed_by": accessed_by,
                }}
            )
            
            return {
                "id": str(result[0]),
                "prompt": result[1],
                "file": result[2],
                "line": result[3],
                "repository": result[4],
                "pr_number": result[5],
                "pr_url": result[6],
                "comment_type": result[7],
                "severity": result[8],
                "finding_id": result[9],
                "created_at": result[10].isoformat() if result[10] else None,
                "accessed_at": result[11].isoformat() if result[11] else None,
                "access_count": result[12],
            }
            
    except Exception as e:
        logger.error(
            "Failed to retrieve cursor fix prompt",
            extra={"context": {
                "prompt_id": prompt_id,
                "error": str(e),
            }}
        )
        return None


def get_prompt_analytics(
    repository: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict[str, Any]:
    """
    Get analytics for cursor fix prompts.
    
    Args:
        repository: Filter by repository
        start_date: Start of date range
        end_date: End of date range
        
    Returns:
        Analytics dict
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return {"error": "DATABASE_URL not configured"}
    
    if start_date is None:
        now = datetime.utcnow()
        start_date = datetime(now.year, now.month, 1)
    
    if end_date is None:
        end_date = datetime.utcnow()
    
    try:
        from pr_agent.db import get_db_connection
        
        query = """
            SELECT 
                COUNT(*) as total_prompts,
                COUNT(CASE WHEN access_count > 0 THEN 1 END) as accessed_prompts,
                SUM(access_count) as total_accesses,
                COUNT(DISTINCT repository) as repositories,
                COUNT(DISTINCT pr_number) as prs,
                COUNT(CASE WHEN comment_type = 'static_analyzer' THEN 1 END) as static_analyzer_count,
                COUNT(CASE WHEN comment_type = 'ai_suggestion' THEN 1 END) as ai_suggestion_count
            FROM cursor_fix_prompts
            WHERE created_at >= %s AND created_at <= %s
        """
        params = [start_date, end_date]
        
        if repository:
            query += " AND repository = %s"
            params.append(repository)
        
        with get_db_connection() as conn:
            cursor = conn.execute(query, params)
            row = cursor.fetchone()
            
            return {
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "total_prompts": row[0] or 0,
                "accessed_prompts": row[1] or 0,
                "total_accesses": row[2] or 0,
                "click_through_rate": round((row[1] or 0) / (row[0] or 1) * 100, 2),
                "repositories": row[3] or 0,
                "prs": row[4] or 0,
                "by_type": {
                    "static_analyzer": row[5] or 0,
                    "ai_suggestion": row[6] or 0,
                },
            }
            
    except Exception as e:
        logger.error(
            "Failed to get cursor fix prompt analytics",
            extra={"context": {"error": str(e)}}
        )
        return {"error": str(e)}

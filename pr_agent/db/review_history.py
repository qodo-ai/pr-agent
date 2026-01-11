"""
Review History Storage Module

Stores PR review history for analytics and learning.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


async def save_review(
    pr_url: str,
    pr_number: int,
    repository: str,
    pr_title: str,
    pr_author: str,
    review_type: str,
    review_output: dict[str, Any],
    findings_count: int = 0,
    suggestions_count: int = 0,
    workiz_context: dict[str, Any] | None = None,
    duration_ms: int | None = None,
    model_used: str | None = None,
    tokens_used: int | None = None,
) -> int | None:
    """
    Save a PR review to the database.
    
    Args:
        pr_url: Full URL of the PR
        pr_number: PR number
        repository: Repository name (org/repo format)
        pr_title: PR title
        pr_author: PR author username
        review_type: Type of review (e.g., "review", "auto_review")
        review_output: The review output dict
        findings_count: Number of issues found
        suggestions_count: Number of suggestions made
        workiz_context: Workiz-specific context used
        duration_ms: Review duration in milliseconds
        model_used: LLM model used
        tokens_used: Total tokens consumed
        
    Returns:
        The ID of the saved review, or None if save failed
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        logger.debug("DATABASE_URL not configured, skipping review history storage")
        return None
    
    try:
        from pr_agent.db import get_db_connection
        
        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO review_history (
                    pr_url, pr_number, repository, pr_title, pr_author,
                    review_type, review_output, findings_count, suggestions_count,
                    workiz_context_used, duration_ms, model_used, tokens_used,
                    created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING id
                """,
                (
                    pr_url,
                    pr_number,
                    repository,
                    pr_title,
                    pr_author,
                    review_type,
                    json.dumps(review_output),
                    findings_count,
                    suggestions_count,
                    json.dumps(workiz_context) if workiz_context else None,
                    duration_ms,
                    model_used,
                    tokens_used,
                    datetime.utcnow(),
                ),
            )
            conn.commit()
            result = cursor.fetchone()
            
            logger.info(
                "Review history saved",
                extra={"context": {
                    "review_id": result[0] if result else None,
                    "pr_url": pr_url,
                    "repository": repository,
                    "review_type": review_type,
                    "findings_count": findings_count,
                    "suggestions_count": suggestions_count,
                }}
            )
            
            return result[0] if result else None
            
    except Exception as e:
        logger.error(
            "Failed to save review history",
            extra={"context": {
                "pr_url": pr_url,
                "error": str(e),
            }}
        )
        return None


async def get_review_history(
    repository: str | None = None,
    pr_author: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """
    Get review history with optional filters.
    
    Args:
        repository: Filter by repository name
        pr_author: Filter by PR author
        limit: Maximum records to return
        offset: Offset for pagination
        
    Returns:
        List of review history records
    """
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        return []
    
    try:
        from pr_agent.db import get_db_connection
        
        query = """
            SELECT 
                id, pr_url, pr_number, repository, pr_title, pr_author,
                review_type, findings_count, suggestions_count,
                duration_ms, model_used, tokens_used, created_at
            FROM review_history
            WHERE 1=1
        """
        params = []
        
        if repository:
            query += " AND repository = %s"
            params.append(repository)
        
        if pr_author:
            query += " AND pr_author = %s"
            params.append(pr_author)
        
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        with get_db_connection() as conn:
            cursor = conn.execute(query, params)
            results = cursor.fetchall()
            
            return [
                {
                    "id": row[0],
                    "pr_url": row[1],
                    "pr_number": row[2],
                    "repository": row[3],
                    "pr_title": row[4],
                    "pr_author": row[5],
                    "review_type": row[6],
                    "findings_count": row[7],
                    "suggestions_count": row[8],
                    "duration_ms": row[9],
                    "model_used": row[10],
                    "tokens_used": row[11],
                    "created_at": row[12].isoformat() if row[12] else None,
                }
                for row in results
            ]
            
    except Exception as e:
        logger.error(
            "Failed to get review history",
            extra={"context": {"error": str(e)}}
        )
        return []


async def get_review_stats(
    repository: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict[str, Any]:
    """
    Get review statistics for analytics.
    
    Args:
        repository: Filter by repository
        start_date: Start of date range
        end_date: End of date range
        
    Returns:
        Statistics dict
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
                COUNT(*) as total_reviews,
                COUNT(DISTINCT repository) as repos_reviewed,
                COUNT(DISTINCT pr_author) as authors_reviewed,
                SUM(findings_count) as total_findings,
                SUM(suggestions_count) as total_suggestions,
                AVG(duration_ms) as avg_duration_ms,
                SUM(tokens_used) as total_tokens
            FROM review_history
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
                "total_reviews": row[0] or 0,
                "repos_reviewed": row[1] or 0,
                "authors_reviewed": row[2] or 0,
                "total_findings": row[3] or 0,
                "total_suggestions": row[4] or 0,
                "avg_duration_ms": float(row[5]) if row[5] else 0,
                "total_tokens": row[6] or 0,
            }
            
    except Exception as e:
        logger.error(
            "Failed to get review stats",
            extra={"context": {"error": str(e)}}
        )
        return {"error": str(e)}

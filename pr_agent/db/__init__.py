"""Database connection module for PR Agent.

Recommended usage:
    from pr_agent.db import get_db_connection
    
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM repositories")
            rows = cur.fetchall()

Note: get_conn/put_conn are deprecated. Use get_db_connection() instead.
"""
from .conn import get_db_connection, pool, get_conn, put_conn
from .api_usage import (
    track_api_call,
    get_usage_summary,
    estimate_cost,
    get_model_pricing,
    list_available_models_with_pricing,
)
from .review_history import save_review, get_review_history, get_review_stats
from .cursor_prompts import save_prompt, get_prompt, get_prompt_analytics

__all__ = [
    "get_db_connection",
    "pool",
    "get_conn",
    "put_conn",
    "track_api_call",
    "get_usage_summary",
    "estimate_cost",
    "get_model_pricing",
    "list_available_models_with_pricing",
    "save_review",
    "get_review_history",
    "get_review_stats",
    "save_prompt",
    "get_prompt",
    "get_prompt_analytics",
]


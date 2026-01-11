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

__all__ = ["get_db_connection", "pool", "get_conn", "put_conn"]


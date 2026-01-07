"""
Database connection pooling for PR Agent.
Following the same pattern as spam-detect service.
"""
import logging
import os
import threading
import time
from contextlib import contextmanager

from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)

dsn = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pr_agent")

pool = ConnectionPool(dsn, min_size=1, max_size=10)

_vector_lock = threading.Lock()
_vector_registered = False
_vector_retry_count = 0
_vector_next_retry_time = 0.0

VECTOR_MAX_RETRIES = int(os.environ.get("PGVECTOR_MAX_RETRIES", "5"))
VECTOR_RETRY_BACKOFF_SECONDS = float(os.environ.get("PGVECTOR_RETRY_BACKOFF", "60"))


def _register_vector_once(conn):
    """Register pgvector extension on first connection (thread-safe).
    
    Retries with exponential backoff until max retries reached.
    Backoff prevents performance degradation from repeated failures.
    
    Config via env vars:
        PGVECTOR_MAX_RETRIES: Max attempts before giving up (default: 5)
        PGVECTOR_RETRY_BACKOFF: Base backoff seconds (default: 60)
    """
    global _vector_registered, _vector_retry_count, _vector_next_retry_time
    
    if _vector_registered:
        return
    
    if _vector_retry_count >= VECTOR_MAX_RETRIES:
        return
    
    current_time = time.time()
    if current_time < _vector_next_retry_time:
        return
    
    with _vector_lock:
        if _vector_registered or _vector_retry_count >= VECTOR_MAX_RETRIES:
            return
        
        if current_time < _vector_next_retry_time:
            return
        
        try:
            register_vector(conn)
            _vector_registered = True
            logger.debug("pgvector extension registered successfully")
        except Exception as e:
            _vector_retry_count += 1
            backoff = VECTOR_RETRY_BACKOFF_SECONDS * (2 ** (_vector_retry_count - 1))
            _vector_next_retry_time = current_time + backoff
            
            if _vector_retry_count >= VECTOR_MAX_RETRIES:
                logger.error(
                    "Failed to register pgvector extension after max retries - vector operations disabled",
                    extra={"context": {"error": str(e), "attempts": _vector_retry_count}}
                )
            else:
                logger.warning(
                    "Failed to register pgvector extension - will retry after backoff",
                    extra={"context": {
                        "error": str(e),
                        "attempt": _vector_retry_count,
                        "max_retries": VECTOR_MAX_RETRIES,
                        "next_retry_in_seconds": backoff
                    }}
                )


def get_conn():
    """
    Get a connection from the pool with pgvector registered.
    
    IMPORTANT: You MUST call put_conn() when done to return the connection.
    Prefer using get_db_connection() context manager instead.
    """
    conn = pool.getconn()
    _register_vector_once(conn)
    return conn


def put_conn(conn):
    """Return a connection to the pool."""
    pool.putconn(conn)


@contextmanager
def get_db_connection():
    """
    Context manager for database connections (recommended).
    
    Automatically returns connection to pool when done.
    
    Usage:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM repositories")
                rows = cur.fetchall()
    """
    conn = pool.getconn()
    _register_vector_once(conn)
    try:
        yield conn
    finally:
        pool.putconn(conn)


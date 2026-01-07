"""
Database connection pooling for PR Agent.
Following the same pattern as spam-detect service.
"""
import logging
import os
import threading
from contextlib import contextmanager

from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)

dsn = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pr_agent")

pool = ConnectionPool(dsn, min_size=1, max_size=10)

_vector_lock = threading.Lock()
_vector_registered = False
_vector_warned = False


def _register_vector_once(conn):
    """Register pgvector extension on first connection (thread-safe).
    
    Retries on each connection until successful, as the extension
    may become available after initial failures.
    """
    global _vector_registered, _vector_warned
    
    if _vector_registered:
        return
    
    with _vector_lock:
        if _vector_registered:
            return
        
        try:
            register_vector(conn)
            _vector_registered = True
            logger.debug("pgvector extension registered successfully")
        except Exception as e:
            if not _vector_warned:
                _vector_warned = True
                logger.warning(
                    "Failed to register pgvector extension - will retry on next connection",
                    extra={"context": {"error": str(e)}}
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


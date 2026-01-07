"""
Database connection pooling for PR Agent.
Following the same pattern as spam-detect service.
"""
import logging
import os
import threading
import warnings
from contextlib import contextmanager

from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)

dsn = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pr_agent")

pool = ConnectionPool(dsn, min_size=1, max_size=10)


class _VectorRegistrationTracker:
    """Tracks pgvector registration failures to avoid log spam.
    
    Note: register_vector() must be called on EACH connection since it
    registers type adapters on the connection object. This class only
    tracks whether we've logged errors to avoid spam.
    
    Config via env vars:
        PGVECTOR_LOG_ERRORS: Set to "false" to suppress pgvector errors (default: true)
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._error_logged = False
        self._success_logged = False
        self._log_errors = os.environ.get("PGVECTOR_LOG_ERRORS", "true").lower() != "false"
    
    def register_on_connection(self, conn) -> bool:
        """Register pgvector adapter on a specific connection.
        
        Must be called on each connection from the pool.
        Returns True if registration succeeded, False otherwise.
        """
        try:
            register_vector(conn)
            
            if not self._success_logged:
                with self._lock:
                    if not self._success_logged:
                        self._success_logged = True
                        logger.debug("pgvector extension registered on connection")
            return True
            
        except Exception as e:
            if self._log_errors and not self._error_logged:
                with self._lock:
                    if not self._error_logged:
                        self._error_logged = True
                        logger.warning(
                            "Failed to register pgvector on connection - vector operations may not work",
                            extra={"context": {"error": str(e)}}
                        )
            return False


_vector_tracker = _VectorRegistrationTracker()


def get_conn():
    """
    Get a connection from the pool with pgvector registered.
    
    .. deprecated::
        Use get_db_connection() context manager instead to prevent connection leaks.
        This function requires manual cleanup via put_conn().
    
    IMPORTANT: You MUST call put_conn() when done to return the connection.
    Failing to do so will leak connections and eventually exhaust the pool.
    
    Example of UNSAFE usage (don't do this):
        conn = get_conn()
        conn.execute(...)  # If this raises, connection is leaked!
        put_conn(conn)
    
    Use this instead:
        with get_db_connection() as conn:
            conn.execute(...)  # Safe - connection returned even on error
    """
    warnings.warn(
        "get_conn() is deprecated and may leak connections. "
        "Use get_db_connection() context manager instead.",
        DeprecationWarning,
        stacklevel=2
    )
    conn = pool.getconn()
    _vector_tracker.register_on_connection(conn)
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
    _vector_tracker.register_on_connection(conn)
    try:
        yield conn
    finally:
        pool.putconn(conn)


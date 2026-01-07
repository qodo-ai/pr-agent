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


class _VectorRegistration:
    """Thread-safe pgvector registration with retry and backoff.
    
    Config via env vars:
        PGVECTOR_MAX_RETRIES: Max attempts before giving up (default: 5)
        PGVECTOR_RETRY_BACKOFF: Base backoff seconds (default: 60)
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._registered = False
        self._permanently_failed = False
        self._retry_count = 0
        self._next_retry_time = 0.0
        self._max_retries = int(os.environ.get("PGVECTOR_MAX_RETRIES", "5"))
        self._backoff_base = float(os.environ.get("PGVECTOR_RETRY_BACKOFF", "60"))
    
    def try_register(self, conn) -> None:
        """Attempt to register pgvector on connection.
        
        All state checks and modifications happen inside the lock
        to prevent race conditions.
        """
        if self._registered or self._permanently_failed:
            return
        
        with self._lock:
            if self._registered or self._permanently_failed:
                return
            
            current_time = time.time()
            if current_time < self._next_retry_time:
                return
            
            try:
                register_vector(conn)
                self._registered = True
                logger.debug("pgvector extension registered successfully")
            except Exception as e:
                self._retry_count += 1
                
                if self._retry_count >= self._max_retries:
                    self._permanently_failed = True
                    logger.error(
                        "Failed to register pgvector extension after max retries - vector operations disabled",
                        extra={"context": {"error": str(e), "attempts": self._retry_count}}
                    )
                else:
                    backoff = self._backoff_base * (2 ** (self._retry_count - 1))
                    self._next_retry_time = current_time + backoff
                    logger.warning(
                        "Failed to register pgvector extension - will retry after backoff",
                        extra={"context": {
                            "error": str(e),
                            "attempt": self._retry_count,
                            "max_retries": self._max_retries,
                            "next_retry_in_seconds": backoff
                        }}
                    )


_vector_registration = _VectorRegistration()


def get_conn():
    """
    Get a connection from the pool with pgvector registered.
    
    IMPORTANT: You MUST call put_conn() when done to return the connection.
    Prefer using get_db_connection() context manager instead.
    """
    conn = pool.getconn()
    _vector_registration.try_register(conn)
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
    _vector_registration.try_register(conn)
    try:
        yield conn
    finally:
        pool.putconn(conn)


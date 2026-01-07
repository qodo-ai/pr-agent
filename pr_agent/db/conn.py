"""
Database connection pooling for PR Agent.
Following the same pattern as spam-detect service.
"""
import logging
import os

from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool

logger = logging.getLogger(__name__)

dsn = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pr_agent")

pool = ConnectionPool(dsn, min_size=1, max_size=10)

_vector_registered = False
_vector_registration_failed = False


def get_conn():
    """Get a connection from the pool with pgvector registered."""
    global _vector_registered, _vector_registration_failed
    
    conn = pool.getconn()
    
    if not _vector_registered and not _vector_registration_failed:
        try:
            register_vector(conn)
            _vector_registered = True
            logger.debug("pgvector extension registered successfully")
        except Exception as e:
            _vector_registration_failed = True
            logger.warning(
                "Failed to register pgvector extension - vector operations may not work",
                extra={"context": {"error": str(e)}}
            )
    
    return conn


def put_conn(conn):
    """Return a connection to the pool."""
    pool.putconn(conn)


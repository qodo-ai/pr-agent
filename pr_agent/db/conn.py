"""
Database connection pooling for PR Agent.
Following the same pattern as spam-detect service.
"""
import os

from pgvector.psycopg import register_vector
from psycopg_pool import ConnectionPool

dsn = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pr_agent")

pool = ConnectionPool(dsn, min_size=1, max_size=10)


def get_conn():
    """Get a connection from the pool with pgvector registered."""
    conn = pool.getconn()
    try:
        register_vector(conn)
    except Exception:
        pass
    return conn


def put_conn(conn):
    """Return a connection to the pool."""
    pool.putconn(conn)


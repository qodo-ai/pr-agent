#!/usr/bin/env python3
"""
Run SQL migrations from migrations/ directory.
Following the same pattern as spam-detect service.
"""
import os
import sys
from pathlib import Path

import psycopg

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pr_agent.log_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

SERVICE_NAME = "pr-agent"


def load_configuration():
    """Load configuration from .env file or Google Cloud Secret Manager.
    
    Priority:
    1. If NODE_ENV not set → use .env file
    2. If NODE_ENV set → check for .env.<NODE_ENV> file first
    3. If no local file → load from Google Secret Manager (requires GCP_PROJECT_ID)
    """
    from pr_agent.utils.config_loader import load_config_sync

    node_env = os.environ.get("NODE_ENV")
    gcp_project_id = os.environ.get("GCP_PROJECT_ID")
    service_root = Path(__file__).parent.parent

    if not node_env:
        env_path = service_root / ".env"
        if env_path.exists():
            from dotenv import load_dotenv
            load_dotenv(env_path)
            logger.info("Loaded environment from file", extra={"context": {"path": str(env_path)}})
            return

        logger.warning("NODE_ENV not set and no .env file found, using defaults")
        return

    env_file_path = service_root / f".env.{node_env}"
    
    if env_file_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file_path)
        logger.info("Loaded environment from file", extra={"context": {"path": str(env_file_path)}})
        return

    if not gcp_project_id:
        raise ValueError(
            f"GCP_PROJECT_ID environment variable is required when NODE_ENV={node_env} "
            f"and no .env.{node_env} file exists"
        )

    try:
        config = load_config_sync(gcp_project_id, SERVICE_NAME)
        logger.info("Loaded config from Secret Manager", extra={"context": {
            "keys_count": len(config),
            "secret": f"{node_env}-{SERVICE_NAME}"
        }})
    except Exception as e:
        logger.warning("Failed to load config from Secret Manager, using env vars", extra={"context": {"error": str(e)}})


def create_database_if_not_exists(database_url: str):
    """Create the target database if it doesn't exist"""
    from urllib.parse import urlparse
    
    from psycopg import sql
    
    parsed = urlparse(database_url)
    db_name = parsed.path.lstrip('/')
    
    postgres_url = database_url.replace(f"/{db_name}", "/postgres")
    
    logger.info("Checking database exists", extra={"context": {"database": db_name}})
    try:
        with psycopg.connect(postgres_url, autocommit=True) as conn:
            result = conn.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (db_name,)
            )
            exists = result.fetchone() is not None
            
            if not exists:
                logger.info("Creating database", extra={"context": {"database": db_name}})
                conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
                logger.info("Database created", extra={"context": {"database": db_name}})
            else:
                logger.debug("Database already exists", extra={"context": {"database": db_name}})
    except Exception as e:
        logger.warning("Could not create database (may need manual creation)", extra={"context": {
            "database": db_name,
            "error": str(e)
        }})


def run_migrations():
    """Run all SQL migration files in order"""
    migrations_dir = Path(__file__).parent.parent / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        logger.warning("No migration files found")
        return
    
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pr_agent")
    
    create_database_if_not_exists(database_url)
    
    db_host = database_url.split('@')[1] if '@' in database_url else 'localhost'
    logger.info("Connecting to database", extra={"context": {"host": db_host}})
    
    with psycopg.connect(database_url) as conn:
        logger.debug("Setting up migration tracking table")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                filename VARCHAR(255) PRIMARY KEY,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        result = conn.execute("SELECT filename FROM schema_migrations")
        executed = {row[0] for row in result.fetchall()}
        
        new_migrations = 0
        for migration_file in migration_files:
            if migration_file.name in executed:
                logger.debug("Skipping migration (already executed)", extra={"context": {"file": migration_file.name}})
                continue
            
            logger.info("Running migration", extra={"context": {"file": migration_file.name}})
            try:
                with open(migration_file) as f:
                    migration_sql = f.read()
                
                with conn.transaction():
                    conn.execute(migration_sql)
                    conn.execute(
                        "INSERT INTO schema_migrations (filename) VALUES (%s)",
                        (migration_file.name,)
                    )
                
                logger.info("Migration completed", extra={"context": {"file": migration_file.name}})
                new_migrations += 1
            except Exception as e:
                logger.error("Migration failed", extra={"context": {
                    "file": migration_file.name,
                    "error": str(e)
                }})
                raise
    
    if new_migrations == 0:
        logger.info("Database is up to date, no new migrations")
    else:
        logger.info("Migrations completed", extra={"context": {"new_migrations": new_migrations}})


if __name__ == "__main__":
    try:
        logger.info("Starting migration runner")
        load_configuration()
        run_migrations()
        logger.info("Migration runner finished successfully")
    except Exception as e:
        logger.error("Migration failed", extra={"context": {"error": str(e)}})
        sys.exit(1)


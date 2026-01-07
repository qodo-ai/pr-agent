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
            print(f"✓ Loaded environment from {env_path}")
            return

        print("⚠ NODE_ENV not set and no .env file found. Using defaults.")
        return

    env_file_path = service_root / f".env.{node_env}"
    
    if env_file_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file_path)
        print(f"✓ Loaded environment from {env_file_path}")
        return

    if not gcp_project_id:
        raise ValueError(
            f"GCP_PROJECT_ID environment variable is required when NODE_ENV={node_env} "
            f"and no .env.{node_env} file exists"
        )

    try:
        config = load_config_sync(gcp_project_id, SERVICE_NAME)
        print(f"✓ Loaded {len(config)} config values from Google Secret Manager ({node_env}-{SERVICE_NAME})")
    except Exception as e:
        print(f"⚠ Failed to load config from Secret Manager: {e}")
        print("  Falling back to environment variables")


def create_database_if_not_exists(database_url: str):
    """Create the target database if it doesn't exist"""
    from urllib.parse import urlparse
    
    from psycopg import sql
    
    parsed = urlparse(database_url)
    db_name = parsed.path.lstrip('/')
    
    postgres_url = database_url.replace(f"/{db_name}", "/postgres")
    
    print(f"Ensuring database '{db_name}' exists...")
    try:
        with psycopg.connect(postgres_url, autocommit=True) as conn:
            result = conn.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (db_name,)
            )
            exists = result.fetchone() is not None
            
            if not exists:
                print(f"  Creating database '{db_name}'...")
                conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
                print(f"  ✓ Database '{db_name}' created")
            else:
                print(f"  ✓ Database '{db_name}' already exists")
    except Exception as e:
        print(f"  ⚠ Could not create database (may need manual creation): {e}")


def run_migrations():
    """Run all SQL migration files in order"""
    migrations_dir = Path(__file__).parent.parent / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        print("No migration files found")
        return
    
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pr_agent")
    
    create_database_if_not_exists(database_url)
    
    print(f"\nConnecting to database...")
    print(f"  Using DATABASE_URL: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
    with psycopg.connect(database_url) as conn:
        print("Setting up migration tracking...")
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
                print(f"⏭️  Skipping {migration_file.name} (already executed)")
                continue
                
            print(f"Running {migration_file.name}...")
            try:
                with open(migration_file) as f:
                    sql = f.read()
                
                with conn.transaction():
                    conn.execute(sql)
                    conn.execute(
                        "INSERT INTO schema_migrations (filename) VALUES (%s)",
                        (migration_file.name,)
                    )
                
                print(f"  ✓ {migration_file.name} completed")
                new_migrations += 1
            except Exception as e:
                print(f"  ❌ {migration_file.name} failed: {e}")
                raise
    
    if new_migrations == 0:
        print("\n✅ No new migrations to run. Database is up to date!")
    else:
        print(f"\n✅ Successfully ran {new_migrations} new migration(s)!")


if __name__ == "__main__":
    try:
        print("Loading configuration...")
        load_configuration()
        print()
        run_migrations()
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        exit(1)


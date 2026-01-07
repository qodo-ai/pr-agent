# Deployment & Implementation Guide

This document covers local setup, production deployment, data initialization, and implementation checklists.

## Table of Contents

1. [Local Development Setup](#1-local-development-setup)
2. [Production Deployment (GKE + Helm)](#2-production-deployment-gke--helm)
3. [Data Initialization](#3-data-initialization)
4. [Continuous Updates](#4-continuous-updates)
5. [Monitoring & Logging](#5-monitoring--logging)
6. [Testing Strategy](#6-testing-strategy)
7. [Files to Create](#7-files-to-create)
8. [Implementation Checklists](#8-implementation-checklists)
9. [Timeline](#9-timeline)

---

## 1. Local Development Setup

### Prerequisites

```bash
# 1. Install Python 3.11+
brew install python@3.11

# 2. Install Docker Desktop
brew install --cask docker

# 3. Install Google Cloud SDK
brew install google-cloud-sdk

# 4. Install PostgreSQL client (for debugging)
brew install postgresql@16

# 5. Install ngrok for webhook testing
brew install ngrok
```

### Clone and Setup Project

```bash
# Clone repository
cd ~/Documents/Github
git clone https://github.com/Workiz/workiz-pr-agent.git
cd workiz-pr-agent

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Start Local Database

Create `docker-compose.yml`:

```yaml
services:
  db:
    image: ankane/pgvector:latest
    environment:
      POSTGRES_PASSWORD: postgres
      POSTGRES_USER: postgres
      POSTGRES_DB: pr_agent_db
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d pr_agent_db"]
      interval: 5s
      timeout: 5s
      retries: 10
    profiles:
      - with-db  # Only start if explicitly requested

  api:
    build: .
    environment:
      - DATABASE_URL=${DATABASE_URL:-postgresql://postgres:postgres@db:5432/pr_agent_db}
      - GITHUB_USER_TOKEN=${GITHUB_USER_TOKEN}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - JIRA_BASE_URL=${JIRA_BASE_URL}
      - JIRA_API_TOKEN=${JIRA_API_TOKEN}
      - JIRA_EMAIL=${JIRA_EMAIL}
    ports:
      - "8000:8000"
```

```bash
# Start database
docker-compose --profile with-db up -d db

# Verify database is running
docker logs workiz-pr-agent-db-1

# Run migrations
python scripts/run_migrations.py
```

### Configure Local Environment

Create `.env` file for local development:

```bash
# .env (for local development)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pr_agent_db
GITHUB_USER_TOKEN=ghp_your-github-token
OPENAI_API_KEY=sk-your-openai-key
JIRA_BASE_URL=https://workiz.atlassian.net
JIRA_API_TOKEN=your-jira-api-token
JIRA_EMAIL=your-email@workiz.com
GCP_PROJECT_ID=workiz-development
```

For staging/production environments, create `.env.staging` or `.env.production`.

### Start Local Server

```bash
# Activate virtual environment
source venv/bin/activate

# Load environment
export $(cat .env | xargs)

# Run migrations
python scripts/run_migrations.py

# Start the server
python -m uvicorn pr_agent.servers.github_app:app --host 0.0.0.0 --port 8000 --reload
```

### Testing with ngrok

```bash
# Terminal 2: Start ngrok tunnel
ngrok http 8000

# Note the ngrok URL (e.g., https://abc123.ngrok.io)
```

Configure GitHub webhook with ngrok URL for testing.

### Test PR Review

```bash
# Use CLI to test directly:
python pr_agent/cli.py --pr_url="https://github.com/Workiz/test-repo/pull/1" review
```

---

## 2. Production Deployment (GKE + Helm)

The PR Agent and RepoSwarm services are deployed to **GKE (Google Kubernetes Engine)** using **Helm charts** and **GitHub Actions**, following the same pattern as other Workiz Python services (e.g., `spam-detect`).

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           Workiz Deployment Architecture                         │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  GitHub Repository                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  workiz-pr-agent/                                                        │    │
│  │  ├── .github/workflows/                                                  │    │
│  │  │   ├── deploy-pr-agent-staging.yml                                     │    │
│  │  │   └── deploy-pr-agent-prod.yml                                        │    │
│  │  ├── infra/helm/                                                         │    │
│  │  │   ├── staging.yaml                                                    │    │
│  │  │   └── prod.yaml                                                       │    │
│  │  ├── migrations/                                                         │    │
│  │  │   └── *.sql                                                           │    │
│  │  └── Dockerfile                                                          │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                               │                                                  │
│                               │ GitHub Actions                                   │
│                               ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Workiz/workiz-actions/deploy-microservice                               │    │
│  │  • Builds Docker image                                                    │    │
│  │  • Pushes to GCR                                                         │    │
│  │  • Deploys to GKE via Helm                                               │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
│                               │                                                  │
│                               ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │  Google Cloud Platform                                                    │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐   │    │
│  │  │  GCR         │  │  GKE         │  │  Secret Manager              │   │    │
│  │  │  (Images)    │  │  (K8s)       │  │  staging-pr-agent            │   │    │
│  │  └──────────────┘  └──────────────┘  │  prod-pr-agent               │   │    │
│  │                          │           └──────────────────────────────┘   │    │
│  │                          ▼                                               │    │
│  │  ┌──────────────────────────────────────────────────────────────────┐   │    │
│  │  │  Cloud SQL (PostgreSQL + pgvector)                                │   │    │
│  │  │  pr_agent_staging / pr_agent_prod                                 │   │    │
│  │  └──────────────────────────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Secrets Management (Google Cloud Secret Manager)

Secrets are stored in Google Cloud Secret Manager using the naming convention:
- **`<environment>-<service-name>`** (e.g., `staging-pr-agent`, `prod-pr-agent`)

The secret content is in `.env` format:

```bash
# Example: staging-pr-agent secret content
DATABASE_URL=postgresql://pr_agent:password@10.x.x.x:5432/pr_agent_staging
GITHUB_USER_TOKEN=ghp_xxx
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----...
GITHUB_WEBHOOK_SECRET=xxx
OPENAI_API_KEY=sk-xxx
JIRA_BASE_URL=https://workiz.atlassian.net
JIRA_API_TOKEN=xxx
JIRA_EMAIL=pr-agent@workiz.com
```

### Config Loader (Python equivalent of @workiz/config-loader)

Create `pr_agent/utils/config_loader.py`:

```python
"""
Configuration loader from .env files or Google Cloud Secret Manager.
Python equivalent of @workiz/config-loader

If .env.<environment> exists in the root directory, loads variables from that file.
Otherwise, loads from Google Cloud Secret Manager.

Secret naming convention: <environment>-<service-name>
Examples: staging-pr-agent, prod-pr-agent
"""

import os
from pathlib import Path


def _parse_env_content(content: str) -> dict[str, str]:
    """Parse .env file content into a dictionary."""
    config = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            config[key] = value
    return config


def _get_secret_manager_config(
    project_id: str,
    service_name: str,
    env_name_override: str | None = None
) -> dict[str, str]:
    """Load configuration from Google Cloud Secret Manager."""
    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient()

    node_env = os.environ.get('NODE_ENV', 'development')
    env_name = env_name_override if env_name_override else ('prod' if node_env == 'production' else node_env)

    secrets_name = f'{env_name}-{service_name}'

    staging_namespace = os.environ.get('STAGING_ENV_NAMESPACE')
    temp_cloud_env_secret = f'{staging_namespace}-{service_name}' if staging_namespace else None

    def fetch_secrets(name: str) -> dict[str, str]:
        secret_path = f'projects/{project_id}/secrets/{name}/versions/latest'
        response = client.access_secret_version(request={'name': secret_path})

        if not response.payload or not response.payload.data:
            raise ValueError(f'No data loaded from Google Secrets: {name}')

        content = response.payload.data.decode('UTF-8')
        return _parse_env_content(content)

    config = fetch_secrets(secrets_name)

    if temp_cloud_env_secret:
        cloud_env_config = fetch_secrets(temp_cloud_env_secret)
        config = {**config, **cloud_env_config}

    return config


def load_config_sync(
    service_name: str,
    project_id: str,
    env_name_override: str | None = None,
    service_root: Path | None = None
) -> dict[str, str]:
    """
    Load configuration from .env file or Google Cloud Secret Manager.
    
    Args:
        service_name: Name of the service (e.g., 'pr-agent')
        project_id: Google Cloud project ID
        env_name_override: Optional override for the environment name
        service_root: Root directory of the service (defaults to project root)
    
    Returns:
        Dictionary of configuration values
    """
    if service_root is None:
        service_root = Path(__file__).parent.parent.parent

    node_env = os.environ.get('NODE_ENV', 'development')
    env_file_path = service_root / f'.env.{node_env}'

    if env_file_path.exists():
        print(f'Loading config from {env_file_path}')
        content = env_file_path.read_text()
        config = _parse_env_content(content)
    else:
        print(f'Loading config from Google Secret Manager: {node_env}-{service_name}')
        config = _get_secret_manager_config(project_id, service_name, env_name_override)

    os.environ.update(config)

    return config
```

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

ENV PIP_NO_CACHE_DIR=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    git wget curl build-essential libpq-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "-m", "pr_agent.servers.github_app"]
```

### Helm Chart Configuration

Create `infra/helm/staging.yaml`:

```yaml
# PR Agent Service - Staging Configuration
replicaCount: 2

namespace: staging

environment: staging

containerPort: 8000

ingress:
  host: pr-agent-staging.workiz.dev

resources:
  limits:
    cpu: 2000m
    memory: 4Gi
  requests:
    cpu: 1000m
    memory: 2Gi

env:
  - name: GCP_PROJECT_ID
    value: "workiz-development"
  - name: SERVICE_NAME
    value: "pr-agent"

preUpgradeHook:
  enabled: true
  command: 
    - "/bin/sh"
    - "-c"
    - "NODE_ENV=staging GCP_PROJECT_ID=workiz-development python scripts/run_migrations.py"
```

Create `infra/helm/prod.yaml`:

```yaml
# PR Agent Service - Production Configuration
replicaCount: 3

namespace: production

environment: production

containerPort: 8000

ingress:
  host: pr-agent.workiz.dev

resources:
  limits:
    cpu: 4000m
    memory: 8Gi
  requests:
    cpu: 2000m
    memory: 4Gi

env:
  - name: GCP_PROJECT_ID
    value: "workiz-production"
  - name: SERVICE_NAME
    value: "pr-agent"

preUpgradeHook:
  enabled: true
  command: 
    - "/bin/sh"
    - "-c"
    - "NODE_ENV=production GCP_PROJECT_ID=workiz-production python scripts/run_migrations.py"
```

### GitHub Actions Workflow

Create `.github/workflows/deploy-pr-agent-staging.yml`:

```yaml
name: "🚀 [staging] Deploy PR Agent"

on:
  workflow_dispatch:
    inputs:
      CHART_VERSION:
        description: "Chart version to deploy"

env:
  DOCKER_FILE_PATH: ${{ github.workspace }}

jobs:
  deploy:
    permissions:
      contents: "read"
      id-token: "write"
    name: deploy
    runs-on: ubuntu-latest
    environment: staging

    env:
      IMAGE: pr-agent
      ENV: staging
      RELEASE_NAME: pr-agent
      GKE_SA_HELM_DEPLOYER_KEY: ${{ secrets.GKE_SA_HELM_DEPLOYER_KEY }}
      DOCKER_FILE_PATH: .
      CHART_VERSION: ${{ inputs.CHART_VERSION }}

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Deploy microservice
        uses: Workiz/workiz-actions/deploy-microservice@workiz.com
        with:
          IMAGE: ${{ env.IMAGE }}
          ENV: ${{ env.ENV }}
          RELEASE_NAME: ${{ env.RELEASE_NAME }}
          GKE_SA_HELM_DEPLOYER_KEY: ${{ env.GKE_SA_HELM_DEPLOYER_KEY }}
          DOCKER_FILE_PATH: ${{ env.DOCKER_FILE_PATH }}
          CHART_VERSION: ${{ env.CHART_VERSION }}
```

### Migrations

Create `migrations/001_init.sql`:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

-- Repositories table
CREATE TABLE IF NOT EXISTS repositories (
    id SERIAL PRIMARY KEY,
    org_name VARCHAR(255) NOT NULL,
    repo_name VARCHAR(255) NOT NULL,
    github_url TEXT,
    default_branch VARCHAR(100) DEFAULT 'workiz.com',
    primary_language VARCHAR(50),
    detected_frameworks JSONB,
    detected_databases JSONB,
    is_monorepo BOOLEAN DEFAULT FALSE,
    excluded BOOLEAN DEFAULT FALSE,
    last_indexed_at TIMESTAMP,
    last_commit_sha VARCHAR(40),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_name, repo_name)
);

-- Code chunks for RAG
CREATE TABLE IF NOT EXISTS code_chunks (
    id SERIAL PRIMARY KEY,
    repository_id INT REFERENCES repositories(id),
    file_path TEXT NOT NULL,
    chunk_content TEXT NOT NULL,
    chunk_type VARCHAR(50),
    start_line INT,
    end_line INT,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create vector index
CREATE INDEX IF NOT EXISTS code_chunks_embedding_idx 
    ON code_chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m=16, ef_construction=64);

-- Schema migrations tracking
CREATE TABLE IF NOT EXISTS schema_migrations (
    filename VARCHAR(255) PRIMARY KEY,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Migration Runner Script

Create `scripts/run_migrations.py`:

```python
#!/usr/bin/env python3
"""
Run SQL migrations from migrations/ directory.
"""
import os
import sys
from pathlib import Path

import psycopg

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SERVICE_NAME = "pr-agent"


def load_configuration():
    """Load configuration from .env file or Google Cloud Secret Manager."""
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
            f"GCP_PROJECT_ID required when NODE_ENV={node_env} and no .env.{node_env} file exists"
        )

    config = load_config_sync(SERVICE_NAME, gcp_project_id)
    print(f"✓ Loaded {len(config)} config values from Google Secret Manager ({node_env}-{SERVICE_NAME})")


def run_migrations():
    """Run all SQL migration files in order."""
    migrations_dir = Path(__file__).parent.parent / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))
    
    if not migration_files:
        print("No migration files found")
        return
    
    database_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pr_agent_db")
    
    print(f"\nConnecting to database...")
    with psycopg.connect(database_url) as conn:
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
```

### Database Setup

Create databases in Cloud SQL:

```bash
# Connect to Cloud SQL
gcloud sql connect pr-agent-db --user=postgres

# In psql:
CREATE DATABASE pr_agent_staging;
CREATE DATABASE pr_agent_prod;
\c pr_agent_staging
CREATE EXTENSION vector;
\c pr_agent_prod
CREATE EXTENSION vector;
\q
```

### Creating Secrets in GCloud Secret Manager

```bash
# Create staging secret with .env format content
cat > /tmp/staging-pr-agent.env << 'EOF'
DATABASE_URL=postgresql://pr_agent:password@10.x.x.x:5432/pr_agent_staging
GITHUB_USER_TOKEN=ghp_xxx
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----
...key content...
-----END RSA PRIVATE KEY-----
GITHUB_WEBHOOK_SECRET=xxx
OPENAI_API_KEY=sk-xxx
JIRA_BASE_URL=https://workiz.atlassian.net
JIRA_API_TOKEN=xxx
JIRA_EMAIL=pr-agent@workiz.com
EOF

gcloud secrets create staging-pr-agent --data-file=/tmp/staging-pr-agent.env
rm /tmp/staging-pr-agent.env

# Same for production
gcloud secrets create prod-pr-agent --data-file=/tmp/prod-pr-agent.env
```

### Configure GitHub App

1. Go to GitHub Organization Settings → Developer Settings → GitHub Apps
2. Create new GitHub App:
   - **Name**: Workiz PR Agent
   - **Webhook URL**: `https://pr-agent-staging.workiz.dev/api/v1/github_webhooks`
   - **Permissions**: Contents (Read), Issues (R&W), Pull requests (R&W), Commit statuses (R&W)
   - **Events**: Issue comment, Pull request, Pull request review, Push

3. Install the GitHub App to your organization

---

## 3. Data Initialization

### CLI Admin Tool

Create `scripts/cli_admin.py`:

```python
#!/usr/bin/env python3
"""
PR Agent Admin CLI for data management.
"""
import os
import sys
from pathlib import Path

import click
import psycopg

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SERVICE_NAME = "pr-agent"


def get_db_connection():
    """Get database connection."""
    dsn = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pr_agent_db")
    return psycopg.connect(dsn)


def load_configuration():
    """Load configuration from .env or Secret Manager."""
    node_env = os.environ.get("NODE_ENV")
    service_root = Path(__file__).parent.parent

    if not node_env:
        env_path = service_root / ".env"
        if env_path.exists():
            from dotenv import load_dotenv
            load_dotenv(env_path)
            return

    env_file_path = service_root / f".env.{node_env}"
    if env_file_path.exists():
        from dotenv import load_dotenv
        load_dotenv(env_file_path)
        return

    gcp_project_id = os.environ.get("GCP_PROJECT_ID")
    if gcp_project_id:
        from pr_agent.utils.config_loader import load_config_sync
        load_config_sync(SERVICE_NAME, gcp_project_id)


@click.group()
def cli():
    """PR Agent Admin CLI"""
    load_configuration()


@cli.command()
@click.option('--orgs', '-o', multiple=True, required=True, help='GitHub organizations')
def discover(orgs):
    """Discover repositories from GitHub organizations."""
    from pr_agent.services.discovery_service import GitHubDiscoveryService
    
    github_token = os.environ.get('GITHUB_USER_TOKEN')
    
    with get_db_connection() as conn:
        discovery = GitHubDiscoveryService(github_token, conn)
        for org in orgs:
            click.echo(f"Discovering repos for {org}...")
            result = discovery.sync_repos_to_database(org)
            click.echo(f"  Synced {result['synced']} repositories")


@cli.command('index-repos')
@click.option('--repo', '-r', help='Specific repository to index')
@click.option('--all', 'index_all', is_flag=True, help='Index all repositories')
def index_repos(repo, index_all):
    """Index repositories for RAG."""
    from pr_agent.services.indexing_service import RepositoryIndexingService
    
    with get_db_connection() as conn:
        indexing = RepositoryIndexingService(conn)
        
        if repo:
            click.echo(f"Indexing {repo}...")
            indexing.index_repository(repo)
        elif index_all:
            click.echo("Indexing all repositories...")
            with conn.cursor() as cur:
                cur.execute("SELECT repo_name, github_url FROM repositories WHERE NOT excluded")
                repos = cur.fetchall()
            for repo_name, github_url in repos:
                click.echo(f"  Indexing {repo_name}...")
                indexing.index_repository(github_url)


@cli.command('sync-jira')
@click.option('--projects', '-p', multiple=True, help='Specific Jira projects')
@click.option('--full', is_flag=True, help='Full sync (not incremental)')
def sync_jira(projects, full):
    """Sync Jira tickets."""
    from pr_agent.integrations.jira_client import JiraClient
    
    jira = JiraClient(
        base_url=os.environ.get('JIRA_BASE_URL'),
        email=os.environ.get('JIRA_EMAIL'),
        api_token=os.environ.get('JIRA_API_TOKEN')
    )
    
    if projects:
        for project in projects:
            click.echo(f"Syncing Jira project {project}...")
    else:
        click.echo("Syncing all Jira projects...")


@cli.command('sync-npm')
def sync_npm():
    """Sync internal @workiz packages from GitHub Packages."""
    from pr_agent.tools.npm_package_analyzer import InternalPackageRegistry
    
    github_token = os.environ.get('GITHUB_USER_TOKEN')
    
    with get_db_connection() as conn:
        registry = InternalPackageRegistry(conn, github_token)
        click.echo("Syncing @workiz packages from GitHub Packages...")
        result = registry.sync_from_github_packages()
        if 'error' in result:
            click.echo(f"  Error: {result['error']}")
        else:
            click.echo(f"  Synced {result.get('synced', 0)} packages")


@cli.command()
def status():
    """Show system status."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM repositories")
            repos = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM code_chunks")
            chunks = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM jira_tickets")
            tickets = cur.fetchone()[0]
            
            cur.execute("SELECT COUNT(*) FROM review_history")
            reviews = cur.fetchone()[0]
    
    click.echo("PR Agent Status")
    click.echo("=" * 40)
    click.echo(f"Repositories: {repos}")
    click.echo(f"Code Chunks: {chunks}")
    click.echo(f"Jira Tickets: {tickets}")
    click.echo(f"Reviews: {reviews}")


if __name__ == '__main__':
    cli()
```

### Initial Population Commands

```bash
# Load environment and run commands
source .env  # or export $(cat .env | xargs)

# 1. Run migrations first
python scripts/run_migrations.py

# 2. Discover all repos (auto-detects frameworks)
python scripts/cli_admin.py discover --orgs Workiz

# 3. Index all repos for RAG
python scripts/cli_admin.py index-repos --all

# 4. Sync Jira tickets
python scripts/cli_admin.py sync-jira --full

# 5. Sync internal @workiz packages from GitHub Packages
python scripts/cli_admin.py sync-npm

# 6. Check status
python scripts/cli_admin.py status
```

---

## 4. Continuous Updates

### Update Mechanisms

| Method | Trigger | Action |
|--------|---------|--------|
| **GitHub Webhook** | Push to main branch | Incremental repo indexing |
| **GitHub Webhook** | PR merged | Update code chunks |
| **Jira Webhook** | Issue created/updated | Sync single ticket |
| **Cloud Scheduler** | Every 6 hours | Full discovery cycle |
| **Cloud Scheduler** | Every 2 hours | Jira incremental sync |
| **Admin API** | Manual trigger | On-demand indexing |

### Webhook Handler Updates

Add to `pr_agent/servers/github_app.py`:

```python
@router.post("/api/v1/webhooks/push")
async def handle_push_webhook(request: Request):
    """Handle push events for incremental indexing."""
    payload = await request.json()
    
    # Only process pushes to main branches
    ref = payload.get('ref', '')
    branch = ref.replace('refs/heads/', '')
    
    main_branches = get_settings().github.main_branches
    if branch not in main_branches:
        return {"status": "skipped", "reason": "not a main branch"}
    
    repo_url = payload.get('repository', {}).get('html_url')
    
    # Trigger incremental indexing
    asyncio.create_task(index_repository_incremental(repo_url, branch))
    
    return {"status": "indexing_started"}

@router.post("/api/v1/webhooks/jira")
async def handle_jira_webhook(request: Request):
    """Handle Jira webhooks for ticket sync."""
    payload = await request.json()
    
    event_type = payload.get('webhookEvent')
    issue_key = payload.get('issue', {}).get('key')
    
    if event_type in ['jira:issue_created', 'jira:issue_updated']:
        asyncio.create_task(sync_single_jira_ticket(issue_key))
    
    return {"status": "synced"}
```

---

## 5. Monitoring & Logging

### Cloud Logging Setup

```bash
# View logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=pr-agent" \
    --limit 100 \
    --format="table(timestamp,textPayload)"

# Create log-based metric for errors
gcloud logging metrics create pr-agent-errors \
    --description="PR Agent error count" \
    --filter='resource.type="cloud_run_revision" AND resource.labels.service_name="pr-agent" AND severity>=ERROR'
```

### Cloud Monitoring Alerts

```bash
# Create alert policy for high error rate
gcloud alpha monitoring policies create \
    --display-name="PR Agent High Error Rate" \
    --condition-display-name="Error rate > 5%" \
    --condition-filter='metric.type="logging.googleapis.com/user/pr-agent-errors"' \
    --condition-threshold-value=0.05 \
    --condition-threshold-duration=300s \
    --notification-channels=your-channel-id
```

### API Cost Tracking

Add to database schema:

```sql
CREATE TABLE api_usage (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    model VARCHAR(100) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    input_tokens INT,
    output_tokens INT,
    cost_usd DECIMAL(10, 6),
    pr_url VARCHAR(500),
    operation VARCHAR(50)
);

CREATE TABLE budget_settings (
    id SERIAL PRIMARY KEY,
    monthly_budget DECIMAL(10, 2),
    alert_threshold DECIMAL(10, 2),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. Testing Strategy

### Test Structure

```
tests/
├── unit/
│   ├── test_language_analyzers/
│   │   ├── test_php_analyzer.py
│   │   ├── test_typescript_analyzer.py
│   │   ├── test_nestjs_analyzer.py
│   │   └── test_react_analyzer.py
│   ├── test_sql_analyzer.py
│   ├── test_security_analyzer.py
│   ├── test_custom_rules_engine.py
│   └── test_pubsub_analyzer.py
├── integration/
│   ├── test_github_provider.py
│   ├── test_jira_integration.py
│   ├── test_reposwarm_loader.py
│   └── test_database.py
├── e2e/
│   ├── test_full_review_flow.py
│   ├── test_autofix_flow.py
│   └── test_admin_api.py
├── fixtures/
│   ├── sample_diffs/
│   ├── sample_arch_md/
│   └── mock_responses/
└── conftest.py
```

### Example Unit Test

```python
# tests/unit/test_nestjs_analyzer.py
import pytest
from pr_agent.tools.language_analyzers.nestjs_analyzer import NestJSAnalyzer

class TestNestJSAnalyzer:
    
    @pytest.fixture
    def analyzer(self):
        return NestJSAnalyzer()
    
    def test_detects_missing_logger_context(self, analyzer):
        code = """
        this.logger.log('User created');
        """
        result = analyzer.analyze('test.service.ts', code)
        
        assert len(result.issues) == 1
        assert result.issues[0]['type'] == 'logger_missing_context'
    
    def test_allows_logger_with_context(self, analyzer):
        code = """
        this.logger.log('User created', { userId: user.id });
        """
        result = analyzer.analyze('test.service.ts', code)
        
        assert len([i for i in result.issues if i['type'] == 'logger_missing_context']) == 0
    
    def test_detects_let_usage(self, analyzer):
        code = """
        let count = 0;
        """
        result = analyzer.analyze('test.service.ts', code)
        
        assert any(i['type'] == 'let_usage' for i in result.issues)
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/test_nestjs_analyzer.py

# Run with coverage
pytest tests/ --cov=pr_agent --cov-report=html
```

---

## 7. Files to Create

### Directory Structure

```
workiz-pr-agent/
├── .github/
│   └── workflows/
│       ├── deploy-pr-agent-staging.yml    # Staging deployment workflow
│       └── deploy-pr-agent-prod.yml       # Production deployment workflow
├── infra/
│   └── helm/
│       ├── staging.yaml                   # Helm values for staging
│       └── prod.yaml                      # Helm values for production
├── migrations/
│   ├── 001_init.sql                       # Initial schema with pgvector
│   ├── 002_reposwarm.sql                  # RepoSwarm analysis cache
│   ├── 003_jira_tickets.sql               # Jira tables
│   └── 004_review_history.sql             # Review tracking tables
├── scripts/
│   └── run_migrations.py                  # Migration runner script
├── pr_agent/
│   ├── db/
│   │   ├── __init__.py
│   │   └── conn.py                        # PostgreSQL connection pool (psycopg)
│   ├── utils/
│   │   ├── __init__.py
│   │   └── config_loader.py               # Config from .env or Secret Manager
│   ├── integrations/
│   │   ├── __init__.py
│   │   └── jira_client.py                 # Jira API integration
│   ├── services/
│   │   ├── __init__.py
│   │   ├── indexing_service.py            # Repository indexing
│   │   ├── jira_sync_service.py           # Jira synchronization
│   │   └── discovery_service.py           # Auto-discovery for repos/Jira
│   ├── servers/
│   │   └── admin_api.py                   # Admin endpoints (add to existing)
│   ├── tools/
│   │   ├── jira_context_provider.py       # RAG for Jira tickets
│   │   ├── custom_rules_engine.py         # Custom review rules
│   │   ├── custom_rules_loader.py         # Load rules from TOML/DB
│   │   ├── sql_analyzer.py                # MySQL/MongoDB/ES analyzer
│   │   ├── pubsub_analyzer.py             # PubSub topology analyzer
│   │   ├── security_analyzer.py           # Deep security checks
│   │   ├── npm_package_analyzer.py        # NPM package version management
│   │   ├── autofix_agent.py               # Auto-fix agent
│   │   ├── reposwarm/                     # Adapted from royosherove/repo-swarm
│   │   │   ├── __init__.py
│   │   │   ├── investigator.py            # Core analysis (no Temporal)
│   │   │   ├── repo_type_detector.py      # Detect backend/frontend/etc
│   │   │   ├── structure_analyzer.py      # Build file tree
│   │   │   ├── context_loader.py          # Load for PR reviews
│   │   │   └── prompts/                   # Analysis prompts
│   │   │       ├── backend/
│   │   │       │   ├── nestjs/
│   │   │       │   ├── nodejs/
│   │   │       │   ├── python/
│   │   │       │   └── php/
│   │   │       ├── frontend/
│   │   │       │   └── react/
│   │   │       └── shared/
│   │   │           ├── security/
│   │   │           └── auth/
│   │   ├── language_analyzers/
│   │   │   ├── __init__.py
│   │   │   ├── base_analyzer.py
│   │   │   ├── php_analyzer.py
│   │   │   ├── javascript_analyzer.py
│   │   │   ├── typescript_analyzer.py
│   │   │   ├── nestjs_analyzer.py
│   │   │   ├── react_analyzer.py
│   │   │   └── python_analyzer.py
│   │   └── figma/
│   │       ├── __init__.py
│   │       ├── figma_mcp_client.py
│   │       └── design_verification_agent.py
│   ├── middleware/
│   │   ├── rate_limiter.py
│   │   └── circuit_breaker.py
│   └── settings/
│       └── workiz_rules.toml              # Custom rules configuration
├── Dockerfile                             # Production Docker image
├── docker-compose.yml                     # Local development setup
├── requirements.txt                       # Python dependencies
├── .env.example                           # Example environment file
└── docs/
    ├── README.md
    ├── ARCHITECTURE_AND_FEATURES.md
    └── DEPLOYMENT_AND_IMPLEMENTATION.md
```

---

## 8. Implementation Checklists

### Local Development Checklist

- [ ] Clone the repository
- [ ] Set up Python 3.11 virtual environment
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Start PostgreSQL: `docker-compose --profile with-db up -d db`
- [ ] Create `.env` file with credentials (GitHub, OpenAI, Jira)
- [ ] Run migrations: `python scripts/run_migrations.py`
- [ ] Start server: `python -m uvicorn pr_agent.servers.github_app:app --port 8000 --reload`
- [ ] Start ngrok: `ngrok http 8000`
- [ ] Configure GitHub webhook with ngrok URL
- [ ] Test with a PR review: `/review`

### Production Deployment Checklist (GKE + Helm)

#### Database Setup
- [ ] Create database in Cloud SQL: `pr_agent_staging`, `pr_agent_prod`
- [ ] Enable pgvector extension in both databases

#### Secrets (GCloud Secret Manager)
Create secrets with `.env` format content:
- [ ] `staging-pr-agent` - Staging environment secrets
- [ ] `prod-pr-agent` - Production environment secrets

Each secret should contain:
```
DATABASE_URL=postgresql://...
GITHUB_USER_TOKEN=ghp_...
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----...
GITHUB_WEBHOOK_SECRET=...
OPENAI_API_KEY=sk-...
JIRA_BASE_URL=https://workiz.atlassian.net
JIRA_API_TOKEN=...
JIRA_EMAIL=...
```

#### Infrastructure Files
- [ ] Create `Dockerfile`
- [ ] Create `infra/helm/staging.yaml`
- [ ] Create `infra/helm/prod.yaml`
- [ ] Create `.github/workflows/deploy-pr-agent-staging.yml`
- [ ] Create `.github/workflows/deploy-pr-agent-prod.yml`
- [ ] Create `scripts/run_migrations.py`
- [ ] Create `migrations/001_init.sql`

#### GitHub App Configuration
- [ ] Create GitHub App in organization
- [ ] Set webhook URL to `https://pr-agent-staging.workiz.dev/api/v1/github_webhooks`
- [ ] Configure permissions (Contents, Issues, PRs, Commit statuses)
- [ ] Add private key to Secret Manager
- [ ] Install App to organization

#### Deploy
- [ ] Run staging workflow: `.github/workflows/deploy-pr-agent-staging.yml`
- [ ] Verify deployment in GKE
- [ ] Test webhook endpoints
- [ ] Run production workflow

#### Jira Webhook
- [ ] Create webhook in Jira settings
- [ ] Point to `https://pr-agent.workiz.dev/api/v1/webhooks/jira`

#### Verification
- [ ] Check pods are running: `kubectl get pods -n staging`
- [ ] Check logs: `kubectl logs -n staging deployment/pr-agent`
- [ ] Test a PR review
- [ ] Verify migrations ran (pre-upgrade hook)

---

## 9. Timeline

### MVP (4 Weeks)

| Week | Focus | Deliverables |
|------|-------|--------------|
| **Week 1** | Foundation | PostgreSQL setup, basic webhook handler, configuration |
| **Week 2** | Core Review | Custom rules engine, language analyzers (NestJS, TS, PHP) |
| **Week 3** | RepoSwarm | Integration, context loader, prompts |
| **Week 4** | Testing & Polish | Unit tests, bug fixes, documentation |

### Full Feature Set (8 Weeks)

| Week | Focus | Deliverables |
|------|-------|--------------|
| **Week 5** | Jira Integration | Full Jira sync, ticket context in reviews |
| **Week 6** | Auto-Fix Agent | Auto-fix flow, GitHub button |
| **Week 7** | Admin UI | React dashboard, analytics |
| **Week 8** | Production | GCloud deployment, monitoring, alerts |

### Future Enhancements (Post-MVP)

| Feature | Timeline |
|---------|----------|
| Figma Design Verification | +2 weeks |
| Slack Integration | +1 week |
| Advanced Analytics | +2 weeks |
| Custom Webhook Outputs | +1 week |

---

## Next Steps

1. **Review documentation** with the team
2. **Set up local development environment** following this guide
3. **Create the database schema** in a local PostgreSQL instance
4. **Run auto-discovery** to populate repos
5. **Start Phase 1** implementation (database setup + global context)

For questions, refer to:
- [Architecture & Features](./ARCHITECTURE_AND_FEATURES.md) for technical details
- [Original PR Agent Documentation](https://qodo-merge-docs.qodo.ai/)

---

*Last updated: January 2026*


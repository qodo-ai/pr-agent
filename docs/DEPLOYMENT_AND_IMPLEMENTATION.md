# Deployment & Implementation Guide

This document covers local setup, production deployment, data initialization, and implementation checklists.

## Table of Contents

1. [Local Development Setup](#1-local-development-setup)
2. [Production Deployment (GCloud)](#2-production-deployment-gcloud)
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
# 1. Install Python 3.12+
brew install python@3.12

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
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install additional Workiz dependencies
pip install asyncpg jira pgvector aiohttp gitpython pyyaml packaging
```

### Start Local Database

Create `docker-compose.local.yml`:

```yaml
version: '3.8'
services:
  postgres:
    image: pgvector/pgvector:pg16
    container_name: pr-agent-db
    environment:
      POSTGRES_DB: pr_agent
      POSTGRES_USER: pr_agent
      POSTGRES_PASSWORD: pr_agent_dev
    ports:
      - "5432:5432"
    volumes:
      - pr_agent_data:/var/lib/postgresql/data
      - ./db/init:/docker-entrypoint-initdb.d

volumes:
  pr_agent_data:
```

```bash
# Create database init directory
mkdir -p db/init

# Create schema file (copy from ARCHITECTURE_AND_FEATURES.md)
# Then start database
docker-compose -f docker-compose.local.yml up -d

# Verify database is running
docker logs pr-agent-db
```

### Configure Secrets

```bash
# Create secrets file
cp pr_agent/settings/.secrets_template.toml pr_agent/settings/.secrets.toml

# Edit with your credentials
nano pr_agent/settings/.secrets.toml
```

Content of `.secrets.toml`:

```toml
[openai]
key = "sk-your-openai-key"

[github]
user_token = "ghp_your-github-token"
organization = "Workiz"
main_branches = ["workiz.com", "main", "master"]

[jira]
api_token = "your-jira-api-token"
email = "your-email@workiz.com"

[workiz]
database_url = "postgresql://pr_agent:pr_agent_dev@localhost:5432/pr_agent"
npm_org = "@workiz"
internal_package_prefixes = ["@workiz/", "workiz-"]
```

### Configure Main Settings

Edit `pr_agent/settings/configuration.toml`:

```toml
[config]
model = "gpt-4o"
fallback_models = ["gpt-4o-mini"]
git_provider = "github"

[workiz]
enable_cross_repo_context = true
enable_jira_integration = true
enable_custom_rules = true
enable_sql_review = true
enable_enhanced_security = true
enable_npm_analysis = true
rag_similarity_threshold = 0.75
rag_max_chunks = 10
max_review_comments = 15
auto_discovery_enabled = true
github_orgs = ["Workiz"]

[jira]
base_url = "https://workiz.atlassian.net"

[pr_reviewer]
num_max_findings = 15
require_security_review = true
```

### Initialize Database

```bash
# Activate virtual environment
source venv/bin/activate

# Set environment variables
export WORKIZ_DATABASE_URL="postgresql://pr_agent:pr_agent_dev@localhost:5432/pr_agent"
export GITHUB_USER_TOKEN="ghp_your_token"
export OPENAI_KEY="sk-your_key"
export JIRA_BASE_URL="https://workiz.atlassian.net"
export JIRA_API_TOKEN="your_jira_token"
export JIRA_EMAIL="your_email@workiz.com"

# Run auto-discovery
python -m pr_agent.cli_admin discover --orgs Workiz

# Index all repos
python -m pr_agent.cli_admin index-repos

# Sync Jira
python -m pr_agent.cli_admin sync-jira --full

# Check status
python -m pr_agent.cli_admin status
```

### Start Local Server

```bash
# Terminal 1: Start the server
source venv/bin/activate
python -m uvicorn pr_agent.servers.github_app:app --host 0.0.0.0 --port 3000 --reload

# Terminal 2: Start ngrok tunnel
ngrok http 3000

# Note the ngrok URL (e.g., https://abc123.ngrok.io)
```

### Configure GitHub Webhook (Testing)

1. Go to your test repository Settings → Webhooks
2. Add webhook:
   - **Payload URL**: `https://your-ngrok-url.ngrok.io/api/v1/github_webhooks`
   - **Content type**: `application/json`
   - **Secret**: (generate and save to `.secrets.toml`)
   - **Events**: Pull requests, Pull request reviews, Issue comments, Push

### Test PR Review

```bash
# Use CLI to test directly:
python pr_agent/cli.py --pr_url="https://github.com/Workiz/test-repo/pull/1" review
```

---

## 2. Production Deployment (GCloud)

### GCloud Project Setup

```bash
# Set your project
export PROJECT_ID="workiz-pr-agent"
export REGION="us-central1"

# Login to GCloud
gcloud auth login
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
    run.googleapis.com \
    secretmanager.googleapis.com \
    sqladmin.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com
```

### Create Cloud SQL Instance

```bash
# Create PostgreSQL instance
gcloud sql instances create pr-agent-db \
    --database-version=POSTGRES_16 \
    --tier=db-g1-small \
    --region=$REGION \
    --storage-auto-increase \
    --backup-start-time=03:00

# Create database
gcloud sql databases create pr_agent --instance=pr-agent-db

# Create user
gcloud sql users create pr_agent \
    --instance=pr-agent-db \
    --password="$(openssl rand -base64 24)"

# Enable pgvector extension
gcloud sql connect pr-agent-db --user=postgres
# In psql:
# CREATE EXTENSION vector;
# \q
```

### Configure Secrets in GCloud Secret Manager

```bash
# Create secrets
echo -n "sk-your-openai-key" | gcloud secrets create openai-key --data-file=-

echo -n "ghp_your-github-token" | gcloud secrets create github-token --data-file=-

# For GitHub App (store private key)
gcloud secrets create github-app-private-key --data-file=private-key.pem

echo -n "123456" | gcloud secrets create github-app-id --data-file=-

echo -n "your-webhook-secret" | gcloud secrets create github-webhook-secret --data-file=-

echo -n "your-jira-token" | gcloud secrets create jira-api-token --data-file=-

echo -n "your-email@workiz.com" | gcloud secrets create jira-email --data-file=-

# Database password
echo -n "database-password" | gcloud secrets create db-password --data-file=-

# List secrets to verify
gcloud secrets list
```

### Create Service Account

```bash
# Create service account
gcloud iam service-accounts create pr-agent-sa \
    --display-name="PR Agent Service Account"

# Grant Secret Manager access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:pr-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Grant Cloud SQL access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:pr-agent-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/cloudsql.client"
```

### GCloud Secret Manager Provider

Create `pr_agent/secret_providers/gcloud_secret_manager.py`:

```python
from google.cloud import secretmanager
from pr_agent.secret_providers.secret_provider import SecretProvider
from pr_agent.log import get_logger

class GCloudSecretManagerProvider(SecretProvider):
    """Secret provider using Google Cloud Secret Manager."""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.client = secretmanager.SecretManagerServiceClient()
        self._cache = {}
    
    def get_secret(self, secret_name: str, version: str = "latest") -> str:
        cache_key = f"{secret_name}:{version}"
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/{version}"
            response = self.client.access_secret_version(name=name)
            secret_value = response.payload.data.decode("UTF-8")
            self._cache[cache_key] = secret_value
            return secret_value
        except Exception as e:
            get_logger().error(f"Failed to get secret {secret_name}: {e}")
            raise
    
    def get_all_secrets(self) -> dict:
        return {
            'openai_key': self.get_secret('openai-key'),
            'github_token': self.get_secret('github-token'),
            'github_app_private_key': self.get_secret('github-app-private-key'),
            'github_app_id': self.get_secret('github-app-id'),
            'github_webhook_secret': self.get_secret('github-webhook-secret'),
            'jira_api_token': self.get_secret('jira-api-token'),
            'jira_email': self.get_secret('jira-email'),
            'db_password': self.get_secret('db-password'),
        }
```

### Production Dockerfile

Create `Dockerfile.production`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir asyncpg jira pgvector aiohttp gitpython pyyaml packaging google-cloud-secret-manager

# Copy application
COPY pr_agent/ ./pr_agent/

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Run with gunicorn
CMD exec gunicorn --bind :$PORT --workers 2 --threads 4 --timeout 300 pr_agent.servers.github_app:app -k uvicorn.workers.UvicornWorker
```

### Deploy to Cloud Run

```bash
# Build and push image
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/pr-agent:latest \
    -f Dockerfile.production .

# Deploy to Cloud Run
gcloud run deploy pr-agent \
    --image gcr.io/$PROJECT_ID/pr-agent:latest \
    --platform managed \
    --region $REGION \
    --service-account pr-agent-sa@$PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars "GCLOUD_PROJECT=$PROJECT_ID" \
    --set-env-vars "CLOUD_SQL_INSTANCE=$PROJECT_ID:$REGION:pr-agent-db" \
    --set-env-vars "JIRA_BASE_URL=https://workiz.atlassian.net" \
    --set-env-vars "GITHUB_ORGS=Workiz" \
    --add-cloudsql-instances $PROJECT_ID:$REGION:pr-agent-db \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --allow-unauthenticated

# Get the deployed URL
gcloud run services describe pr-agent --region $REGION --format='value(status.url)'
```

### Configure GitHub App (Production)

1. Go to GitHub Organization Settings → Developer Settings → GitHub Apps
2. Create new GitHub App:
   - **Name**: Workiz PR Agent
   - **Homepage URL**: Your Cloud Run URL
   - **Webhook URL**: `https://your-cloud-run-url/api/v1/github_webhooks`
   - **Webhook secret**: (store in Secret Manager)
   - **Permissions**:
     - Repository:
       - Contents: Read
       - Issues: Read & Write
       - Pull requests: Read & Write
       - Commit statuses: Read & Write
     - Organization:
       - Members: Read
   - **Events**:
     - Issue comment
     - Pull request
     - Pull request review
     - Push

3. Generate and download private key
4. Store private key in Secret Manager:
   ```bash
   gcloud secrets versions add github-app-private-key --data-file=downloaded-key.pem
   ```

5. Install the GitHub App to your organization

### Configure Jira Webhook (Production)

1. Go to Jira Settings → System → Webhooks
2. Create webhook:
   - **URL**: `https://your-cloud-run-url/api/v1/webhooks/jira`
   - **Events**: Issue: created, updated, deleted

### Set Up Scheduled Jobs

```bash
# Create Cloud Scheduler for periodic sync
gcloud scheduler jobs create http pr-agent-sync \
    --location $REGION \
    --schedule "0 */6 * * *" \
    --uri "https://your-cloud-run-url/api/v1/admin/sync/all" \
    --http-method POST \
    --oidc-service-account-email pr-agent-sa@$PROJECT_ID.iam.gserviceaccount.com

# Create job for Jira sync
gcloud scheduler jobs create http jira-sync \
    --location $REGION \
    --schedule "0 */2 * * *" \
    --uri "https://your-cloud-run-url/api/v1/admin/sync/jira" \
    --http-method POST \
    --oidc-service-account-email pr-agent-sa@$PROJECT_ID.iam.gserviceaccount.com
```

---

## 3. Data Initialization

### CLI Admin Tool

Create `pr_agent/cli_admin.py`:

```python
import asyncio
import click
from pr_agent.db.connection import DatabaseManager
from pr_agent.services.discovery_service import GitHubDiscoveryService
from pr_agent.services.indexing_service import RepositoryIndexingService
from pr_agent.integrations.jira_client import JiraClient
import os

db = DatabaseManager(os.environ.get('WORKIZ_DATABASE_URL'))

@click.group()
def cli():
    """PR Agent Admin CLI"""
    pass

@cli.command()
@click.option('--orgs', '-o', multiple=True, required=True, help='GitHub organizations')
def discover(orgs):
    """Discover repositories from GitHub organizations."""
    async def run():
        discovery = GitHubDiscoveryService(
            token=os.environ.get('GITHUB_USER_TOKEN'),
            db=db
        )
        for org in orgs:
            click.echo(f"Discovering repos for {org}...")
            result = await discovery.sync_repos_to_database(org)
            click.echo(f"  Synced {result['synced']} repositories")
    
    asyncio.run(run())

@cli.command('index-repos')
@click.option('--repo', '-r', help='Specific repository to index')
@click.option('--all', 'index_all', is_flag=True, help='Index all repositories')
def index_repos(repo, index_all):
    """Index repositories for RAG."""
    async def run():
        indexing = RepositoryIndexingService(db)
        
        if repo:
            click.echo(f"Indexing {repo}...")
            await indexing.index_repository(repo)
        elif index_all:
            click.echo("Indexing all repositories...")
            async with db.connection() as conn:
                repos = await conn.fetch("SELECT * FROM repositories WHERE NOT excluded")
            for r in repos:
                click.echo(f"  Indexing {r['repo_name']}...")
                await indexing.index_repository(r['github_url'])
    
    asyncio.run(run())

@cli.command('sync-jira')
@click.option('--projects', '-p', multiple=True, help='Specific Jira projects')
@click.option('--full', is_flag=True, help='Full sync (not incremental)')
def sync_jira(projects, full):
    """Sync Jira tickets."""
    async def run():
        jira = JiraClient(
            base_url=os.environ.get('JIRA_BASE_URL'),
            email=os.environ.get('JIRA_EMAIL'),
            api_token=os.environ.get('JIRA_API_TOKEN')
        )
        
        if projects:
            for project in projects:
                click.echo(f"Syncing Jira project {project}...")
                # Implement sync logic
        else:
            click.echo("Syncing all Jira projects...")
            # Implement full sync
    
    asyncio.run(run())

@cli.command('sync-npm')
@click.option('--org', '-o', default='@workiz', help='NPM organization')
def sync_npm(org):
    """Sync internal NPM packages."""
    async def run():
        from pr_agent.tools.npm_package_analyzer import InternalPackageRegistry
        registry = InternalPackageRegistry(db)
        click.echo(f"Syncing NPM packages from {org}...")
        result = await registry.sync_from_npm_org(org)
        click.echo(f"  Synced {result.get('synced', 0)} packages")
    
    asyncio.run(run())

@cli.command()
def status():
    """Show system status."""
    async def run():
        async with db.connection() as conn:
            repos = await conn.fetchval("SELECT COUNT(*) FROM repositories")
            chunks = await conn.fetchval("SELECT COUNT(*) FROM code_chunks")
            tickets = await conn.fetchval("SELECT COUNT(*) FROM jira_tickets")
            reviews = await conn.fetchval("SELECT COUNT(*) FROM review_history")
        
        click.echo("PR Agent Status")
        click.echo("=" * 40)
        click.echo(f"Repositories: {repos}")
        click.echo(f"Code Chunks: {chunks}")
        click.echo(f"Jira Tickets: {tickets}")
        click.echo(f"Reviews: {reviews}")
    
    asyncio.run(run())

if __name__ == '__main__':
    cli()
```

### Initial Population Commands

```bash
# 1. Discover all repos (auto-detects frameworks)
python -m pr_agent.cli_admin discover --orgs Workiz

# 2. Index all repos for RAG
python -m pr_agent.cli_admin index-repos --all

# 3. Sync Jira tickets
python -m pr_agent.cli_admin sync-jira --full

# 4. Sync internal NPM packages
python -m pr_agent.cli_admin sync-npm --org @workiz

# 5. Check status
python -m pr_agent.cli_admin status
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
pr_agent/
├── db/
│   ├── __init__.py
│   └── connection.py                    # PostgreSQL connection manager
├── integrations/
│   ├── __init__.py
│   └── jira_client.py                   # Jira API integration
├── services/
│   ├── __init__.py
│   ├── indexing_service.py              # Repository indexing
│   ├── jira_sync_service.py             # Jira synchronization
│   └── discovery_service.py             # Auto-discovery for repos/Jira
├── servers/
│   └── admin_api.py                     # Admin endpoints (add to existing)
├── secret_providers/
│   └── gcloud_secret_manager.py         # GCloud Secrets Manager integration
├── tools/
│   ├── global_context_provider.py       # RAG for cross-repo context
│   ├── jira_context_provider.py         # RAG for Jira tickets
│   ├── custom_rules_engine.py           # Custom review rules
│   ├── custom_rules_loader.py           # Load rules from TOML/DB
│   ├── sql_analyzer.py                  # MySQL/MongoDB/ES analyzer
│   ├── pubsub_analyzer.py               # PubSub topology analyzer
│   ├── security_analyzer.py             # Deep security checks
│   ├── npm_package_analyzer.py          # NPM package version management
│   ├── autofix_agent.py                 # Auto-fix agent
│   ├── reposwarm_context_loader.py      # RepoSwarm integration
│   └── language_analyzers/
│       ├── __init__.py
│       ├── base_analyzer.py
│       ├── php_analyzer.py
│       ├── javascript_analyzer.py
│       ├── typescript_analyzer.py
│       ├── nestjs_analyzer.py
│       ├── react_analyzer.py
│       └── python_analyzer.py
│   └── figma/
│       ├── __init__.py
│       ├── figma_mcp_client.py
│       └── design_verification_agent.py
├── middleware/
│   ├── rate_limiter.py
│   └── circuit_breaker.py
├── settings/
│   └── workiz_rules.toml                # Custom rules configuration
├── cli_admin.py                         # Admin CLI for data management
db/
└── init/
    └── 01_schema.sql                    # PostgreSQL schema
docker-compose.local.yml                 # Local DB setup
Dockerfile.production                    # Production Docker image
repos_config.yaml                        # Exclusion patterns & overrides
docs/
├── README.md
├── ARCHITECTURE_AND_FEATURES.md
└── DEPLOYMENT_AND_IMPLEMENTATION.md
```

---

## 8. Implementation Checklists

### Local Development Checklist

- [ ] Clone the repository
- [ ] Set up Python 3.12 virtual environment
- [ ] Install dependencies: `pip install -r requirements.txt asyncpg jira pgvector gitpython aiohttp packaging`
- [ ] Start PostgreSQL: `docker-compose -f docker-compose.local.yml up -d`
- [ ] Create `.secrets.toml` with credentials (GitHub, OpenAI, Jira)
- [ ] Run auto-discovery: `python -m pr_agent.cli_admin discover --orgs Workiz`
- [ ] Run Jira sync: `python -m pr_agent.cli_admin sync-jira --full`
- [ ] Sync internal NPM packages: `python -m pr_agent.cli_admin sync-npm --org @workiz`
- [ ] Start server: `python -m uvicorn pr_agent.servers.github_app:app --port 3000`
- [ ] Start ngrok: `ngrok http 3000`
- [ ] Configure GitHub webhook with ngrok URL
- [ ] Test with a PR review: `/review`

### Production Deployment Checklist

#### GCloud Setup
- [ ] Set project: `gcloud config set project workiz-pr-agent`
- [ ] Enable APIs: Cloud Run, Secret Manager, Cloud SQL, Cloud Build

#### Database
- [ ] Create Cloud SQL PostgreSQL instance
- [ ] Enable pgvector extension
- [ ] Run schema migration

#### Secrets (GCloud Secret Manager)
- [ ] `openai-key` - OpenAI API key
- [ ] `github-token` - GitHub personal access token
- [ ] `github-app-private-key` - GitHub App private key
- [ ] `github-app-id` - GitHub App ID
- [ ] `github-webhook-secret` - Webhook secret
- [ ] `jira-api-token` - Jira API token
- [ ] `jira-email` - Jira email
- [ ] `db-password` - Database password

#### Service Account
- [ ] Create service account: `pr-agent-sa`
- [ ] Grant Secret Manager access
- [ ] Grant Cloud SQL Client access

#### Deploy
- [ ] Build container: `gcloud builds submit`
- [ ] Deploy to Cloud Run
- [ ] Note the service URL

#### GitHub App Configuration
- [ ] Create GitHub App in organization
- [ ] Set webhook URL to Cloud Run service
- [ ] Configure permissions (Contents, Issues, PRs, Commit statuses)
- [ ] Install App to organization

#### Jira Webhook
- [ ] Create webhook in Jira settings
- [ ] Point to `{service-url}/api/v1/webhooks/jira`

#### Scheduled Jobs
- [ ] Create Cloud Scheduler for discovery (every 6 hours)
- [ ] Create Cloud Scheduler for Jira sync (every 2 hours)

#### Monitoring
- [ ] Set up Cloud Logging
- [ ] Create error rate alerts
- [ ] Set up uptime checks

#### Initial Data
- [ ] Run discovery job
- [ ] Verify repos are indexed
- [ ] Verify Jira projects synced

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


# Workiz PR Agent - Development Plan & Tracking

> **Status**: 🟢 Phase 3 & 4 Complete - Ready for Phase 5  
> **Last Updated**: January 11, 2026  
> **Total Phases**: 8  
> **Estimated Duration**: 8-10 weeks

---

## How to Use This Document

1. Work through phases **in order** (dependencies exist between phases)
2. Check off tasks as completed: `- [x] Task`
3. Each **🚀 Deployment Checkpoint** indicates when you can deploy and test
4. Links reference sections in our documentation:
   - [README.md](./README.md) - Quick start and overview
   - [ARCHITECTURE_AND_FEATURES.md](./ARCHITECTURE_AND_FEATURES.md) - Implementation details
   - [DEPLOYMENT_AND_IMPLEMENTATION.md](./DEPLOYMENT_AND_IMPLEMENTATION.md) - Setup guides

---

## Phase Overview

| Phase | Name | Duration | Deployment |
|-------|------|----------|------------|
| **1** | [Foundation & Local Setup](#phase-1-foundation--local-setup) | 3-4 days | ✅ Local only |
| **2** | [Database & Core Infrastructure](#phase-2-database--core-infrastructure) | 3-4 days | ✅ Local only |
| **3** | [Basic PR Review Enhancement](#phase-3-basic-pr-review-enhancement) | 5-7 days | 🚀 **First Deploy** |
| **4** | [Language Analyzers & Custom Rules](#phase-4-language-analyzers--custom-rules) | 5-7 days | 🚀 Deploy |
| **5** | [RepoSwarm & Cross-Repo Context](#phase-5-reposwarm--cross-repo-context) | 5-7 days | 🚀 Deploy |
| **6** | [Jira Integration](#phase-6-jira-integration) | 4-5 days | 🚀 Deploy |
| **7** | [Auto-Fix Agent](#phase-7-auto-fix-agent) | 5-7 days | 🚀 Deploy |
| **8** | [Admin UI & Knowledge Assistant](#phase-8-admin-ui--knowledge-assistant) | 7-10 days | 🚀 **Full Deploy** |

---

## Phase 1: Foundation & Local Setup

**Goal**: Get the base PR Agent running locally with all dependencies

**Prerequisites**: Python 3.11+, Docker Desktop, GitHub PAT, Google API Key (Gemini)

### Tasks

#### 1.1 Repository Setup ✅ COMPLETED
- [x] Clone the forked repository ✅
  ```bash
  git clone https://github.com/Workiz/workiz-pr-agent.git
  cd workiz-pr-agent
  ```
- [x] Create and activate virtual environment ✅
  ```bash
  python3.11 -m venv venv
  source venv/bin/activate
  ```
- [x] Install dependencies ✅
  ```bash
  pip install -r requirements.txt
  ```
  > 📖 Reference: [README.md - Quick Start](./README.md#-quick-start)

#### 1.2 Environment Configuration ✅ MOSTLY COMPLETED
- [x] Create `env.example` template file ✅
- [x] Create `.env` file from template ✅
  ```bash
  cp env.example .env
  ```
- [x] Configure required secrets in `.env`:
  - [x] `GITHUB_APP_ID` ✅
  - [x] `GITHUB_APP_PRIVATE_KEY_BASE64` (base64 encoded) ✅
  - [x] `GITHUB_WEBHOOK_SECRET` ✅
  - [x] `GOOGLE_API_KEY` ✅ (Gemini - primary LLM)
  - [x] `LLM_PROVIDER=google` ✅
  - [x] `LLM_MODEL=gemini-3-pro` ✅
  - [x] `DATABASE_URL` ✅
  - Note: `GITHUB_USER_TOKEN` not needed - GitHub App uses installation tokens
- [x] Create `docker-compose.yml` for local PostgreSQL ✅
  > 📖 Reference: [DEPLOYMENT_AND_IMPLEMENTATION.md - Environment Variables](./DEPLOYMENT_AND_IMPLEMENTATION.md#environment-variables)

#### 1.3 GitHub App Setup
- [x] Create GitHub App in Workiz organization ✅ (App ID: 2636208)
- [ ] Configure permissions (Contents: Read, PRs: Read/Write, Issues: Read/Write)
- [ ] Configure webhook URL (use ngrok for local testing)
- [ ] Subscribe to events: `pull_request`, `issue_comment`, `push`
- [ ] Install app on test repository
  > 📖 Reference: [DEPLOYMENT_AND_IMPLEMENTATION.md - GitHub App Configuration](./DEPLOYMENT_AND_IMPLEMENTATION.md#github-app-configuration)

#### 1.4 Verify Base Functionality
- [ ] Start the base server
  ```bash
  python -m uvicorn pr_agent.servers.github_app:app --port 8000 --reload
  ```
- [ ] Create a test PR in the test repository
- [ ] Verify `/review` command works (comment on PR)
- [ ] Verify `/improve` command works
- [ ] Check logs for any errors

### ✅ Phase 1 Completion Criteria
- [ ] Server runs without errors
- [ ] Basic `/review` command works on test PRs
- [ ] Logs show successful LLM API calls

---

## Phase 2: Database & Core Infrastructure ✅ COMPLETED

**Goal**: Set up PostgreSQL with pgvector and create the database schema

### Tasks

#### 2.1 Database Setup ✅ COMPLETED
- [x] Create `docker-compose.yml` with PostgreSQL + pgvector ✅
  ```yaml
  services:
    db:
      image: pgvector/pgvector:pg16
      environment:
        POSTGRES_DB: pr_agent
        POSTGRES_USER: postgres
        POSTGRES_PASSWORD: postgres
      ports:
        - "5432:5432"
      volumes:
        - pgdata:/var/lib/postgresql/data
  ```
- [x] Start database container ✅
  ```bash
  docker-compose up -d db
  ```
  > 📖 Reference: [DEPLOYMENT_AND_IMPLEMENTATION.md - Docker Compose](./DEPLOYMENT_AND_IMPLEMENTATION.md#docker-compose-for-local-development)

#### 2.2 Database Schema ✅ COMPLETED
- [x] Create `migrations/` directory ✅
- [x] Create `001_init.sql` with full schema: ✅
  - [x] `repositories` table ✅
  - [x] `code_chunks` table with vector column ✅
  - [x] `jira_tickets` table with vector column ✅
  - [x] `repo_analysis_cache` table ✅
  - [x] `review_rules` table ✅
  - [x] `review_history` table ✅
  - [x] `internal_packages` table ✅
  - [x] `github_activity` table ✅
  - [x] `assistant_conversations` table ✅
  - [x] All indexes (including HNSW vector indexes) ✅
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Database Schema](./ARCHITECTURE_AND_FEATURES.md#database-schema-postgresql-with-pgvector)

#### 2.3 Migration Runner ✅ COMPLETED
- [x] Create `scripts/run_migrations.py` ✅
  - [x] Load config from `.env` or Secret Manager ✅
  - [x] Track executed migrations in `schema_migrations` table ✅
  - [x] Execute migrations in order ✅
- [x] Run migrations ✅
  ```bash
  python scripts/run_migrations.py
  ```
- [x] Verify tables exist ✅
  ```bash
  docker exec -it pr-agent-db psql -U postgres -d pr_agent -c "\dt"
  ```
  > 📖 Reference: [DEPLOYMENT_AND_IMPLEMENTATION.md - Migration Runner](./DEPLOYMENT_AND_IMPLEMENTATION.md#migration-runner)

#### 2.4 Database Connection Module ✅ COMPLETED
- [x] Create `pr_agent/db/conn.py` ✅
  - [x] Connection pool with `psycopg_pool` ✅
  - [x] `get_conn()` / `put_conn()` functions ✅
  - [x] Register pgvector extension ✅
- [x] Add `DATABASE_URL` to `.env` ✅
- [x] Test database connection ✅
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Database Connection](./ARCHITECTURE_AND_FEATURES.md#database-connection)

#### 2.5 Config Loader ✅ COMPLETED
- [x] Create `pr_agent/utils/config_loader.py` ✅
  - [x] Load config from `.env` file (local dev) ✅
  - [x] Load from Google Secret Manager (production) ✅
  - [x] `load_config_sync()` / `load_config()` functions ✅
  > 📖 Reference: [DEPLOYMENT_AND_IMPLEMENTATION.md - Configuration](./DEPLOYMENT_AND_IMPLEMENTATION.md#configuration)

#### 2.6 Logging Configuration ✅ COMPLETED
- [x] Create `pr_agent/log_config.py` ✅
  - [x] JSON formatter for Datadog ✅
  - [x] `setup_logging()` function ✅
  - [x] `get_logger()` / `get_context_logger()` helpers ✅
- [ ] Integrate into `main.py` / server startup (will be done in Phase 3)
  > 📖 Reference: [DEPLOYMENT_AND_IMPLEMENTATION.md - Logging Configuration](./DEPLOYMENT_AND_IMPLEMENTATION.md#logging-configuration)

### ✅ Phase 2 Completion Criteria
- [x] PostgreSQL running with all tables created ✅
- [x] Connection pool works ✅
- [x] JSON logging formatter ready ✅
- [x] Migrations run successfully ✅

**Phase 2 Status: ✅ COMPLETED** (pending API keys for Phase 1 completion)

---

## Phase 3: Basic PR Review Enhancement

**Goal**: Enhance the base PR reviewer with basic Workiz-specific features

### 🚀 Deployment Checkpoint: First Production Deploy

After this phase, you can deploy a basic working version to GKE.

### Tasks

#### 3.1 Configuration Extension ✅ COMPLETED
- [x] Update `pr_agent/settings/configuration.toml` with `[workiz]` section ✅
- [x] Create `pr_agent/settings/workiz_rules.toml` with 20+ custom rules ✅
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Configuration](./ARCHITECTURE_AND_FEATURES.md#configuration-extension)

#### 3.2 Workiz PR Reviewer ✅ COMPLETED
- [x] Create `pr_agent/tools/workiz_pr_reviewer.py` ✅
  - [x] Extend base `PRReviewer` ✅
  - [x] Override `run()` method to add Workiz pipeline ✅
  - [x] Add placeholder methods for future analyzers ✅
  - [x] Integrate with database for review history ✅
- [x] Register in `pr_agent/agent/pr_agent.py` command mapping ✅
- [x] Added `get_reviewer_class()` to dynamically select reviewer based on config ✅
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - WorkizPRReviewer](./ARCHITECTURE_AND_FEATURES.md#workizprreviewer)

#### 3.3 Prompt Enhancement ✅ COMPLETED
- [x] Create `pr_agent/settings/workiz_prompts.toml` ✅
  - [x] Enhanced system prompt with Workiz context ✅
  - [x] Template variables for dynamic context injection ✅
  - [x] Cross-repo, Jira, rules, and analyzer prompt templates ✅
- [x] Max comments configurable via `max_review_comments` setting ✅
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Prompt Enhancement](./ARCHITECTURE_AND_FEATURES.md#prompt-enhancement)

#### 3.4 API Usage Tracking ✅ COMPLETED
- [x] Create `pr_agent/db/api_usage.py` ✅
  - [x] `track_api_call()` function ✅
  - [x] `estimate_cost()` function with per-model pricing ✅
  - [x] `get_usage_summary()` for analytics ✅
- [x] Created migration `002_api_usage.sql` for api_usage table ✅
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Cost Tracking](./ARCHITECTURE_AND_FEATURES.md#14-cost-tracking)

#### 3.5 Review History Storage ✅ COMPLETED
- [x] Create `pr_agent/db/review_history.py` ✅
  - [x] `save_review()` function ✅
  - [x] `get_review_history()` for listing ✅
  - [x] `get_review_stats()` for analytics ✅
- [x] Enhanced existing review_history table with new columns ✅

#### 3.6 CLI Admin Tool (Basic) ✅ COMPLETED
- [x] Create `scripts/cli_admin.py` with Click ✅
  - [x] `status` command - show DB stats ✅
  - [x] `costs` command - show API usage/costs ✅
  - [x] `reviews` command - show review history ✅
  - [x] `discover`, `index-repos`, `analyze-repos` placeholders ✅
  - [x] `sync-jira`, `sync-github-activity` placeholders ✅
- [x] Add to `requirements.txt`: `click` ✅
  > 📖 Reference: [DEPLOYMENT_AND_IMPLEMENTATION.md - CLI Admin Tool](./DEPLOYMENT_AND_IMPLEMENTATION.md#cli-admin-tool)

#### 3.7 Workiz Code Suggestions ✅ COMPLETED
- [x] Create `pr_agent/tools/workiz_pr_code_suggestions.py` ✅
  - [x] Extend base `PRCodeSuggestions` ✅
  - [x] Override `run()` method to add Workiz pipeline ✅
  - [x] Inject Workiz coding standards into prompts ✅
  - [x] Add placeholder methods for cross-repo context ✅
- [x] Register in `pr_agent/agent/pr_agent.py` command mapping ✅
- [x] Added `get_code_suggestions_class()` to dynamically select suggestions class ✅
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - WorkizPRCodeSuggestions](./ARCHITECTURE_AND_FEATURES.md#workiz-specific-extensions)

#### 3.8 Webhook Handlers ✅ COMPLETED
- [x] Create push webhook handler for main branches ✅
  - [x] Filter for main branches (workiz.com, main, master) ✅
  - [x] Placeholder for indexing trigger ✅
  > 📖 Reference: [DEPLOYMENT_AND_IMPLEMENTATION.md - Push Webhook](./DEPLOYMENT_AND_IMPLEMENTATION.md#push-webhook-handler)

### 3.9 DB Storage Implementation ✅ COMPLETED
- [x] Implement actual DB storage in `_store_review_history()` ✅
- [x] Implement actual API tracking in `_track_api_usage()` ✅
- [x] Create migration 002 for api_usage table and review_history enhancements ✅

### 🚀 3.10 First Deployment
- [ ] Create `Dockerfile` for production
- [ ] Create Helm chart `infra/helm/staging.yaml`
- [ ] Create GitHub Actions workflow `deploy-pr-agent-staging.yml`
- [ ] Create Cloud SQL instance (PostgreSQL)
- [ ] Create secrets in GCloud Secret Manager:
  - [ ] `staging-pr-agent` with all env vars
- [ ] Deploy to staging GKE
- [ ] Configure GitHub App webhook to point to staging URL
- [ ] Test on real PR in test repository
  > 📖 Reference: [DEPLOYMENT_AND_IMPLEMENTATION.md - Production Deployment](./DEPLOYMENT_AND_IMPLEMENTATION.md#2-production-deployment-gke--helm)

### ✅ Phase 3 Completion Criteria
- [x] Enhanced reviewer (WorkizPRReviewer) works locally ✅
- [x] Enhanced code suggestions (WorkizPRCodeSuggestions) works locally ✅
- [x] Webhook handlers for push events ✅
- [x] Review history saved to database ✅
- [x] API costs tracked ✅
- [ ] **Deployed to staging and functional** (SKIPPED for now)
- [ ] Can review real PRs in test repo

**Phase 3 Status: ✅ COMPLETED** (deployment skipped)

---

## Phase 4: Language Analyzers & Custom Rules ✅ COMPLETED

**Goal**: Add language-specific analysis and custom review rules

### Tasks

#### 4.1 Base Analyzer Framework ✅ COMPLETED
- [x] Create `pr_agent/tools/language_analyzers.py` ✅
  - [x] `BaseAnalyzer` abstract class ✅
  - [x] `AnalyzerFinding` dataclass ✅
  - [x] `Severity` enum ✅
  - [x] Common methods: `analyze()`, `get_findings()` ✅
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Language Analyzers](./ARCHITECTURE_AND_FEATURES.md#5-language-specific-analyzers)

#### 4.2 TypeScript/NestJS Analyzer ✅ COMPLETED
- [x] Create `TypeScriptAnalyzer` ✅
  - [x] Detect TypeScript files ✅
  - [x] Check for let/var usage (FP rules) ✅
  - [x] Check for array mutations ✅
  - [x] Check for console.log ✅
  - [x] Check for any type ✅
- [x] Create `NestJSAnalyzer` ✅
  - [x] Detect NestJS patterns (decorators, modules) ✅
  - [x] Check DI patterns ✅
  - [x] Validate controller/service structure ✅
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - NestJS Analyzer](./ARCHITECTURE_AND_FEATURES.md#nestjs-analyzer)

#### 4.3 React Analyzer ✅ COMPLETED
- [x] Create `ReactAnalyzer` ✅
  - [x] Detect React components ✅
  - [x] Check for class components vs functional ✅
  - [x] Check inline styles ✅
  - [x] Check hook patterns ✅

#### 4.4 PHP Analyzer ✅ COMPLETED
- [x] Create `PHPAnalyzer` ✅
  - [x] Parse PHP files ✅
  - [x] Detect SQL injection patterns ✅
  - [x] Check for eval usage ✅
  - [x] Check for global variables ✅

#### 4.5 Python Analyzer ✅ COMPLETED
- [x] Create `PythonAnalyzer` ✅
  - [x] Check for bare except ✅
  - [x] Check for print statements ✅
  - [x] Check for mutable default arguments ✅

#### 4.6 Custom Rules Engine ✅ COMPLETED
- [x] Create `pr_agent/tools/custom_rules_engine.py` ✅
  - [x] Load rules from `workiz_rules.toml` ✅
  - [x] Pattern matching with regex ✅
  - [x] Apply rules to code by language ✅
  - [x] Generate findings ✅
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Custom Rules Engine](./ARCHITECTURE_AND_FEATURES.md#4-custom-rules-engine)

#### 4.7 Implement Workiz Team Rules ✅ COMPLETED
- [x] Added 20+ rules to `workiz_rules.toml`: ✅
  - [x] Functional programming style ✅
  - [x] Immutability (const over let) ✅
  - [x] Small functions (<15 lines) ✅
  - [x] Structured logging with context ✅
  - [x] No inline comments ✅
  - [x] Code reuse (no duplication) ✅
  - [x] NestJS patterns (DI, module structure) ✅
  - [x] DTO validation ✅
  - [x] TypeORM migration rules ✅
  - [x] React functional components ✅
  - [x] Security rules (secrets, SQL injection) ✅
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Actionable Review Rules](./ARCHITECTURE_AND_FEATURES.md#actionable-review-rules-from-cursor-team-rules)

#### 4.8 SQL Analyzer ✅ COMPLETED
- [x] Create `pr_agent/tools/sql_analyzer.py` ✅
  - [x] Detect SQL in code (TypeORM, raw queries) ✅
  - [x] Check for N+1 queries ✅
  - [x] Check for missing transactions ✅
  - [x] Security: SQL injection patterns ✅
  - [x] TypeORM migration rules ✅
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - SQL Analyzer](./ARCHITECTURE_AND_FEATURES.md#6-sql-analyzer)

#### 4.9 Security Analyzer ✅ COMPLETED
- [x] Create `pr_agent/tools/security_analyzer.py` ✅
  - [x] Hardcoded secrets detection ✅
  - [x] Sensitive data exposure ✅
  - [x] eval() usage detection ✅
  - [x] XSS patterns (innerHTML, dangerouslySetInnerHTML) ✅
  - [x] Weak crypto (MD5, SHA1) ✅
  - [x] JWT without verification ✅
  - [x] CWE IDs for findings ✅
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Security Analyzer](./ARCHITECTURE_AND_FEATURES.md#7-security-analyzer)

#### 4.10 Integrate Analyzers into Reviewer ✅ COMPLETED
- [x] Update `WorkizPRReviewer.run()`: ✅
  - [x] Detect file types in PR ✅
  - [x] Run appropriate language analyzers ✅
  - [x] Run custom rules engine ✅
  - [x] Run SQL analyzer on relevant files ✅
  - [x] Run security analyzer ✅
  - [x] Merge findings into review context ✅

### 4.11 Testing ✅ COMPLETED
- [x] Create test files for language analyzers ✅
- [x] Create test files for custom rules engine ✅
- [x] Create test files for SQL analyzer ✅
- [x] Create test files for security analyzer ✅

### 🚀 4.12 Deployment
- [ ] Deploy updated version to staging (SKIPPED for now)
- [ ] Test on real PRs across different repos
- [ ] Verify Datadog logs show analyzer activity
- [ ] Tune rules based on feedback

### ✅ Phase 4 Completion Criteria
- [x] All language analyzers implemented ✅
- [x] Custom rules working ✅
- [x] SQL analyzer finds issues ✅
- [x] Security analyzer finds issues ✅
- [ ] **Deployed and tested on real PRs** (SKIPPED for now)

**Phase 4 Status: ✅ COMPLETED** (deployment skipped)

---

## Phase 5: RepoSwarm & Cross-Repo Context

**Goal**: Implement cross-repository context using RepoSwarm integration

### Tasks

#### 5.1 RepoSwarm Module Structure
- [ ] Create directory `pr_agent/tools/reposwarm/`
- [ ] Create `__init__.py`
- [ ] Create `type_detector.py` - detect repo type (NestJS, React, PHP, etc.)
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - RepoSwarm Integration](./ARCHITECTURE_AND_FEATURES.md#reposwarm-integration)

#### 5.2 RepoSwarm Prompts
- [ ] Create `pr_agent/tools/reposwarm/prompts/` directory
- [ ] Copy/adapt prompts from original RepoSwarm:
  - [ ] `api_analysis.md`
  - [ ] `architecture_overview.md`
  - [ ] `event_flow.md`
  - [ ] `dependency_analysis.md`
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - RepoSwarm Prompts](./ARCHITECTURE_AND_FEATURES.md#reposwarm-prompts-directory)

#### 5.3 Repository Investigator
- [ ] Create `pr_agent/tools/reposwarm/investigator.py`
  - [ ] `RepositoryInvestigator` class
  - [ ] `investigate(repo_url, branch)` method
  - [ ] Clone repository (sparse checkout)
  - [ ] Detect type using `type_detector`
  - [ ] Load appropriate prompts
  - [ ] Run AI analysis
  - [ ] Store results in `repo_analysis_cache`
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Core Investigator](./ARCHITECTURE_AND_FEATURES.md#core-investigator-adapted-from-reposwarm)

#### 5.4 PubSub Topology Analyzer
- [ ] Create `pr_agent/tools/pubsub_analyzer.py`
  - [ ] Extract publishers from code
  - [ ] Extract subscribers from code
  - [ ] Build topic → service mapping
  - [ ] Store in `pubsub_events` table
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - PubSub Analyzer](./ARCHITECTURE_AND_FEATURES.md#pubsub-analyzer)

#### 5.5 Automated Repository Discovery
- [ ] Update `scripts/cli_admin.py` with `discover` command
  - [ ] Use GitHub API to list all Workiz repos
  - [ ] Auto-detect framework/language from files
  - [ ] Insert into `repositories` table
- [ ] Create `pr_agent/services/discovery_service.py`
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Automated Repository Discovery](./ARCHITECTURE_AND_FEATURES.md#automated-repository-discovery-system)

#### 5.6 Repository Indexing Service
- [ ] Create `pr_agent/services/indexing_service.py`
  - [ ] Clone repository
  - [ ] Split code into chunks
  - [ ] Generate embeddings (OpenAI)
  - [ ] Store in `code_chunks` table
- [ ] Add `index-repos` command to CLI
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Code Indexing](./ARCHITECTURE_AND_FEATURES.md#code-indexing)

#### 5.7 Global Context Provider
- [ ] Create `pr_agent/tools/global_context_provider.py`
  - [ ] `RepoSwarmContextLoader` class
  - [ ] Load analysis from `repo_analysis_cache`
  - [ ] Load related code chunks via vector search
  - [ ] Load PubSub topology
  - [ ] Format context for prompts
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Global Context Provider](./ARCHITECTURE_AND_FEATURES.md#1-global-context-cross-repo-awareness)

#### 5.8 Push Webhook Enhancement
- [ ] Update `/api/v1/webhooks/push` handler:
  - [ ] Trigger incremental indexing
  - [ ] Trigger RepoSwarm analysis
  - [ ] Store commits for Knowledge Assistant
  > 📖 Reference: [DEPLOYMENT_AND_IMPLEMENTATION.md - Push Webhook Handler](./DEPLOYMENT_AND_IMPLEMENTATION.md#push-webhook-handler)

#### 5.9 Organization Webhook Handler
- [ ] Create `/api/v1/webhooks/github/organization` handler
  - [ ] Handle `repository.created` event
  - [ ] Auto-discover new repo
  - [ ] Trigger initial RepoSwarm analysis
  > 📖 Reference: [DEPLOYMENT_AND_IMPLEMENTATION.md - Organization Webhook](./DEPLOYMENT_AND_IMPLEMENTATION.md#organization-webhook-handler)

#### 5.10 Integrate into Reviewer
- [ ] Update `WorkizPRReviewer`:
  - [ ] Load global context at start of review
  - [ ] Include cross-repo API calls in context
  - [ ] Include PubSub relationships in context
  - [ ] Add context to prompts

### 5.11 Initial Data Population
- [ ] Run repository discovery
  ```bash
  python scripts/cli_admin.py discover --orgs Workiz
  ```
- [ ] Run RepoSwarm analysis on all repos
  ```bash
  python scripts/cli_admin.py analyze-repos --all
  ```
- [ ] Index all repositories
  ```bash
  python scripts/cli_admin.py index-repos --all
  ```
  > 📖 Reference: [DEPLOYMENT_AND_IMPLEMENTATION.md - Initial Data Population](./DEPLOYMENT_AND_IMPLEMENTATION.md#3-data-initialization)

### 5.12 Testing
- [ ] Verify cross-repo context appears in reviews
- [ ] Test PR in service A that calls service B's API
- [ ] Verify PubSub relationships are detected
- [ ] Check `repo_analysis_cache` populated correctly

### 🚀 5.13 Deployment
- [ ] Deploy updated version
- [ ] Run initial data population in production
- [ ] Set up organization webhook in GitHub
- [ ] Test cross-repo context on real PRs

### ✅ Phase 5 Completion Criteria
- [ ] All repos discovered and indexed
- [ ] RepoSwarm analysis complete
- [ ] Cross-repo context appears in reviews
- [ ] PubSub topology mapped
- [ ] **Organization webhook handling new repos**

---

## Phase 6: Jira Integration

**Goal**: Connect to Jira for ticket context and history

### Tasks

#### 6.1 Jira Client
- [ ] Create `pr_agent/integrations/jira_client.py`
  - [ ] `JiraClient` class
  - [ ] Authentication with API token
  - [ ] `get_ticket(key)` method
  - [ ] `search_tickets(jql)` method
  - [ ] `get_ticket_history(key)` method
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Jira Integration](./ARCHITECTURE_AND_FEATURES.md#2-jira-integration)

#### 6.2 Jira Sync Service
- [ ] Create `pr_agent/services/jira_sync_service.py`
  - [ ] Full sync: fetch all tickets
  - [ ] Incremental sync: updated tickets
  - [ ] Generate embeddings for tickets
  - [ ] Store in `jira_tickets` table
- [ ] Add `sync-jira` command to CLI
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Jira Sync](./ARCHITECTURE_AND_FEATURES.md#jira-sync-service)

#### 6.3 Jira Context Provider
- [ ] Create `pr_agent/tools/jira_context_provider.py`
  - [ ] Extract ticket key from PR (title, description, branch)
  - [ ] Fetch ticket details and history
  - [ ] Find similar past tickets (vector search)
  - [ ] Format context for prompts
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Jira Context Provider](./ARCHITECTURE_AND_FEATURES.md#jira-context-provider)

#### 6.4 Jira Webhook Handler
- [ ] Create `/api/v1/webhooks/jira` handler
  - [ ] Handle `jira:issue_created`
  - [ ] Handle `jira:issue_updated`
  - [ ] Sync individual ticket on change
  > 📖 Reference: [DEPLOYMENT_AND_IMPLEMENTATION.md - Jira Webhook](./DEPLOYMENT_AND_IMPLEMENTATION.md#jira-webhook-handler)

#### 6.5 Configure Jira Webhook
- [ ] Add `JIRA_BASE_URL`, `JIRA_API_TOKEN`, `JIRA_EMAIL` to secrets
- [ ] Create webhook in Jira (Settings → Webhooks)
- [ ] Point to PR Agent `/api/v1/webhooks/jira`
  > 📖 Reference: [DEPLOYMENT_AND_IMPLEMENTATION.md - Jira Configuration](./DEPLOYMENT_AND_IMPLEMENTATION.md#jira-webhook-configuration)

#### 6.6 Integrate into Reviewer
- [ ] Update `WorkizPRReviewer`:
  - [ ] Extract ticket key from PR
  - [ ] Load Jira context
  - [ ] Check for similar past bugs
  - [ ] Add to review prompt
  - [ ] Generate ticket compliance feedback

### 6.7 Initial Data Population
- [ ] Run full Jira sync
  ```bash
  python scripts/cli_admin.py sync-jira --full
  ```
- [ ] Verify tickets in database

### 6.8 Testing
- [ ] Create PR linked to Jira ticket
- [ ] Verify ticket context in review
- [ ] Test ticket history lookup
- [ ] Test similar bug detection

### 🚀 6.9 Deployment
- [ ] Add Jira secrets to GCloud Secret Manager
- [ ] Deploy updated version
- [ ] Run Jira sync in production
- [ ] Configure Jira webhook
- [ ] Test on PRs with linked tickets

### ✅ Phase 6 Completion Criteria
- [ ] Jira tickets synced
- [ ] Ticket context appears in reviews
- [ ] Similar bugs detected
- [ ] Jira webhook updates tickets automatically

---

## Phase 7: Auto-Fix Agent

**Goal**: Implement automatic code fix agent triggered from GitHub

### Tasks

#### 7.1 Auto-Fix Agent Core
- [ ] Create `pr_agent/tools/autofix_agent.py`
  - [ ] `AutoFixAgent` class
  - [ ] Parse review comments
  - [ ] Generate fixes using advanced LLM (Opus/Gemini)
  - [ ] Apply fixes via GitHub API
  - [ ] Run review loop until complete
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Auto-Fix Agent](./ARCHITECTURE_AND_FEATURES.md#11-auto-fix-agent)

#### 7.2 GitHub Provider Extensions
- [ ] Add methods to `GithubProvider`:
  - [ ] `create_branch(base_branch, new_branch)`
  - [ ] `create_pr(title, body, head, base)`
  - [ ] `get_review_comments(pr_number)`
  - [ ] `update_file(path, content, message, branch)`
  - [ ] `resolve_review_comment(comment_id)`
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - GitHub Provider Extensions](./ARCHITECTURE_AND_FEATURES.md#github-provider-extensions)

#### 7.3 Check Run Button
- [ ] Add `create_check_run()` to GitHub Provider
- [ ] Create check run with "Auto-Fix" button
- [ ] Handle `check_run.requested_action` webhook
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - GitHub Check Run](./ARCHITECTURE_AND_FEATURES.md#triggering-auto-fix)

#### 7.4 Comment Command Handler
- [ ] Add `/auto-fix` command handler
- [ ] Triggered by comment on PR
- [ ] Start Auto-Fix Agent

#### 7.5 Configuration
- [ ] Add `[autofix]` section to configuration:
  ```toml
  [autofix]
  enabled = true
  max_iterations = 5
  models = ["gemini-3-pro", "gemini-2.5-pro"]  # Configurable, more models can be added
  ```

### 7.6 Testing
- [ ] Create PR with intentional issues
- [ ] Trigger `/auto-fix` command
- [ ] Verify fix PR created
- [ ] Verify review loop runs
- [ ] Check fixes resolve comments

### 🚀 7.7 Deployment
- [ ] Deploy updated version
- [ ] Enable auto-fix in configuration
- [ ] Test on staging PRs
- [ ] Monitor API costs (auto-fix uses more tokens)

### ✅ Phase 7 Completion Criteria
- [ ] `/auto-fix` command works
- [ ] Check run button works
- [ ] Fix PR created correctly
- [ ] Review loop completes
- [ ] Comments resolved

---

## Phase 8: Admin UI & Knowledge Assistant

**Goal**: Build web dashboard for management and Q&A interface

### Tasks

#### 8.1 Admin API Setup
- [ ] Create `pr_agent/servers/admin_api.py`
- [ ] Add admin routes to FastAPI app
- [ ] Implement authentication (API key or OAuth)
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Admin API](./ARCHITECTURE_AND_FEATURES.md#12-admin-ui)

#### 8.2 Admin API Endpoints
- [ ] `GET /api/admin/dashboard` - stats and metrics
- [ ] `GET /api/admin/repositories` - list repos
- [ ] `POST /api/admin/repositories/:id/reindex` - trigger reindex
- [ ] `GET /api/admin/rules` - list custom rules
- [ ] `POST /api/admin/rules` - create rule
- [ ] `PUT /api/admin/rules/:id` - update rule
- [ ] `DELETE /api/admin/rules/:id` - delete rule
- [ ] `GET /api/admin/analytics` - review analytics
- [ ] `GET /api/admin/costs` - API cost breakdown
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Admin API Endpoints](./ARCHITECTURE_AND_FEATURES.md#api-implementation)

#### 8.3 Knowledge Assistant Backend
- [ ] Create `pr_agent/tools/knowledge_assistant.py`
  - [ ] `KnowledgeAssistant` class
  - [ ] Question classifier
  - [ ] Context retrieval from multiple sources
  - [ ] LLM answer generation
  - [ ] Source citation
- [ ] Add `POST /api/admin/ask` endpoint
- [ ] Add `GET /api/admin/ask/history/:session_id` endpoint
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Knowledge Assistant](./ARCHITECTURE_AND_FEATURES.md#121-knowledge-assistant)

#### 8.4 GitHub Activity Sync
- [ ] Add `sync-github-activity` command to CLI
- [ ] Sync commits and PRs for Knowledge Assistant
- [ ] Integrate into push webhook
  > 📖 Reference: [DEPLOYMENT_AND_IMPLEMENTATION.md - GitHub Activity Sync](./DEPLOYMENT_AND_IMPLEMENTATION.md#github-activity-sync)

#### 8.5 Admin UI Frontend
- [ ] Create `admin-ui/` directory with React + Vite
- [ ] Install dependencies: React, TailwindCSS, shadcn/ui
- [ ] Create pages:
  - [ ] Dashboard page
  - [ ] Repositories page
  - [ ] Custom Rules page
  - [ ] Analytics page
  - [ ] Knowledge Assistant page
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Frontend Component](./ARCHITECTURE_AND_FEATURES.md#frontend-component-react)

#### 8.6 Dashboard Page
- [ ] Total repos count
- [ ] Total code chunks count
- [ ] Reviews today/week/month
- [ ] API costs chart
- [ ] Recent activity feed

#### 8.7 Repositories Page
- [ ] Table with all repos
- [ ] Framework/language badges
- [ ] Last indexed timestamp
- [ ] RepoSwarm status
- [ ] Reindex button

#### 8.8 Custom Rules Page
- [ ] List all rules
- [ ] Create/Edit rule form
- [ ] Rule categories
- [ ] Enable/disable toggle

#### 8.9 Knowledge Assistant Page
- [ ] Chat interface
- [ ] Suggested questions
- [ ] Source citations
- [ ] Conversation history
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Knowledge Assistant UI](./ARCHITECTURE_AND_FEATURES.md#frontend-component-react)

#### 8.10 NPM Package Management
- [ ] Create `pr_agent/tools/npm_package_analyzer.py`
  - [ ] Query GitHub Packages API
  - [ ] Track internal package versions
  - [ ] Check for outdated dependencies
- [ ] Add `sync-npm` command to CLI
- [ ] Add registry package webhook handler
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - NPM Package Analyzer](./ARCHITECTURE_AND_FEATURES.md#10-internal-npm-package-management)

#### 8.11 Figma Integration (Optional)
- [ ] Create `pr_agent/tools/figma/` directory
- [ ] Implement Figma MCP client
- [ ] Extract design from Figma links in Jira
- [ ] Compare with React component styles
  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Figma Integration](./ARCHITECTURE_AND_FEATURES.md#9-figma-design-verification)

### 8.12 Testing
- [ ] Test all Admin API endpoints
- [ ] Test Knowledge Assistant with various questions
- [ ] Test Admin UI pages
- [ ] Verify analytics accuracy

### 🚀 8.13 Final Deployment
- [ ] Build Admin UI for production
- [ ] Add to Docker image or serve separately
- [ ] Configure ingress for Admin UI
- [ ] Set up authentication
- [ ] Deploy complete system
- [ ] Run full data population
- [ ] Monitor Datadog dashboards

### ✅ Phase 8 Completion Criteria
- [ ] Admin UI fully functional
- [ ] Knowledge Assistant answers questions
- [ ] All analytics working
- [ ] NPM package tracking active
- [ ] **Full production deployment complete**

---

## Final Checklist

### Production Readiness

#### Infrastructure
- [ ] Cloud SQL (PostgreSQL) provisioned
- [ ] GKE cluster configured
- [ ] Helm charts created
- [ ] Secrets in Secret Manager
- [ ] GitHub App configured for production
- [ ] Jira webhook configured
- [ ] Organization webhook configured

#### Data
- [ ] All repositories discovered
- [ ] All repositories indexed (code chunks)
- [ ] RepoSwarm analysis complete
- [ ] Jira tickets synced
- [ ] GitHub activity synced
- [ ] Internal packages synced

#### Monitoring
- [ ] Logs flowing to Datadog
- [ ] Datadog monitors configured
- [ ] Error alerting set up
- [ ] Cost tracking dashboard

#### Documentation
- [ ] README updated
- [ ] Runbooks created
- [ ] On-call procedures documented

---

## Maintenance Tasks (Post-Launch)

### Weekly
- [ ] Review Datadog monitors for issues
- [ ] Check API costs
- [ ] Review auto-fix success rate

### Monthly
- [ ] Review and update custom rules
- [ ] Check for new repos needing configuration
- [ ] Update prompts based on feedback

### Quarterly
- [ ] Update LLM models if better options available
- [ ] Review and optimize costs
- [ ] Gather team feedback on review quality

---

## Quick Reference Links

| Document | Section |
|----------|---------|
| [README.md](./README.md) | Overview, Quick Start |
| [ARCHITECTURE_AND_FEATURES.md](./ARCHITECTURE_AND_FEATURES.md) | All feature implementations |
| [DEPLOYMENT_AND_IMPLEMENTATION.md](./DEPLOYMENT_AND_IMPLEMENTATION.md) | Setup guides, deployment |

---

**Last Updated**: January 11, 2026  
**Version**: 1.1


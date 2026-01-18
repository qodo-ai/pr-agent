# Workiz PR Agent - Development Plan & Tracking

> **Status**: ✅ Phase 4B.12 Complete - Persistent Prompt Storage for Fix in Cursor  
> **Last Updated**: January 18, 2026  
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

#### 4.13 "Fix in Cursor" Button 🔄 IN PROGRESS
> **⚠️ Important Discovery**: GitHub's HTML sanitizer blocks custom URL schemes like `cursor://`. The buttons render but are not clickable. A different approach is needed.

**Current Status (Partial):**
- [x] Add copyable Cursor prompt to code suggestions ✅
- [x] Add vscode.dev fallback link (HTTPS, works in GitHub) ✅
- [x] Create `pr_agent/tools/comment_formatter.py` ✅
- [x] Add `[workiz.cursor_integration]` config section ✅

**🔴 Blocked Items (Cursor security restriction):**
- [ ] ~~cursor://agent/prompt URLs~~ - Only works for Cursor's own Bugbot, not third-party tools
- [x] cursor://file URLs work via redirect page ✅

**💡 Note:** `cursor://agent/prompt?prompt=...` is restricted for security reasons. Only Cursor's Bugbot can pre-fill prompts. Our redirect page opens the file via `cursor://file/{path}:{line}` and shows the prompt for copy/paste.

**📋 New Implementation Plan:**
See Phase 4B below for the corrected approach using GitHub Check Runs.

  > 📖 Reference: [ARCHITECTURE_AND_FEATURES.md - Fix in Cursor Integration](#14-fix-in-cursor-integration)

### ✅ Phase 4 Completion Criteria
- [x] All language analyzers implemented ✅
- [x] Custom rules working ✅
- [x] SQL analyzer finds issues ✅
- [x] Security analyzer finds issues ✅
- [x] "Fix in Cursor" basic implementation (prompts, fallbacks) ✅
- [ ] **Deployed and tested on real PRs** (SKIPPED for now)

**Phase 4 Status: ✅ COMPLETED** (deployment skipped, Fix in Cursor continues in 4B)

---

## Phase 4B: Bugbot-Style Inline Review Comments (REVISED)

**Goal**: Add **individual inline review comments** for findings and suggestions, styled like Cursor Bugbot, with working "Fix in Cursor" and "Fix in Web" buttons. **The standard AI review is always published** - inline comments are **additional** to the AI review, not a replacement.

**How it works:**
- **`/review`**: AI review summary is **always published** + static analyzer findings as inline comments
- **`/improve`**: AI suggestions are published as **individual inline comments** (not batched)

**Key Insight**: Cursor Bugbot uses GitHub's **Pull Request Review API** to create individual review comments placed inline on specific code lines. These appear in BOTH the "Conversation" tab AND the "Files Changed" tab. The buttons are markdown/HTML styled links that go to an HTTPS redirect page.

### Architecture Overview (Bugbot Style)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Current Approach                                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  /review:                                                                   │
│    • AI review summary ALWAYS published (PR type, description, walkthrough) │
│    • Static analyzer findings as individual inline comments                 │
│                                                                             │
│  /improve:                                                                  │
│    • AI suggestions as individual inline comments (NOT batched table)       │
│                                                                             │
│  Features:                                                                  │
│    • Inline on code (Files Changed tab) + Conversation tab                  │
│    • "Fix in Cursor" / "Fix in Web" as markdown button links                │
│    • NOT blocking - just informational comments                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Visual Reference (Cursor Bugbot)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ 📝 cursor [bot] reviewed 4 hours ago          View reviewed changes        │
├────────────────────────────────────────────────────────────────────────────┤
│  react/containers/geniusAi/settingsPage/SettingsPage.tsx                   │
│       85 | +     } else {                                                  │
│       86 | +         directToBilling();                                    │
│       87 | +     }                                                         │
│       88 | + };                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│ 🤖 cursor [bot] 4 hours ago                                                │
│                                                                            │
│ **Upgrade action bypasses unsaved changes confirmation**                   │
│                                                                            │
│ **Medium Severity**                                                        │
│                                                                            │
│ The `onClickUpgrade` function calls `onClose?.(false)` which triggers      │
│ `handleClose` in `SettingsModal`. If the form has unsaved changes,         │
│ `handleClose` shows a confirmation modal and returns early. However,       │
│ execution in `onClickUpgrade` continues regardless...                      │
│                                                                            │
│ ┌──────────────┐  ┌─────────────┐                                         │
│ │ 🔧 Fix in Cursor │  │ ↗ Fix in Web │                                     │
│ └──────────────┘  └─────────────┘                                         │
│                                                                            │
│ 😊                                                                         │
│ ┌────────────────────────────────────────────────────────────────────────┐│
│ │ Reply...                                                               ││
│ └────────────────────────────────────────────────────────────────────────┘│
│ [Resolve conversation]                                                     │
└────────────────────────────────────────────────────────────────────────────┘
```

### Tasks

#### 4B.1 Remove Default Batched Output ✅ COMPLETED
- [x] **Disable** the existing `publish_comment()` for review findings ✅
- [x] **Disable** the existing code suggestions table format ✅
- [x] Remove Check Run approach (too limited, not the right UX) ✅
- [x] Config flag: `use_inline_comments = true` (default) ✅

#### 4B.2 GitHub PR Review API Integration ✅ COMPLETED
- [x] Add `create_review_with_inline_comments()` to `GithubProvider`: ✅
  ```python
  def create_review_with_comments(
      self,
      comments: list[dict],  # [{path, line, body}, ...]
      event: str = "COMMENT"  # "COMMENT" = non-blocking, "REQUEST_CHANGES" = blocking
  ) -> dict:
      """
      Create a PR review with multiple inline comments.
      
      POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews
      
      Each comment appears:
      - Inline on the code in "Files Changed" tab
      - In the "Conversation" tab as part of the review thread
      """
      payload = {
          "commit_id": self.last_commit_id.sha,
          "event": event,  # "COMMENT" for non-blocking
          "comments": [
              {
                  "path": c["path"],
                  "line": c["line"],  # or "start_line" + "line" for multi-line
                  "body": c["body"]
              }
              for c in comments
          ]
      }
      # POST to /repos/{owner}/{repo}/pulls/{pull_number}/reviews
  ```
- [x] Support multi-line comments with `start_line` + `line` for code ranges ✅
- [x] Always use `event: "COMMENT"` (non-blocking) ✅

#### 4B.3 Cursor Redirect Service ✅ COMPLETED
- [x] Host HTTPS redirect page at our server: `/api/v1/cursor-redirect` ✅
- [x] The page: ✅
  1. Opens file via `cursor://file/{path}:{line}:1`
  2. Shows "Opening file in Cursor..." message
  3. Shows prompt prominently for copy/paste (Cursor doesn't support pre-filling prompts from third-party)
- [x] URL format: `https://our-server.com/api/v1/cursor-redirect?prompt={encoded_prompt}&file={path}&line={num}` ✅

**⚠️ Important:** `cursor://agent/prompt` only works for Cursor's own Bugbot. Third-party tools must use `cursor://file/` and show prompts for copy/paste.

Example HTML page:
```html
<!DOCTYPE html>
<html>
<head>
  <title>Opening Cursor...</title>
  <style>
    body { font-family: system-ui; max-width: 600px; margin: 50px auto; padding: 20px; }
    .prompt-box { background: #f4f4f4; padding: 15px; border-radius: 8px; white-space: pre-wrap; }
    button { margin-top: 10px; padding: 10px 20px; cursor: pointer; }
  </style>
</head>
<body>
  <h2>Opening Cursor...</h2>
  <p>If Cursor doesn't open automatically, copy the prompt below:</p>
  <div class="prompt-box" id="prompt"></div>
  <button onclick="copyPrompt()">📋 Copy Prompt</button>
  <script>
    const params = new URLSearchParams(window.location.search);
    const prompt = decodeURIComponent(params.get('prompt') || '');
    document.getElementById('prompt').textContent = prompt;
    
    // Try to open file in Cursor (prompt pre-fill doesn't work for third-party)
    // Use cursor://file/{path}:{line}:{column} to open at the correct location
    const file = params.get('file') || '';
    const line = params.get('line') || '1';
    const cursorUrl = file ? `cursor://file/${file}:${line}:1` : 'cursor://'
    window.location = cursorUrl;
    
    function copyPrompt() {
      navigator.clipboard.writeText(prompt);
      alert('Copied!');
    }
  </script>
</body>
</html>
```

#### 4B.4 Format Individual Comment Body ✅ COMPLETED
- [x] Create `format_inline_comment()` in `inline_comment_formatter.py` ✅:
  ```python
  def format_inline_review_comment(
      title: str,
      severity: str,  # "High", "Medium", "Low"
      description: str,
      file_path: str,
      line: int,
      suggestion: str = "",
      cursor_redirect_url: str = "",
  ) -> str:
      """
      Format a single inline review comment like Cursor Bugbot.
      """
      body = f"""**{title}**

**{severity} Severity**

{description}
"""
      if suggestion:
          body += f"\n**Suggested fix:** {suggestion}\n"
      
      # Buttons as markdown links styled with emoji
      cursor_url = f"{cursor_redirect_url}?prompt={encode_prompt(...)}&file={file_path}&line={line}"
      vscode_url = f"https://vscode.dev/github/{repo}/{branch}/{file_path}#L{line}"
      
      body += f"""
[🔧 Fix in Cursor]({cursor_url}) | [↗ Fix in Web]({vscode_url})
"""
      return body
  ```

#### 4B.5 Update WorkizPRReviewer ✅ COMPLETED
- [x] **Replace** current review output completely ✅
- [x] Collect all findings (analyzer + rules + AI review) ✅
- [x] For each finding, format as individual inline comment ✅
- [x] Call `create_review_with_inline_comments()` with all comments ✅
- [x] Use `event: "COMMENT"` (non-blocking) ✅
- [x] Remove the batched persistent comment (disabled via publish_output=False) ✅
- [x] Remove Check Run creation (no longer called) ✅

New flow:
```python
async def run(self):
    # ... existing analysis ...
    
    # Collect all findings
    all_findings = self._collect_all_findings()
    
    # Format each as inline comment
    review_comments = []
    for finding in all_findings:
        body = format_inline_review_comment(
            title=finding["title"],
            severity=finding["severity"],
            description=finding["message"],
            file_path=finding["file"],
            line=finding["line"],
            suggestion=finding.get("suggestion", ""),
            cursor_redirect_url=self.cursor_redirect_url,
        )
        review_comments.append({
            "path": finding["file"],
            "line": finding["line"],
            "body": body
        })
    
    # Create non-blocking review with inline comments
    self.git_provider.create_review_with_comments(
        comments=review_comments,
        event="COMMENT"  # Non-blocking!
    )
```

#### 4B.6 Update WorkizPRCodeSuggestions ✅ COMPLETED
- [x] Same approach for code suggestions ✅
- [x] Each suggestion as an individual inline comment ✅
- [x] Include "Fix in Cursor" and "Fix in Web" buttons ✅
- [x] Remove the batched suggestions table (disabled via publish_output=False) ✅

#### 4B.7 Configuration ✅ COMPLETED
- [x] Add config options: ✅
  ```toml
  [workiz.inline_comments]
  enabled = true                    # Use inline comments instead of batched
  max_comments = 20                 # Limit to avoid spam
  cursor_redirect_url = ""          # Uses server URL if empty
  show_web_fallback = true          # Include vscode.dev link
  severity_threshold = "low"        # Only show findings >= this severity
  ```

#### 4B.8 Handle Comment Limitations ✅ COMPLETED
- [x] GitHub limits reviews to ~60 comments max ✅
- [x] Implement smart filtering: ✅
  - Prioritize higher severity findings
  - Limit by max_comments config
  - Severity threshold filtering
- [x] Log when limit is reached ✅

### 📖 References
- [GitHub Pull Request Review API](https://docs.github.com/en/rest/pulls/reviews#create-a-review-for-a-pull-request)
- [GitHub PR Review Comments](https://docs.github.com/en/rest/pulls/comments)
- Cursor Bugbot behavior analysis (from screenshots)

### ✅ Phase 4B Completion Criteria ✅ ALL COMPLETED
- [x] Individual inline comments appear on each finding ✅
- [x] Comments visible in BOTH "Conversation" tab AND "Files Changed" tab ✅
- [x] "Fix in Cursor" button opens redirect page → Cursor ✅
- [x] "Fix in Web" button opens vscode.dev at correct file/line ✅
- [x] NOT a blocking check - uses `event: "COMMENT"` ✅
- [x] Default batched review/suggestions DISABLED ✅
- [ ] End-to-end tested on real PR (next step)
- [x] Matches Cursor Bugbot UX ✅

**Phase 4B Status: ✅ IMPLEMENTATION COMPLETE** (pending end-to-end test)

### Phase 4B.9: Bug Fixes and Improvements ✅ COMPLETED

**Issues fixed:**

1. **File Type Filtering** ✅
   - Added `SKIP_ANALYZER_EXTENSIONS` to skip non-code files (.md, .json, .toml, etc.)
   - Prevents false positives from analyzers pattern-matching documentation
   - Files: `workiz_pr_reviewer.py`

2. **Finding Deduplication** ✅
   - Added `_deduplicate_findings()` to remove duplicate findings by (file, line, rule_id)
   - Prevents same issue being reported multiple times
   - Files: `workiz_pr_reviewer.py`

3. **cursor_redirect_url Configuration** ✅
   - Removed hardcoded ngrok URL from config
   - Auto-builds from `WEBHOOK_URL` env var when empty
   - Documented configuration options for local/production
   - Files: `configuration.toml`, `workiz_pr_reviewer.py`, `workiz_pr_code_suggestions.py`

4. **Org/Repo/Branch Extraction** ✅
   - Fixed `_parse_repo_info()` to use `git_provider` for accurate data
   - Properly extracts org, repo, and HEAD branch
   - Fixes "Fix in Web" vscode.dev URLs pointing to wrong location
   - Files: `workiz_pr_reviewer.py`, `workiz_pr_code_suggestions.py`

5. **URL Encoding Fix** ✅
   - Removed double-encoding of prompt in cursor redirect
   - FastAPI auto-decodes query params, so extra `unquote()` was breaking prompts
   - Added HTML escaping for XSS prevention
   - Files: `github_app.py`

6. **AI Review Always Published** ✅
   - Fixed issue where AI review was suppressed when inline comments enabled
   - `/review` now ALWAYS publishes AI review summary (PR description, type, walkthrough)
   - Inline comments are ADDITIONAL to AI review, not a replacement
   - `/improve` still suppresses batched suggestions (uses inline comments instead)
   - Files: `workiz_pr_reviewer.py`, `configuration.toml`

### Phase 4B.10: Smart Line Adjustment for Inline Comments ✅ COMPLETED

**Problem:** AI suggestions often target "context lines" (unchanged lines shown around changes in the diff), but GitHub's API only allows inline comments on actual diff lines (lines with `+` or `-` prefixes).

**Solution:** Implemented smart line adjustment that:
1. Parses the PR diff to extract valid line ranges for each file
2. For each suggestion/finding, validates if the line is in the diff
3. If inside a diff hunk → post directly
4. If within 10 lines of a hunk boundary → adjust to nearest hunk line
5. If far from any hunk → skip with logging (or could fall back to PR comment)

**Implementation:**
- Added `_get_diff_hunk_ranges()` - Parses diff to get valid line ranges per file
- Added `_adjust_suggestion_to_diff()` - Smart adjustment for AI suggestions
- Added `_adjust_finding_to_diff()` - Smart adjustment for static analyzer findings
- Added `side` parameter support (`RIGHT` for new lines, `LEFT` for removed lines)
- Updated `_publish_inline_suggestion_comments()` and `_publish_inline_review_comments()`
- Files: `workiz_pr_code_suggestions.py`, `workiz_pr_reviewer.py`

### Phase 4B.11: Comment Format Unification 🔲 TODO

**Problem:** Static analyzer comments (`format_inline_comment()`) and AI suggestion comments (`format_suggestion_comment()`) have different formats:

| Feature | Static Analyzer | AI Suggestion |
|---------|-----------------|---------------|
| Title | `**[RULE_ID] Title**` | `**Summary**` |
| Severity | `**High Severity**` | `*Label* (e.g., "Enhancement")` |
| Code Diff | None | Collapsible code diff |
| Structure | Title → Severity → Description | Title → Label → Description → Diff |

**Goal:** Unify both formats so they:
1. Look identical in structure and styling
2. Use the same severity/issue classification (High/Medium/Low)
3. Enable consistent filtering and tooling based on severity
4. Map AI suggestion labels to severity levels

**Tasks:**
- [ ] Define unified severity mapping (AI labels → severity levels)
- [ ] Create single `format_unified_inline_comment()` function
- [ ] Update static analyzer findings to use unified format
- [ ] Update AI suggestions to use unified format  
- [ ] Add optional code diff collapsible section to both
- [ ] Update documentation

### Phase 4B.12: Persistent Prompt Storage for Fix in Cursor ✅ COMPLETED

**Problem:** Prompts for "Fix in Cursor" were stored in-memory with a 1-hour TTL. This limited analytics capabilities and prompts were lost on server restart.

**Solution:** Implemented persistent PostgreSQL storage with full tracking:

**Implementation:**
- Created `migrations/002_cursor_fix_prompts.sql` - new table with full context and tracking
- Created `pr_agent/db/cursor_prompts.py` - `save_prompt()`, `get_prompt()`, `get_prompt_analytics()`
- Updated `pr_agent/servers/github_app.py` - DB storage with in-memory fallback
- Updated `pr_agent/tools/inline_comment_formatter.py` - pass tracking context to URLs
- Updated `pr_agent/tools/workiz_pr_reviewer.py` and `workiz_pr_code_suggestions.py` - pass PR context

**Features:**
- [x] Persistent storage in PostgreSQL with UUID primary keys ✅
- [x] Full PR context tracking (repository, pr_number, pr_url) ✅
- [x] Comment context (comment_type, severity, finding_id) ✅
- [x] Access tracking (accessed_at, access_count, accessed_by) ✅
- [x] Analytics endpoint for click-through rates ✅
- [x] Graceful fallback to in-memory when DB unavailable ✅

**Database Schema:**
```sql
CREATE TABLE cursor_fix_prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt TEXT NOT NULL,
    file_path TEXT,
    line_number INT,
    repository VARCHAR(255),
    pr_number INT,
    pr_url TEXT,
    comment_type VARCHAR(50),  -- 'static_analyzer', 'ai_suggestion'
    severity VARCHAR(20),
    finding_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP,
    access_count INT DEFAULT 0,
    accessed_by VARCHAR(255)
);
```

### Phase 4B.13: API Key Authentication for Extension ✅ COMPLETED

**Problem:** The `/api/v1/prompt/{id}` endpoint was publicly accessible, allowing anyone to retrieve stored prompts without authentication.

**Solution:** Implemented API key authentication for the extension endpoint while keeping webhooks and redirect public:

**Implementation:**
- Updated `pr_agent/servers/github_app.py` - Added `validate_extension_api_key()` dependency
- Updated `cursor-extension/src/extension.ts` - Send `Authorization: Bearer` header with API key
- Updated `.github/workflows/build-cursor-extension.yml` - Inject API key at build time
- Updated `env.example` and deployment docs - Added `EXTENSION_API_KEY` configuration
- Updated all documentation - Added security information

**Features:**
- [x] API key validation for `/api/v1/prompt/{id}` endpoint ✅
- [x] Bearer token authentication in extension ✅
- [x] Build-time API key injection (not in source code) ✅
- [x] Dev mode support (empty key = no validation) ✅
- [x] Structured logging of auth attempts ✅

**Security Model:**
| Endpoint | Auth Method | Status |
|----------|-------------|--------|
| `/api/v1/prompt/{id}` | API Key (Bearer token) | ✅ Protected |
| `/api/v1/cursor-redirect` | None (public) | ✅ Remains public |
| `/api/v1/github_webhooks` | GitHub HMAC signature | ✅ Already protected |
| `/api/v1/marketplace_webhooks` | GitHub HMAC signature | ✅ Already protected |

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

**Last Updated**: January 18, 2026  
**Version**: 1.2


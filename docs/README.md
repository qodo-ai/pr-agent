# Workiz PR Agent

A customized fork of [qodo-ai/pr-agent](https://github.com/qodo-ai/pr-agent) tailored for Workiz's development workflow, supporting multi-language code review, cross-repository context, Jira integration, Figma design verification, and automated code fixes.

## 📚 Documentation Index

| Document | Description |
|----------|-------------|
| [**Development Plan**](./DEVELOPMENT_PLAN.md) | 📋 **Start here!** Phased tasks, milestones, tracking |
| [Architecture & Features](./ARCHITECTURE_AND_FEATURES.md) | System architecture, all features, code implementations |
| [Deployment & Implementation](./DEPLOYMENT_AND_IMPLEMENTATION.md) | Setup guides, deployment, checklists |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker Desktop
- GitHub Personal Access Token
- Google API Key (Gemini - default model)
- (Optional) Anthropic API Key (Claude - for future use)
- (Optional) OpenAI API Key (for future use)
- (Optional) Jira API Token
- (Optional) Figma Access Token (for design verification)

### Local Development (5 minutes)

```bash
# Clone and setup
cd ~/Documents/Github
git clone https://github.com/Workiz/workiz-pr-agent.git
cd workiz-pr-agent

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start database (PostgreSQL with pgvector)
docker-compose --profile with-db up -d db

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run database migrations
python scripts/run_migrations.py

# Start server
python -m uvicorn pr_agent.servers.github_app:app --port 8000 --reload
```

See [Deployment & Implementation](./DEPLOYMENT_AND_IMPLEMENTATION.md) for detailed setup instructions.

---

## 🎯 Feature Summary

### Core Review Capabilities

| Feature | Description | Status |
|---------|-------------|--------|
| **WorkizPRReviewer** | Enhanced `/review` with Workiz coding standards | ✅ Implemented |
| **WorkizPRCodeSuggestions** | Enhanced `/improve` with Workiz patterns | ✅ Implemented |
| **🔧 Inline Comments** | Bugbot-style inline comments with Fix in Cursor buttons | ✅ Implemented |
| **Custom Rules Engine** | Workiz-specific code style rules | ✅ Implemented |
| **Language Analyzers** | PHP, JS/TS, NestJS, React, Python | ✅ Implemented |
| **SQL Analyzer** | TypeORM patterns, N+1, injection, transactions | ✅ Implemented |
| **Security Analyzer** | Secrets, XSS, eval(), weak crypto detection | ✅ Implemented |
| **MongoDB Analyzer** | Missing indexes, $regex patterns, aggregations | 🔲 Planned |
| **Elasticsearch Analyzer** | Wildcard queries, deep pagination, mappings | 🔲 Planned |
| **PubSub Analyzer** | Event topology and pattern validation | 🔲 Planned |

### Integrations

| Integration | Purpose | Status |
|-------------|---------|--------|
| **GitHub** | Webhooks, PR reviews, inline comments | ✅ Implemented |
| **Cursor Extension** | "Fix in Cursor" with pre-filled AI prompts | ✅ Implemented |
| **Jira** | Ticket context, history, compliance | 🔲 Planned |
| **RepoSwarm** | Cross-repo architecture context (adapted from [royosherove/repo-swarm](https://github.com/royosherove/repo-swarm)) | 🔲 Planned |
| **Figma** | Design verification for frontend | 🔲 Planned |
| **GitHub Packages** | Internal @workiz package version tracking | 🔲 Planned |

### Advanced Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Cost Tracking** | API usage and cost monitoring | ✅ Implemented |
| **Prompt Analytics** | Track "Fix in Cursor" usage and click-through | ✅ Implemented |
| **Auto-Fix Agent** | AI-powered automatic code fixes | 🔲 Planned |
| **Auto-Discovery** | Automatic repo/project detection | 🔲 Planned |
| **Admin UI** | Web dashboard for management | 🔲 Planned |
| **🤖 Knowledge Assistant** | Ask questions about your codebase | 🔲 Planned |

### 🔧 Bugbot-Style Inline Comments (NEW!)

**How it works:**
- **`/review`**: AI review summary is **always published** + static analyzer findings as inline comments
- **`/improve`**: AI suggestions are published as **individual inline comments** (not batched)

Every code finding and suggestion is posted as an **individual inline comment** on the specific code line, appearing in both "Files Changed" and "Conversation" tabs - just like Cursor Bugbot!

**Features:**
- **AI Review Always Published** - PR description, type, and walkthrough are always visible
- **Individual inline comments** - Each static analyzer finding and AI suggestion becomes its own comment
- **Visible in both tabs** - Shows in "Files Changed" AND "Conversation" 
- **Non-blocking** - Comments don't block PR merging
- **Fix buttons** - Each comment includes action buttons:
  - **🔧 Fix in Cursor** → Opens redirect page to launch Cursor with AI prompt
  - **↗ Fix in Web** → Opens VS Code Web (vscode.dev) at the exact line

```
                    Files Changed Tab
    ┌────────────────────────────────────────────────────────┐
    │ src/user.service.ts                                    │
    ├────────────────────────────────────────────────────────┤
    │  41 │   let count = 0;                                 │
    │     │   ┌──────────────────────────────────────────┐  │
    │     │   │ **[TS001] Use const instead of let**     │  │
    │     │   │ **High Severity**                        │  │
    │     │   │                                          │  │
    │     │   │ Variable 'count' is never reassigned.    │  │
    │     │   │ Use const for immutability.              │  │
    │     │   │                                          │  │
    │     │   │ [🔧 Fix in Cursor] | [↗ Fix in Web]     │  │
    │     │   └──────────────────────────────────────────┘  │
    │  42 │   users.forEach(user => {                       │
    └────────────────────────────────────────────────────────┘
```

**Configuration** (`configuration.toml`):

```toml
[workiz.inline_comments]
enabled = true              # Enable inline comments (in addition to standard AI review)
max_comments = 20           # Maximum comments per PR
severity_threshold = "low"  # "high", "medium", or "low"
cursor_redirect_url = ""    # See below for configuration options
show_web_fallback = true    # Include vscode.dev link
```

**Cursor Redirect URL Configuration:**

| Environment | cursor_redirect_url Setting |
|-------------|----------------------------|
| **Local dev (ngrok)** | Leave empty `""` - auto-uses `WEBHOOK_URL` env var + `/api/v1/cursor-redirect` |
| **Production** | `"https://pr-agent.workiz.com/api/v1/cursor-redirect"` |

**🔌 Cursor Extension (Optional but Recommended):**

Install the **Workiz PR Agent Cursor Extension** for the best experience:
- **With extension**: Clicking "Fix in Cursor" opens the file AND pre-fills the AI chat with the fix prompt!
- **Without extension**: Opens the file only; prompt shown on redirect page for copy/paste
- **Auto-update**: Extension checks for updates daily and prompts to install new versions

See [`cursor-extension/README.md`](../cursor-extension/README.md) for installation.

**📊 Prompt Storage & Analytics:**

"Fix in Cursor" prompts are stored persistently in PostgreSQL (with in-memory fallback) enabling:
- **Full tracking**: repository, PR number, comment type, severity, finding ID
- **Access analytics**: Click-through rates, access counts, who accessed
- **No URL limits**: Prompts stored by UUID reference, avoiding URL length restrictions

**For local development with ngrok:**
1. Start ngrok: `ngrok http 8000`
2. Set `WEBHOOK_URL` environment variable to the ngrok URL
3. Leave `cursor_redirect_url = ""` in config
4. The system automatically appends `/api/v1/cursor-redirect`

**Smart Line Adjustment:**

AI suggestions may target "context lines" (unchanged lines in the diff), which GitHub's API doesn't allow. Smart line adjustment automatically:
- Validates if the suggested line is actually in the PR diff
- Adjusts comments within 10 lines of a hunk to the nearest valid line
- Logs when comments are skipped (too far from any changed code)

See [ARCHITECTURE_AND_FEATURES.md - Inline Comments](./ARCHITECTURE_AND_FEATURES.md) for implementation details.

### 🤖 Knowledge Assistant (NEW!)

Ask questions about your entire codebase in natural language:

```
"How does the notification service communicate with users-service?"
"Who has been working on the checkout flow recently?"
"What PRs were merged to payments this month?"
"What bugs were reported for the mobile app?"
"Which services subscribe to USER_CREATED event?"
"Where is the payment processing logic?"
```

Uses RAG to search across code, architecture (RepoSwarm), Jira tickets, commits, PRs, and contributor history. Available in the Admin UI.

### Automation Summary

| Process | Trigger | Status |
|---------|---------|--------|
| **PR Review** | GitHub webhook (`pull_request`) | ✅ Implemented |
| **Inline Comments** | GitHub webhook (`issue_comment: /review`, `/improve`) | ✅ Implemented |
| **Code Indexing** | GitHub webhook (`push` to main) | 🔲 Planned |
| **RepoSwarm Analysis** | GitHub webhook (`push` to main) | 🔲 Planned |
| **Repo Discovery** | GitHub org webhook (`repository.created`) | 🔲 Planned |
| **Jira Sync** | Jira webhook (`issue_created/updated`) | 🔲 Planned |
| **NPM Packages Sync** | GitHub webhook (`registry_package.published`) | 🔲 Planned |

Webhooks enable real-time updates once fully implemented. Weekly reconciliation CronJob serves as safety net.

---

## 🏗️ Supported Stack

### Languages & Frameworks

| Stack | Analyzer | Key Rules |
|-------|----------|-----------|
| **PHP** | `PHPAnalyzer` | No raw SQL, no `dd()`, N+1 detection |
| **JavaScript** | `JavaScriptAnalyzer` | No `console.log`, no `var`, callback hell |
| **TypeScript** | `TypeScriptAnalyzer` | Type safety, `const` over `let` |
| **NestJS** | `NestJSAnalyzer` | DI patterns, structured logging, PubSub |
| **React** | `ReactAnalyzer` | Hooks rules, key props, style consistency |
| **Python** | `PythonAnalyzer` | No `print()`, async patterns, FastAPI |

### Databases

| Database | Analyzer | Key Checks | Status |
|----------|----------|------------|--------|
| **MySQL/PostgreSQL** | `SQLAnalyzer` | N+1, SQL injection, transactions, TypeORM | ✅ Implemented |
| **MongoDB** | `MongoDBAnalyzer` | Missing indexes, $regex without anchor | 🔲 Planned |
| **Elasticsearch** | `ElasticsearchAnalyzer` | Wildcard queries, deep pagination | 🔲 Planned |

### Workiz Internal Packages

All `@workiz` packages are hosted on **GitHub Packages** (not npmjs.org).

**Registry**: `https://npm.pkg.github.com/`
**Source**: `architecture/packages/` monorepo
**Publishing**: Automatic via `release-packages.yml` workflow on push to `main`

| Package | Version | Purpose |
|---------|---------|---------|
| `@workiz/all-exceptions-filter` | 1.1.2 | Global NestJS exception handling |
| `@workiz/config-loader` | 1.0.15 | Configuration with GCloud Secrets |
| `@workiz/node-logger` | 2.0.0 | Structured logging (Winston) |
| `@workiz/pubsub-decorator-reflector` | 1.3.2 | PubSub decorators for NestJS |
| `@workiz/pubsub-publish-client` | - | PubSub publishing client |
| `@workiz/redis-nestjs` | - | Redis integration for NestJS |
| `@workiz/jwt-headers-generator` | - | JWT header utilities |
| `@workiz/socket-io-updater` | - | Socket.io updates |
| `@workiz/gcs-nestjs` | - | Google Cloud Storage integration |
| `@workiz/elasticsearch-nestjs` | - | Elasticsearch integration |
| `@workiz/feature-flag-getter` | - | Feature flag utilities |
| `@workiz/message-builder` | - | Message building utilities |
| `@workiz/xss-security` | - | XSS protection utilities |
| `@workiz/contracts` | - | Shared TypeScript contracts |

**.npmrc Configuration**:
```
@workiz:registry=https://npm.pkg.github.com/
//npm.pkg.github.com/:_authToken=${NPM_READONLY_TOKEN}
```

---

## 📋 Actionable Review Rules

These rules are automatically enforced during PR reviews:

### Code Quality

| Rule | Trigger | Action |
|------|---------|--------|
| **Test Coverage** | `.ts` file without `.spec.ts` | Comment: "Missing test coverage" |
| **Code Duplication** | Similar code blocks | Comment: "Consider extracting to utility" |
| **Function Size** | Function > 30 lines | Comment: "Consider splitting function" |
| **Nesting Depth** | Nesting > 3 levels | Comment: "Reduce nesting depth" |

### NestJS Patterns

| Rule | Trigger | Action |
|------|---------|--------|
| **Structured Logging** | `logger.*` without context | Comment: "Add context object" |
| **Functional Style** | `let` instead of `const` | Comment: "Use const and immutable operations" |
| **Dependency Injection** | `new Service()` in code | Comment: "Use constructor injection" |
| **PubSub Patterns** | Missing `@PubSubAsyncAcknowledge` | Comment: "Add async acknowledge decorator" |

### Security

| Rule | Trigger | Action |
|------|---------|--------|
| **SQL Injection** | String interpolation in queries | Comment: "Use parameterized queries" |
| **Hardcoded Secrets** | Regex matches for secrets | Comment: "Use environment variables" |
| **Sensitive Data** | Passwords in logs | Comment: "Use maskSensitive()" |

---

## 🔧 Configuration

### Main Configuration (`pr_agent/settings/configuration.toml`)

```toml
[config]
model = "gemini-3-pro"
fallback_models = ["gemini-2.5-pro"]  # Additional models can be added later
git_provider = "github"

[workiz]
enable_cross_repo_context = true
enable_jira_integration = true
enable_custom_rules = true
enable_sql_review = true
enable_enhanced_security = true
enable_npm_analysis = true
max_review_comments = 15
github_orgs = ["Workiz"]

[jira]
base_url = "https://workiz.atlassian.net"
```

### Secrets (`.secrets.toml` or GCloud Secret Manager)

```toml
[openai]
key = "sk-..."

[github]
user_token = "ghp_..."
organization = "Workiz"
main_branches = ["workiz.com", "main", "master"]

[jira]
api_token = "..."
email = "your-email@workiz.com"

[workiz]
database_url = "postgresql://..."
npm_org = "@workiz"
```

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              Workiz PR Agent System                                   │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                       │
│   External Systems                                                                    │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │
│   │  GitHub  │  │   Jira   │  │  Figma   │  │ GitHub   │  │  RepoSwarm Hub       │  │
│   │  (PRs)   │  │ (Tickets)│  │ (Designs)│  │ Packages │  │  (.arch.md files)    │  │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘  │
│        │             │             │             │                    │              │
│        ▼             ▼             ▼             ▼                    ▼              │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │                      PR Agent Core (FastAPI on GKE)                           │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │   │
│   │  │   Context   │  │ Specialized │  │   Custom    │  │    Output           │ │   │
│   │  │   Loaders   │  │   Agents    │  │   Rules     │  │    Handlers         │ │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │   │
│   └─────────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                             │
│                                        ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │                    LLM Layer (via LiteLLM)                                    │   │
│   │  Gemini 3 Pro (default) │ Gemini 2.5 Pro (fallback) │ (more coming)        │   │
│   └─────────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                             │
│                                        ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │                     Cloud SQL PostgreSQL + pgvector                           │   │
│   │  repositories │ code_chunks │ jira_tickets │ custom_rules │ api_usage        │   │
│   └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### Deployment Infrastructure

| Component | Technology |
|-----------|------------|
| **Container Registry** | Google Container Registry (GCR) |
| **Orchestration** | Google Kubernetes Engine (GKE) |
| **Deployment** | Helm charts + GitHub Actions (`Workiz/workiz-actions/deploy-microservice`) |
| **Secrets** | Google Cloud Secret Manager (naming: `<env>-pr-agent`) |
| **Database** | Cloud SQL PostgreSQL with pgvector |
| **Domains** | `pr-agent-staging.workiz.dev`, `pr-agent.workiz.dev` |

### RepoSwarm Integration

Cross-repository architecture discovery is powered by an adaptation of [RepoSwarm](https://github.com/royosherove/repo-swarm):

| Original RepoSwarm | PR Agent Adaptation |
|--------------------|---------------------|
| Temporal workflows | Simple async Python |
| DynamoDB caching | PostgreSQL |
| Direct API calls | LiteLLM (model-agnostic) |
| Standalone service | Embedded in PR Agent |
| `prompts/` directory | ✅ Kept as-is |
| `src/investigator/` | ✅ Adapted |

The prompts and analysis logic from RepoSwarm are integrated directly into PR Agent, eliminating the need for a separate service or Temporal infrastructure.

---

## 📅 Implementation Timeline

### MVP (4 Weeks)

| Week | Focus | Deliverables |
|------|-------|--------------|
| **Week 1** | Foundation | PostgreSQL setup, webhook handler, configuration |
| **Week 2** | Core Review | Custom rules engine, language analyzers |
| **Week 3** | RepoSwarm | Integration, context loader, prompts |
| **Week 4** | Testing | Unit tests, bug fixes, documentation |

### Full Feature Set (8 Weeks)

| Week | Focus | Deliverables |
|------|-------|--------------|
| **Week 5** | Jira | Full Jira sync, ticket context |
| **Week 6** | Auto-Fix | Auto-fix flow, GitHub button |
| **Week 7** | Admin UI | React dashboard, analytics |
| **Week 8** | Production | GKE deployment, Datadog dashboards |

---

## 🔗 References

- [Original PR Agent Documentation](https://qodo-merge-docs.qodo.ai/)
- [RepoSwarm by Roy Osherove](https://github.com/royosherove/repo-swarm) - AI-powered multi-repo architecture discovery (adapted for PR Agent)
- [Figma MCP](https://modelcontextprotocol.io/examples)
- [GCloud Secret Manager](https://cloud.google.com/secret-manager)
- [Temporal](https://temporal.io/) - Original RepoSwarm orchestration (not used in our adaptation)

---

## 📞 Support

For questions or issues:
1. Check the detailed documentation in this folder
2. Review the original [qodo-ai/pr-agent](https://github.com/qodo-ai/pr-agent) repository
3. Contact the DevOps team

---

*Last updated: January 18, 2026*

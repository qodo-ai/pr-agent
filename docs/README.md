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
| **🔧 Fix in Cursor** | One-click links to open issues in Cursor IDE | ✅ Planned |
| **Custom Rules Engine** | Workiz-specific code style rules | ✅ Implemented |
| **Language Analyzers** | PHP, JS/TS, NestJS, React, Python | ✅ Implemented |
| **Database Analyzers** | MySQL, MongoDB, Elasticsearch, PostgreSQL | ✅ Planned |
| **Security Analyzer** | Traefik-aware security checks | ✅ Implemented |
| **PubSub Analyzer** | Event topology and pattern validation | ✅ Planned |

### Integrations

| Integration | Purpose | Status |
|-------------|---------|--------|
| **GitHub** | Webhooks, PR reviews, comments | ✅ Base exists |
| **Jira** | Ticket context, history, compliance | ✅ Planned |
| **RepoSwarm** | Cross-repo architecture context (adapted from [royosherove/repo-swarm](https://github.com/royosherove/repo-swarm)) | ✅ Planned |
| **Figma** | Design verification for frontend | ✅ Planned |
| **GitHub Packages** | Internal @workiz package version tracking | ✅ Planned |

### Advanced Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Auto-Fix Agent** | AI-powered automatic code fixes | ✅ Planned |
| **Auto-Discovery** | Automatic repo/project detection | ✅ Planned |
| **Admin UI** | Web dashboard for management | ✅ Planned |
| **🤖 Knowledge Assistant** | Ask questions about your codebase | ✅ Planned |
| **Cost Tracking** | API usage and cost monitoring | ✅ Planned |

### 🔧 Fix in Cursor (NEW!)

Every review comment includes a **"Fix in Cursor"** link that opens the file at the exact line in your IDE:

```
🔍 Issue: Let Usage Detected
File: src/services/user.service.ts (line 42)

[🔧 Fix in Cursor](cursor://file/...) | [📋 Copy Fix Instructions](#)
```

**How it works:**
1. Click "🔧 Fix in Cursor" → Opens file at the exact line in Cursor
2. Click "📋 Copy Fix Instructions" → Copy context for Cursor Composer
3. Paste in Composer (Cmd+K) → AI fixes with full context

Supports: `cursor://` (Cursor IDE), `vscode://` (VS Code), and `vscode.dev` (web fallback)

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

### Automation Summary (100% Webhook-Driven)

| Process | Trigger | Latency |
|---------|---------|---------|
| **PR Review** | GitHub webhook (`pull_request`) | ⚡ Real-time |
| **Code Indexing** | GitHub webhook (`push` to main) | ⚡ Real-time |
| **RepoSwarm Analysis** | GitHub webhook (`push` to main) | ⚡ Real-time |
| **Repo Discovery** | GitHub org webhook (`repository.created`) | ⚡ Real-time |
| **Jira Sync** | Jira webhook (`issue_created/updated`) | ⚡ Real-time |
| **NPM Packages Sync** | GitHub webhook (`registry_package.published`) | ⚡ Real-time |
| **Reconciliation** | Weekly CronJob (safety net) | Weekly |

**No frequent CronJobs needed!** All updates happen instantly via webhooks.

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

| Database | Analyzer | Key Checks |
|----------|----------|------------|
| **MySQL** | `MySQLAnalyzer` | SELECT *, N+1, SQL injection |
| **PostgreSQL** | `PostgreSQLAnalyzer` | Same + asyncpg patterns |
| **MongoDB** | `MongoDBAnalyzer` | Missing indexes, $regex without anchor |
| **Elasticsearch** | `ElasticsearchAnalyzer` | Wildcard queries, deep pagination |

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

*Last updated: January 2026*

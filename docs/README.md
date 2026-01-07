# Workiz PR Agent

A customized fork of [qodo-ai/pr-agent](https://github.com/qodo-ai/pr-agent) tailored for Workiz's development workflow, supporting multi-language code review, cross-repository context, Jira integration, Figma design verification, and automated code fixes.

## 📚 Documentation Index

| Document | Description |
|----------|-------------|
| [Architecture & Features](./ARCHITECTURE_AND_FEATURES.md) | System architecture, all features, code implementations |
| [Deployment & Implementation](./DEPLOYMENT_AND_IMPLEMENTATION.md) | Setup guides, deployment, checklists |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Docker Desktop
- GitHub Personal Access Token
- OpenAI API Key
- (Optional) Jira API Token

### Local Development (5 minutes)

```bash
# Clone and setup
cd ~/Documents/Github
git clone https://github.com/Workiz/workiz-pr-agent.git
cd workiz-pr-agent

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install asyncpg jira pgvector aiohttp gitpython pyyaml packaging

# Start database
docker-compose -f docker-compose.local.yml up -d

# Configure secrets
cp pr_agent/settings/.secrets_template.toml pr_agent/settings/.secrets.toml
# Edit .secrets.toml with your credentials

# Discover and index repositories
python -m pr_agent.cli_admin discover --orgs workiz

# Start server
python -m uvicorn pr_agent.servers.github_app:app --port 3000 --reload
```

See [Deployment & Implementation](./DEPLOYMENT_AND_IMPLEMENTATION.md) for detailed setup instructions.

---

## 🎯 Feature Summary

### Core Review Capabilities

| Feature | Description | Status |
|---------|-------------|--------|
| **Custom Rules Engine** | Workiz-specific code style rules | ✅ Planned |
| **Language Analyzers** | PHP, JS/TS, NestJS, React, Python | ✅ Planned |
| **Database Analyzers** | MySQL, MongoDB, Elasticsearch, PostgreSQL | ✅ Planned |
| **Security Analyzer** | Traefik-aware security checks | ✅ Planned |
| **PubSub Analyzer** | Event topology and pattern validation | ✅ Planned |

### Integrations

| Integration | Purpose | Status |
|-------------|---------|--------|
| **GitHub** | Webhooks, PR reviews, comments | ✅ Base exists |
| **Jira** | Ticket context, history, compliance | ✅ Planned |
| **RepoSwarm** | Cross-repo architecture context | ✅ Planned |
| **Figma** | Design verification for frontend | ✅ Planned |
| **NPM Registry** | Internal package version tracking | ✅ Planned |

### Advanced Features

| Feature | Description | Status |
|---------|-------------|--------|
| **Auto-Fix Agent** | AI-powered automatic code fixes | ✅ Planned |
| **Auto-Discovery** | Automatic repo/project detection | ✅ Planned |
| **Admin UI** | Web dashboard for management | ✅ Planned |
| **Cost Tracking** | API usage and cost monitoring | ✅ Planned |

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
│   │  GitHub  │  │   Jira   │  │  Figma   │  │ NPM Reg  │  │  RepoSwarm Hub       │  │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────────┬───────────┘  │
│        │             │             │             │                    │              │
│        ▼             ▼             ▼             ▼                    ▼              │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │                      PR Agent Core (FastAPI)                                  │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │   │
│   │  │   Context   │  │ Specialized │  │   Custom    │  │    Output           │ │   │
│   │  │   Loaders   │  │   Agents    │  │   Rules     │  │    Handlers         │ │   │
│   │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │   │
│   └─────────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                             │
│                                        ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │                    LLM Layer (via LiteLLM)                                    │   │
│   │  Claude Sonnet (default) │ Claude Opus (auto-fix) │ GPT-4o (fallback)        │   │
│   └─────────────────────────────────────────────────────────────────────────────┘   │
│                                        │                                             │
│                                        ▼                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────┐   │
│   │                     PostgreSQL + pgvector                                     │   │
│   │  repositories │ code_chunks │ jira_tickets │ custom_rules │ api_usage        │   │
│   └─────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                       │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

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
| **Week 8** | Production | GCloud deployment, monitoring |

---

## 🔗 References

- [Original PR Agent Documentation](https://qodo-merge-docs.qodo.ai/)
- [RepoSwarm](https://github.com/your-org/reposwarm)
- [Figma MCP](https://modelcontextprotocol.io/examples)
- [GCloud Secret Manager](https://cloud.google.com/secret-manager)

---

## 📞 Support

For questions or issues:
1. Check the detailed documentation in this folder
2. Review the original [qodo-ai/pr-agent](https://github.com/qodo-ai/pr-agent) repository
3. Contact the DevOps team

---

*Last updated: January 2026*

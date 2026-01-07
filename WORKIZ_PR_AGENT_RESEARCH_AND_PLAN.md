# Workiz PR Agent - Research and Implementation Plan

> **📚 This documentation has been reorganized!**
> 
> The comprehensive plan has been split into focused, maintainable documents for better navigation.

## Documentation

| Document | Description |
|----------|-------------|
| **[📖 Overview & Quick Start](./docs/README.md)** | High-level overview, feature summary, quick start guide |
| **[🏗️ Architecture & Features](./docs/ARCHITECTURE_AND_FEATURES.md)** | System architecture, database schema, all features with code |
| **[🚀 Deployment & Implementation](./docs/DEPLOYMENT_AND_IMPLEMENTATION.md)** | Local setup, production deployment, checklists |

---

## Quick Links

### Getting Started
- [Prerequisites](./docs/DEPLOYMENT_AND_IMPLEMENTATION.md#prerequisites)
- [Local Development Setup](./docs/DEPLOYMENT_AND_IMPLEMENTATION.md#1-local-development-setup)
- [Production Deployment](./docs/DEPLOYMENT_AND_IMPLEMENTATION.md#2-production-deployment-gcloud)

### Features
- [Custom Rules Engine](./docs/ARCHITECTURE_AND_FEATURES.md#4-custom-rules-engine)
- [Language Analyzers](./docs/ARCHITECTURE_AND_FEATURES.md#5-language-analyzers)
- [Jira Integration](./docs/ARCHITECTURE_AND_FEATURES.md#81-jira-integration)
- [RepoSwarm Integration](./docs/ARCHITECTURE_AND_FEATURES.md#82-reposwarm-integration)
- [Figma Integration](./docs/ARCHITECTURE_AND_FEATURES.md#83-figma-integration)
- [Auto-Fix Agent](./docs/ARCHITECTURE_AND_FEATURES.md#9-auto-fix-agent)
- [Admin UI](./docs/ARCHITECTURE_AND_FEATURES.md#12-admin-ui)

### Implementation
- [Files to Create](./docs/DEPLOYMENT_AND_IMPLEMENTATION.md#7-files-to-create)
- [Checklists](./docs/DEPLOYMENT_AND_IMPLEMENTATION.md#8-implementation-checklists)
- [Timeline](./docs/DEPLOYMENT_AND_IMPLEMENTATION.md#9-timeline)

---

## Summary

This fork of [qodo-ai/pr-agent](https://github.com/qodo-ai/pr-agent) is customized for Workiz with:

### Core Features
- ✅ **Multi-language Support**: PHP, JS/TS, NestJS, React, Python
- ✅ **Database Analysis**: MySQL, PostgreSQL, MongoDB, Elasticsearch
- ✅ **Custom Rules**: Workiz-specific coding standards from Cursor Team Rules
- ✅ **Cross-Repo Context**: RepoSwarm integration for architectural awareness
- ✅ **Jira Integration**: Ticket compliance and context in reviews
- ✅ **Security Analysis**: Traefik-aware security checks
- ✅ **PubSub Analysis**: Event topology and pattern validation

### Advanced Features
- ✅ **Auto-Fix Agent**: AI-powered automatic code fixes
- ✅ **Figma Verification**: Design compliance for frontend PRs
- ✅ **NPM Package Management**: Internal package version tracking
- ✅ **Auto-Discovery**: Automatic repo/project detection
- ✅ **Admin UI**: Web dashboard for management

### Tech Stack
- **Backend**: Python 3.12+, FastAPI
- **Database**: PostgreSQL with pgvector
- **LLMs**: Claude Sonnet/Opus, GPT-4o, Gemini 2.5 (via LiteLLM)
- **Infrastructure**: Google Cloud (Cloud Run, Cloud SQL, Secret Manager)

---

*See the [docs folder](./docs/) for complete documentation.*

# Qodo PR-Agent Architecture Documentation

**Generated:** 2025-10-07
**Project:** Qodo PR-Agent - AI-Powered Code Review Tool
**Repository:** https://github.com/Codium-ai/pr-agent

## Overview

This directory contains comprehensive architectural documentation for the Qodo PR-Agent project, visualized using Mermaid diagrams. These diagrams provide insights into the system's structure, data flow, and component interactions.

## Documentation Index

### 1. [System Overview](./01-system-overview.md)
**Purpose:** High-level architecture overview showing all major components and their relationships.

**Key Diagrams:**
- Overall system architecture with all layers
- Component descriptions and responsibilities
- Technology stack overview

**Use this when:** You need to understand the complete system structure or explain the project to new team members.

---

### 2. [Request Flow Architecture](./02-request-flow.md)
**Purpose:** Detailed flow of how requests are processed through the system.

**Key Diagrams:**
- Request processing sequence diagram
- Large PR handling strategy
- Command-to-tool mapping
- Token management strategy
- Configuration flow

**Use this when:** You need to understand how a PR review request flows from start to finish, or debug processing issues.

---

### 3. [Git Providers Architecture](./03-git-providers.md)
**Purpose:** Architecture of the git provider abstraction layer.

**Key Diagrams:**
- Git provider class hierarchy
- Platform feature support matrix
- Provider factory pattern
- Provider communication flow
- Clone operations
- Data models (FilePatchInfo, EDIT_TYPE)

**Use this when:** Adding support for a new git platform or understanding how platform-specific features are implemented.

---

### 4. [AI Handlers Architecture](./04-ai-handlers.md)
**Purpose:** AI/LLM integration layer architecture.

**Key Diagrams:**
- AI handler class hierarchy
- Model support matrix
- AI request flow with fallback
- Model selection strategy
- Token management in AI calls
- LiteLLM configuration
- Response parsing
- Error handling

**Use this when:** Integrating a new AI model, debugging AI-related issues, or understanding token management.

---

### 5. [Deployment Architecture](./05-deployment-architecture.md)
**Purpose:** Different deployment options and infrastructure patterns.

**Key Diagrams:**
- Deployment options overview
- GitHub Actions deployment
- GitHub App deployment
- GitLab webhook deployment
- Docker deployment
- AWS Lambda deployment
- Self-hosted server deployment
- Scaling considerations
- Configuration management
- Security architecture

**Use this when:** Planning a deployment, troubleshooting infrastructure issues, or implementing security measures.

---

### 6. [Tools Architecture](./06-tools-architecture.md)
**Purpose:** Architecture of individual PR-Agent tools.

**Key Diagrams:**
- Tools class structure
- PR Review tool flow
- PR Description tool flow
- Code Suggestions tool flow
- Ask Questions tool flow
- Line Questions tool flow
- Similar Issue search flow
- Tool configuration
- Execution context

**Use this when:** Developing a new tool, customizing existing tools, or understanding tool-specific behavior.

---

## Quick Reference: Component Locations

### Core Components
- **PR Agent Core:** `/pr_agent/agent/pr_agent.py`
- **Command Router:** Defined in `command2class` dictionary in `pr_agent.py`

### Tools
- **Location:** `/pr_agent/tools/`
- **Main Tools:**
  - `pr_reviewer.py` - Code review tool
  - `pr_description.py` - PR description generation
  - `pr_code_suggestions.py` - Code improvement suggestions
  - `pr_questions.py` - PR Q&A
  - `pr_line_questions.py` - Line-specific questions
  - `pr_update_changelog.py` - Changelog generation
  - `pr_add_docs.py` - Documentation generation
  - `pr_generate_labels.py` - Label suggestions
  - `pr_similar_issue.py` - Similar issue search

### Git Providers
- **Location:** `/pr_agent/git_providers/`
- **Providers:**
  - `github_provider.py`
  - `gitlab_provider.py`
  - `bitbucket_provider.py`
  - `bitbucket_server_provider.py`
  - `azuredevops_provider.py`
  - `gitea_provider.py`
  - `gerrit_provider.py`
  - `codecommit_provider.py`
  - `local_git_provider.py`

### AI Handlers
- **Location:** `/pr_agent/algo/ai_handlers/`
- **Handlers:**
  - `base_ai_handler.py` - Abstract base class
  - `litellm_ai_handler.py` - Multi-provider support
  - `openai_ai_handler.py` - Direct OpenAI integration
  - `langchain_ai_handler.py` - Langchain integration

### Algorithm Layer
- **Location:** `/pr_agent/algo/`
- **Key Files:**
  - `pr_processing.py` - PR analysis and token management
  - `git_patch_processing.py` - Diff parsing and manipulation
  - `token_handler.py` - Token counting
  - `file_filter.py` - File filtering
  - `language_handler.py` - Language detection

### Servers
- **Location:** `/pr_agent/servers/`
- **Server Types:**
  - `github_app.py` - GitHub App webhook
  - `github_action_runner.py` - GitHub Actions
  - `gitlab_webhook.py` - GitLab webhook
  - `bitbucket_app.py` - Bitbucket App
  - `azuredevops_server_webhook.py` - Azure DevOps webhook
  - `gitea_app.py` - Gitea App

### Configuration
- **Location:** `/pr_agent/settings/`
- **Key Files:**
  - `configuration.toml` - Main configuration
  - `pr_reviewer_prompts.toml` - Review prompts
  - `pr_description_prompts.toml` - Description prompts
  - `code_suggestions/` - Code suggestion prompts
  - `language_extensions.toml` - Language mappings

## Architecture Principles

### 1. **Separation of Concerns**
- Tools handle business logic
- Git providers abstract platform differences
- AI handlers abstract LLM differences
- Algorithm layer handles data processing

### 2. **Token Management**
- Aggressive token counting to stay within LLM limits
- Dynamic compression for large PRs
- Multi-call strategy for very large PRs
- Buffer zones for safe operation

### 3. **Extensibility**
- Abstract base classes for easy extension
- Plugin architecture for new tools
- Provider pattern for new platforms
- Handler pattern for new AI models

### 4. **Resilience**
- Fallback models for AI failures
- Retry logic with exponential backoff
- Graceful degradation for large PRs
- Error handling and logging throughout

### 5. **Performance**
- Shallow git clones with blob filtering
- Response caching where appropriate
- Async operations for I/O-bound tasks
- Efficient diff processing

## Technology Stack Summary

### Core Technologies
- **Language:** Python 3.x
- **Web Framework:** FastAPI + Uvicorn/Gunicorn
- **Configuration:** Dynaconf (TOML-based)
- **Logging:** Loguru

### AI/LLM Integration
- **Primary:** LiteLLM (multi-provider support)
- **Direct:** OpenAI SDK, Anthropic SDK
- **Alternative:** Langchain
- **Token Counting:** tiktoken

### Git Platform SDKs
- **GitHub:** PyGithub
- **GitLab:** python-gitlab
- **Bitbucket:** atlassian-python-api
- **Azure DevOps:** azure-devops
- **Others:** GitPython, giteapy

### Infrastructure
- **HTTP:** aiohttp, requests
- **Queue/Jobs:** Optional (Celery + Redis)
- **Testing:** pytest, pytest-cov
- **Data Validation:** pydantic

### Optional Components
- **Vector DB:** Pinecone, LanceDB, Qdrant (for similar issue search)
- **Secrets:** AWS Secrets Manager, GCP Secret Manager
- **Monitoring:** Custom logging + metrics

## Common Patterns

### 1. Provider Pattern
Used for git platforms and AI models to abstract implementation details behind a common interface.

### 2. Factory Pattern
Used to instantiate the correct provider based on URL or configuration.

### 3. Strategy Pattern
Used for different token management strategies (full, compressed, multi-call).

### 4. Chain of Responsibility
Used for configuration loading (defaults → secrets → env → args → repo-specific).

### 5. Template Method
Used in tool base class with hooks for specific tool implementations.

## Contributing to Architecture

When adding new components:

1. **Follow existing patterns** - Use abstract base classes and inheritance
2. **Update diagrams** - Keep these architecture docs current
3. **Document decisions** - Explain why you chose a particular approach
4. **Test integrations** - Ensure new components work with existing ones
5. **Consider token limits** - Always account for LLM context windows

## Viewing Diagrams

These Mermaid diagrams can be viewed in:
- **GitHub:** Native rendering in markdown files
- **VS Code:** With Mermaid extensions
- **Mermaid Live Editor:** https://mermaid.live/
- **Documentation sites:** Rendered in most modern static site generators

## Questions or Issues?

- **Documentation Issues:** Open an issue in the repository
- **Architecture Questions:** Discuss in project Discord/Slack
- **Contribution Ideas:** Review CONTRIBUTING.md

---

**Last Updated:** 2025-10-07
**Architecture Version:** v1.0
**Compatible with:** PR-Agent v0.30+

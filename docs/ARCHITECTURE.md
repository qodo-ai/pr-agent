# Qodo PR-Agent: Architecture Documentation

**Generated:** 2025-10-07
**Version:** 1.0
**Project:** AI-Powered Code Review Tool

## Overview

This document provides a comprehensive architectural overview of the Qodo PR-Agent system. For detailed diagrams and deep dives, see the [architecture directory](./architecture/).

---

## System at a Glance

**What is Qodo PR-Agent?**
An AI-powered code review tool that analyzes pull requests and provides automated reviews, suggestions, documentation, and answers to questions about code changes.

**Core Capabilities:**
- Automated code review with AI-generated feedback
- PR description generation
- Code improvement suggestions
- Interactive Q&A on PRs
- Multiple git platform support (GitHub, GitLab, Bitbucket, Azure DevOps, Gitea, Gerrit)
- Multiple LLM support (OpenAI, Claude, Gemini, and more)

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Entry Points                             │
│  CLI │ GitHub Actions │ Webhooks │ Browser Extension        │
└───────────────────┬─────────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────────┐
│                 PR Agent Core                               │
│  • Command routing                                          │
│  • Configuration management                                 │
│  • Orchestration                                            │
└───────────────────┬─────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
┌───────▼──────┐ ┌─▼────────┐ ┌▼──────────────┐
│   Tools      │ │ Git       │ │ AI Handlers   │
│              │ │ Providers │ │               │
│ • Review     │ │           │ │ • LiteLLM     │
│ • Describe   │ │ • GitHub  │ │ • OpenAI      │
│ • Improve    │ │ • GitLab  │ │ • Langchain   │
│ • Ask        │ │ • Bitbucket│ │               │
│ • More...    │ │ • Azure   │ │               │
└──────────────┘ └───────────┘ └───────────────┘
        │               │               │
        └───────────────┼───────────────┘
                        │
        ┌───────────────▼────────────────┐
        │   Algorithm Layer              │
        │ • PR Processing                │
        │ • Token Management             │
        │ • Diff Processing              │
        │ • Language Detection           │
        └────────────────────────────────┘
```

---

## Key Components

### 1. **Entry Points** (How users interact with the system)

| Entry Point | Description | Use Case |
|-------------|-------------|----------|
| **CLI** | Command-line interface | Local development, testing |
| **GitHub Actions** | CI/CD workflow | Automated PR reviews on push |
| **Webhooks** | Real-time event processing | Production deployments |
| **Browser Extension** | Chrome extension | Enhanced UI experience |

**File Locations:**
- CLI: `/pr_agent/cli.py`, `/pr_agent/cli_pip.py`
- GitHub Action: `/pr_agent/servers/github_action_runner.py`
- Webhooks: `/pr_agent/servers/*_webhook.py`

---

### 2. **PR Agent Core** (Central orchestration)

**Responsibilities:**
- Parse and route commands (e.g., `/review`, `/describe`, `/improve`)
- Load and merge configurations from multiple sources
- Initialize appropriate git providers and AI handlers
- Manage execution lifecycle

**Key File:** `/pr_agent/agent/pr_agent.py`

**Command Mapping:**
```python
command2class = {
    "review": PRReviewer,
    "describe": PRDescription,
    "improve": PRCodeSuggestions,
    "ask": PRQuestions,
    "ask_line": PR_LineQuestions,
    "update_changelog": PRUpdateChangelog,
    "add_docs": PRAddDocs,
    "generate_labels": PRGenerateLabels,
    # ... more commands
}
```

---

### 3. **Tools Layer** (Business logic)

Each tool implements a specific PR operation:

| Tool | Command | Purpose |
|------|---------|---------|
| **PRReviewer** | `/review` | Generate comprehensive code review |
| **PRDescription** | `/describe` | Auto-generate PR title, summary, and walkthrough |
| **PRCodeSuggestions** | `/improve` | Suggest code improvements |
| **PRQuestions** | `/ask` | Answer questions about the PR |
| **PR_LineQuestions** | `/ask_line` | Answer questions about specific code lines |
| **PRUpdateChangelog** | `/update_changelog` | Generate/update CHANGELOG entries |
| **PRAddDocs** | `/add_docs` | Generate missing documentation |
| **PRGenerateLabels** | `/generate_labels` | Suggest PR labels |

**Location:** `/pr_agent/tools/`

**Common Flow:**
1. Fetch PR data from git provider
2. Process and compress diffs (token management)
3. Build AI prompt with context
4. Call AI handler
5. Parse and validate response
6. Publish results to git platform

---

### 4. **Git Providers** (Platform abstraction)

Abstracts differences between git platforms with a common interface.

**Supported Platforms:**
- GitHub (github.com)
- GitLab (gitlab.com)
- Bitbucket Cloud & Server
- Azure DevOps
- Gitea
- Gerrit
- AWS CodeCommit
- Local Git

**Location:** `/pr_agent/git_providers/`

**Key Operations:**
- `get_diff_files()` - Fetch PR diff
- `get_pr_description()` - Get PR description
- `publish_comment()` - Post comment
- `publish_inline_comments()` - Post inline code suggestions
- `publish_labels()` - Add labels
- `clone()` - Clone repository with authentication

---

### 5. **AI Handlers** (LLM abstraction)

Provides a unified interface for multiple AI providers.

**Supported Models:**
- **OpenAI:** GPT-4, GPT-4 Turbo, GPT-5, GPT-3.5
- **Anthropic:** Claude 3 Opus, Sonnet, Haiku
- **Google:** Gemini Pro, PaLM 2
- **Others:** Deepseek, Cohere, Replicate

**Location:** `/pr_agent/algo/ai_handlers/`

**Primary Handler:** `LiteLLMAIHandler` (supports 100+ models via LiteLLM)

**Features:**
- Automatic fallback to alternative models
- Token counting and management
- Response parsing and validation
- Rate limit handling
- Retry logic with exponential backoff

---

### 6. **Algorithm Layer** (Data processing)

Core algorithms for processing PRs and managing tokens.

**Key Components:**

| Component | File | Purpose |
|-----------|------|---------|
| **PR Processing** | `pr_processing.py` | PR diff compression, token management, multi-call strategy |
| **Git Patch Processing** | `git_patch_processing.py` | Diff parsing, hunk manipulation, patch extension |
| **Token Handler** | `token_handler.py` | Count tokens, manage budgets, ensure fits in context |
| **File Filter** | `file_filter.py` | Filter files by patterns (ignore tests, generated code) |
| **Language Handler** | `language_handler.py` | Detect languages, sort files by priority |

**Location:** `/pr_agent/algo/`

---

## Token Management Strategy

**The Problem:** Large PRs can exceed LLM context windows.

**The Solution:** Intelligent compression and prioritization.

```
┌─────────────────────────────────────────────┐
│  PR with 50 files, 10,000 lines changed    │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Count Tokens (with tiktoken)              │
│  Total: 15,000 tokens                       │
└──────────────────┬──────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│  Check Against Model Limit                 │
│  GPT-4: 8,192 tokens                        │
│  Buffer: 1,500 tokens for response         │
│  Available: 6,692 tokens                    │
└──────────────────┬──────────────────────────┘
                   │
         ┌─────────┴─────────┐
         │ Fits?             │
         └─────────┬─────────┘
              ┌────┴────┐
              │         │
           YES│         │NO
              │         │
              ▼         ▼
    ┌─────────────┐  ┌──────────────────────┐
    │ Use Full    │  │ Compress Strategy:   │
    │ Extended    │  │ 1. Remove context    │
    │ Diff        │  │ 2. Remove deletions  │
    └─────────────┘  │ 3. Sort by language  │
                     │ 4. Prioritize files  │
                     │ 5. Clip if needed    │
                     └──────────────────────┘
```

**Compression Strategies:**

1. **Remove Extra Context Lines** - Strip surrounding unchanged code
2. **Remove Delete-Only Hunks** - Focus on additions/modifications
3. **Prioritize by Language** - Process main language files first
4. **Sort by Size** - Include largest files first
5. **Multi-Call Strategy** - Split into multiple AI calls if needed
6. **Clip Large Files** - Truncate individual large patches

---

## Request Flow Example: `/review` Command

```
User comments: @bot /review
         │
         ▼
┌────────────────────┐
│ Webhook receives   │
│ event from GitHub  │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ PR Agent Core      │
│ • Parse command    │
│ • Load config      │
│ • Create providers │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ PRReviewer Tool    │
│ • Fetch PR data    │
│ • Get diff files   │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ PR Processing      │
│ • Count tokens     │
│ • Compress if      │
│   needed           │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Build Prompt       │
│ • Diff             │
│ • Description      │
│ • Instructions     │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ AI Handler         │
│ • Call LLM API     │
│ • Parse response   │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Format Review      │
│ • Markdown table   │
│ • Inline comments  │
│ • Suggestions      │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ Publish to GitHub  │
│ • Main comment     │
│ • Inline comments  │
│ • Labels           │
└────────────────────┘
```

**Timing:** Typically 10-60 seconds depending on PR size.

---

## Configuration Management

**Configuration Sources** (in order of precedence):

1. **Defaults** - `/pr_agent/settings/configuration.toml`
2. **Secrets** - `/pr_agent/settings/.secrets.toml` (API keys)
3. **Environment Variables** - `OPENAI_KEY`, `GITHUB_TOKEN`, etc.
4. **CLI Arguments** - `--config.model=gpt-4`
5. **Repo-Specific** - `.pr_agent.toml` in the repository

**Example Configuration:**

```toml
[config]
model = "gpt-4"
fallback_models = ["gpt-3.5-turbo", "claude-3-sonnet"]
max_description_tokens = 1000

[pr_reviewer]
require_score_review = true
require_tests_review = false
inline_comments = true
num_code_suggestions = 4

[pr_code_suggestions]
rank_suggestions = "top"
enable_tracking = true
```

---

## Deployment Options

| Option | Pros | Cons | Best For |
|--------|------|------|----------|
| **CLI** | Simple, local control | Manual execution | Testing, development |
| **GitHub Actions** | Automated, integrated | GitHub-only | GitHub repos |
| **GitHub App** | Zero-setup, managed | Limited customization | Teams wanting hands-off |
| **Webhooks** | Real-time, flexible | Requires server | Production, multi-platform |
| **Docker** | Isolated, reproducible | Resource overhead | Self-hosted |
| **Lambda** | Serverless, scalable | Cold starts, time limits | Cloud-native |
| **Self-Hosted** | Full control | Maintenance burden | Enterprise |

**Recommended:** Start with GitHub Actions or CLI, move to webhooks/app for production.

---

## Security & Privacy

### Security Measures
- **API Keys:** Stored in secrets manager or environment variables
- **Webhook Verification:** Signature validation for all webhooks
- **Rate Limiting:** Prevents abuse
- **Input Validation:** All user inputs sanitized
- **TLS/HTTPS:** All communications encrypted

### Privacy Considerations
- **Self-Hosted:** You control all data (OpenAI API data policy applies)
- **Qodo-Hosted (Pro):** Zero data retention, not used for training
- **Code Transmission:** Only sent when tools are invoked
- **No Passive Collection:** Agent only activates on command

---

## Performance Considerations

### Optimization Strategies
1. **Shallow Clones:** `--depth=1 --filter=blob:none` for fast repo access
2. **Token-Aware Processing:** Avoid unnecessary LLM calls
3. **Caching:** Reuse data within the same PR processing
4. **Async Operations:** Non-blocking I/O for API calls
5. **Efficient Diff Parsing:** Minimal memory footprint

### Typical Timings
- **Small PR (< 5 files):** 10-20 seconds
- **Medium PR (5-20 files):** 20-45 seconds
- **Large PR (20-50 files):** 45-90 seconds
- **Very Large PR (50+ files):** 90+ seconds (may use multiple calls)

---

## Extensibility Points

### Adding a New Tool
1. Create class extending base tool pattern
2. Implement `run()` method
3. Add to `command2class` dictionary
4. Create prompt templates in `/pr_agent/settings/`

### Adding a New Git Provider
1. Extend `GitProvider` abstract class
2. Implement required methods (get_diff_files, publish_comment, etc.)
3. Add provider detection logic
4. Test with platform-specific features

### Adding a New AI Model
1. Configure via LiteLLM (easiest)
2. Or extend `BaseAiHandler` for direct integration
3. Update token counting logic if needed
4. Test with various prompt sizes

---

## Detailed Documentation

For in-depth architectural diagrams and explanations, see:

- **[System Overview](./architecture/01-system-overview.md)** - Complete system diagram
- **[Request Flow](./architecture/02-request-flow.md)** - How requests are processed
- **[Git Providers](./architecture/03-git-providers.md)** - Platform abstraction layer
- **[AI Handlers](./architecture/04-ai-handlers.md)** - LLM integration architecture
- **[Deployment](./architecture/05-deployment-architecture.md)** - Deployment patterns
- **[Tools](./architecture/06-tools-architecture.md)** - Individual tool architectures

---

## Quick Start for Developers

### Prerequisites
```bash
# Install dependencies
pip install -r requirements.txt

# Set API keys
export OPENAI_KEY=your_key_here
export GITHUB_TOKEN=your_token_here
```

### Run Locally
```bash
# Review a PR
python -m pr_agent --pr_url https://github.com/owner/repo/pull/123 review

# Generate description
python -m pr_agent --pr_url https://github.com/owner/repo/pull/123 describe

# Get suggestions
python -m pr_agent --pr_url https://github.com/owner/repo/pull/123 improve
```

### Run Tests
```bash
pytest tests/
```

---

## Common Issues & Solutions

### Issue: "Token limit exceeded"
**Solution:** Enable compression strategy or reduce `patch_extra_lines_before/after` in config.

### Issue: "Rate limit hit"
**Solution:** Configure fallback models or implement request queuing.

### Issue: "Provider authentication failed"
**Solution:** Check API token permissions and expiration.

### Issue: "Large PR timeout"
**Solution:** Enable multi-call strategy with `max_ai_calls` configuration.

---

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.

**Architecture Changes:**
- Discuss significant changes in issues first
- Update architecture diagrams when modifying core components
- Add tests for new integrations
- Document new configuration options

---

## Resources

- **Main Repository:** https://github.com/Codium-ai/pr-agent
- **Documentation:** https://qodo-merge-docs.qodo.ai/
- **Discord Community:** https://discord.com/invite/SgSxuQ65GF
- **Qodo Website:** https://www.qodo.ai/

---

**Document Version:** 1.0
**Last Updated:** 2025-10-07
**Maintained by:** Architecture Team

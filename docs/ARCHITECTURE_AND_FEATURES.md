# Architecture & Features

This document covers the system architecture and all features of the Workiz PR Agent.

## Table of Contents

1. [Existing PR Agent Architecture](#1-existing-pr-agent-architecture)
2. [System Architecture](#2-system-architecture)
3. [Database Schema](#3-database-schema)
4. [Custom Rules Engine](#4-custom-rules-engine)
5. [Language Analyzers](#5-language-analyzers)
6. [Database Analyzers](#6-database-analyzers)
7. [PubSub Event System](#7-pubsub-event-system)
8. [Integrations](#8-integrations)
9. [Auto-Fix Agent](#9-auto-fix-agent)
10. [Auto-Discovery System](#10-auto-discovery-system)
11. [NPM Package Management](#11-npm-package-management)
12. [Admin UI](#12-admin-ui)
13. [Error Handling](#13-error-handling)
14. [Fix in Cursor Integration](#14-fix-in-cursor-integration)

---

## 1. Existing PR Agent Architecture

### Core Components

The qodo-ai/pr-agent is built with these key components:

| Component | Location | Purpose |
|-----------|----------|---------|
| `PRAgent` | `pr_agent/agent/pr_agent.py` | Central command dispatcher |
| `PRReviewer` | `pr_agent/tools/pr_reviewer.py` | Core review logic |
| `LiteLLMAIHandler` | `pr_agent/algo/ai_handlers/litellm_ai_handler.py` | LLM abstraction |
| `GithubProvider` | `pr_agent/git_providers/github_provider.py` | GitHub API integration |
| `Dynaconf` | `pr_agent/config_loader.py` | Configuration management |

### Command Routing

```python
# pr_agent/agent/pr_agent.py
command2class = {
    "review": PRReviewer,           # Base reviewer (or WorkizPRReviewer if workiz.enabled)
    "improve": PRCodeSuggestions,   # Base suggestions (or WorkizPRCodeSuggestions if workiz.enabled)
    "describe": PRDescription,
    "ask": PRReviewerAsk,
    "workiz_review": WorkizPRReviewer,         # Explicit Workiz reviewer
    "workiz_improve": WorkizPRCodeSuggestions, # Explicit Workiz suggestions
    # ... more commands
}
```

### Configuration System

Uses `dynaconf` with layered configuration:
1. `configuration.toml` - defaults
2. `.secrets.toml` - sensitive data
3. `.pr_agent.toml` - per-repo overrides
4. Environment variables - runtime overrides

### Prompt System

Jinja2 templates in `pr_agent/settings/*.toml`:

```toml
[pr_review_prompt]
system = """You are PR-Reviewer...
{%- if extra_instructions %}
Extra instructions:
{{ extra_instructions }}
{%- endif %}
"""
```

---

## 2. System Architecture

### Complete Flow Diagram

```
┌───────────────────────────────────────────────────────────────────────────────────────┐
│                           Workiz PR Agent - System Flow                                │
├───────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│  EXTERNAL                                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────────────────┐  │
│  │  GitHub  │  │   Jira   │  │  Figma   │  │ NPM Reg  │  │  RepoSwarm Hub          │  │
│  │  (PRs)   │  │ (Tickets)│  │ (Designs)│  │(Packages)│  │  (.arch.md files)       │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────────┬─────────────┘  │
│       │             │             │             │                     │               │
│       │ Webhooks    │ Webhooks    │ MCP         │ API                 │ GitHub API    │
│       ▼             ▼             ▼             ▼                     ▼               │
│  ┌────────────────────────────────────────────────────────────────────────────────┐   │
│  │                            PR AGENT CORE                                        │   │
│  │                                                                                 │   │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│  │  │                     Webhook Handler (FastAPI)                            │   │   │
│  │  │  /api/v1/github_webhooks  /api/v1/webhooks/jira  /api/v1/admin/*        │   │   │
│  │  └─────────────────────────────────┬───────────────────────────────────────┘   │   │
│  │                                    │                                            │   │
│  │                                    ▼                                            │   │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│  │  │                  Orchestrator (Multi-Agent Coordinator)                  │   │   │
│  │  │  1. Detect PR type (backend/frontend)                                   │   │   │
│  │  │  2. Load relevant context                                               │   │   │
│  │  │  3. Dispatch to specialized agents                                      │   │   │
│  │  │  4. Synthesize results                                                  │   │   │
│  │  │  5. Post review                                                         │   │   │
│  │  └────────────────────────────────┬────────────────────────────────────────┘   │   │
│  │                                   │                                             │   │
│  │           ┌───────────────────────┼───────────────────────────┐                │   │
│  │           │                       │                           │                │   │
│  │           ▼                       ▼                           ▼                │   │
│  │  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐              │   │
│  │  │ Context Loaders │   │  Specialized    │   │  Output         │              │   │
│  │  │ • RepoSwarm     │   │    Agents       │   │  Handlers       │              │   │
│  │  │ • Jira          │   │ • Code Quality  │   │ • GitHub        │              │   │
│  │  │ • Cross-Repo    │   │ • Security      │   │ • PR Comments   │              │   │
│  │  │ • Figma         │   │ • SQL           │   │ • Check Runs    │              │   │
│  │  │ • NPM Packages  │   │ • PubSub        │   │ • Labels        │              │   │
│  │  │                 │   │ • Figma Design  │   │                 │              │   │
│  │  └─────────────────┘   └─────────────────┘   └─────────────────┘              │   │
│  │                                   │                                             │   │
│  │                                   ▼                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│  │  │                         LLM Layer (LiteLLM)                              │   │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │   │   │
│  │  │  │ Gemini 3    │  │Gemini 2.5   │  │  (Future)   │  │  (Future)   │     │   │   │
│  │  │  │ Pro(Default)│  │Pro(Fallback)│  │ Claude/GPT  │  │ More models │     │   │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘     │   │   │
│  │  └─────────────────────────────────────────────────────────────────────────┘   │   │
│  │                                   │                                             │   │
│  │                                   ▼                                             │   │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐   │   │
│  │  │                      PostgreSQL + pgvector                               │   │   │
│  │  │  • repositories  • code_chunks  • jira_tickets  • review_history        │   │   │
│  │  │  • custom_rules  • pubsub_events  • api_usage  • admin_users            │   │   │
│  │  └─────────────────────────────────────────────────────────────────────────┘   │   │
│  └────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                        │
└───────────────────────────────────────────────────────────────────────────────────────┘
```

### Workiz-Specific Extensions

| Extension | Purpose | Implementation |
|-----------|---------|----------------|
| `WorkizPRReviewer` | Enhanced reviewer with Workiz rules | Extends `PRReviewer` |
| `WorkizPRCodeSuggestions` | Enhanced code suggestions with Workiz standards | Extends `PRCodeSuggestions` |
| `AgentOrchestrator` | Coordinates multiple specialized agents | New component |
| `RepoSwarmContextLoader` | Loads cross-repo architecture context | New component |
| `JiraContextProvider` | RAG for Jira ticket context | New component |
| `CustomRulesEngine` | Applies Workiz coding standards | New component |

---

## 3. Database Schema

### Core Tables

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Repositories table
CREATE TABLE repositories (
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
CREATE TABLE code_chunks (
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

-- Jira tickets
CREATE TABLE jira_tickets (
    id SERIAL PRIMARY KEY,
    ticket_key VARCHAR(50) UNIQUE NOT NULL,
    project_key VARCHAR(20) NOT NULL,
    summary TEXT,
    description TEXT,
    issue_type VARCHAR(50),
    status VARCHAR(50),
    priority VARCHAR(50),
    assignee VARCHAR(255),
    created_date TIMESTAMP,
    updated_date TIMESTAMP,
    embedding vector(1536),
    metadata JSONB,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Review history
CREATE TABLE review_history (
    id SERIAL PRIMARY KEY,
    pr_url TEXT NOT NULL,
    repository_id INT REFERENCES repositories(id),
    review_type VARCHAR(50),
    comments_count INT,
    issues_found JSONB,
    context_used JSONB,
    model_used VARCHAR(100),
    tokens_used INT,
    duration_ms INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Custom rules
CREATE TABLE custom_rules (
    id SERIAL PRIMARY KEY,
    rule_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    severity VARCHAR(20),
    languages TEXT[],
    pattern TEXT,
    message_template TEXT,
    autofix_template TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PubSub events topology
CREATE TABLE pubsub_events (
    id SERIAL PRIMARY KEY,
    repository_id INT REFERENCES repositories(id),
    file_path TEXT NOT NULL,
    line_number INT,
    topic VARCHAR(255) NOT NULL,
    event_type VARCHAR(50),
    handler_name VARCHAR(255),
    message_schema VARCHAR(255),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API usage tracking
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

-- Package dependencies
CREATE TABLE package_dependencies (
    id SERIAL PRIMARY KEY,
    repository_id INT REFERENCES repositories(id),
    package_name VARCHAR(255) NOT NULL,
    version_spec VARCHAR(100),
    dep_type VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repository_id, package_name)
);

-- Internal packages registry
CREATE TABLE internal_packages (
    id SERIAL PRIMARY KEY,
    package_name VARCHAR(255) UNIQUE NOT NULL,
    latest_version VARCHAR(100),
    repo_url TEXT,
    changelog_url TEXT,
    deprecated BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- GitHub activity for Knowledge Assistant
CREATE TABLE github_activity (
    id SERIAL PRIMARY KEY,
    repository_id INT REFERENCES repositories(id),
    activity_type VARCHAR(50),  -- 'commit', 'pr', 'review'
    github_id VARCHAR(100),     -- SHA for commits, PR number for PRs
    author VARCHAR(255),
    title TEXT,
    description TEXT,
    files_changed JSONB,
    created_at TIMESTAMP,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repository_id, activity_type, github_id)
);

-- Conversation history for Knowledge Assistant
CREATE TABLE assistant_conversations (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    user_id VARCHAR(255),
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    context_used JSONB,         -- Sources used for the answer
    tokens_used INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cursor Fix Prompts: persistent storage for "Fix in Cursor" feature
-- Enables full tracking and analytics for prompt access
CREATE TABLE cursor_fix_prompts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt TEXT NOT NULL,
    file_path TEXT,
    line_number INT,
    
    -- PR Context
    repository VARCHAR(255),
    pr_number INT,
    pr_url TEXT,
    
    -- Comment Context
    comment_type VARCHAR(50),   -- 'static_analyzer', 'ai_suggestion'
    severity VARCHAR(20),       -- 'High', 'Medium', 'Low'
    finding_id VARCHAR(255),    -- Original finding/suggestion ID
    
    -- Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP,
    access_count INT DEFAULT 0,
    accessed_by VARCHAR(255)    -- GitHub username if available
);

CREATE INDEX idx_cursor_fix_prompts_repository ON cursor_fix_prompts(repository);
CREATE INDEX idx_cursor_fix_prompts_pr_number ON cursor_fix_prompts(pr_number);
CREATE INDEX idx_cursor_fix_prompts_comment_type ON cursor_fix_prompts(comment_type);
CREATE INDEX idx_cursor_fix_prompts_created_at ON cursor_fix_prompts(created_at);

-- Indexes
CREATE INDEX idx_code_chunks_embedding ON code_chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_jira_tickets_embedding ON jira_tickets USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_code_chunks_repo ON code_chunks(repository_id);
CREATE INDEX idx_pubsub_events_topic ON pubsub_events(topic);
CREATE INDEX idx_api_usage_timestamp ON api_usage(timestamp);
CREATE INDEX idx_github_activity_author ON github_activity(author);
CREATE INDEX idx_github_activity_created ON github_activity(created_at);
CREATE INDEX idx_github_activity_repo ON github_activity(repository_id);
CREATE INDEX idx_assistant_conversations_session ON assistant_conversations(session_id);
```

---

## 4. Custom Rules Engine

### Rules Loader

```python
# pr_agent/tools/custom_rules_loader.py
from dataclasses import dataclass
from typing import List, Optional
import re

@dataclass
class CustomRule:
    rule_id: str
    name: str
    description: str
    category: str
    severity: str  # 'error', 'warning', 'info'
    languages: List[str]
    pattern: Optional[str]  # regex pattern
    message_template: str
    autofix_template: Optional[str]
    enabled: bool = True

class CustomRulesLoader:
    """Load custom rules from TOML and database."""
    
    async def load_rules(self) -> List[CustomRule]:
        rules = []
        rules.extend(self._load_from_toml())
        rules.extend(await self._load_from_database())
        return [r for r in rules if r.enabled]
    
    def _load_from_toml(self) -> List[CustomRule]:
        # Load from pr_agent/settings/workiz_rules.toml
        pass
    
    async def _load_from_database(self) -> List[CustomRule]:
        # Load from custom_rules table
        pass
```

### Rules Configuration (`workiz_rules.toml`)

```toml
# pr_agent/settings/workiz_rules.toml

[rules.code_quality]

[rules.code_quality.no_let_usage]
name = "No let Usage"
description = "Use const instead of let for immutable variables"
severity = "warning"
languages = ["typescript", "javascript"]
pattern = "\\blet\\s+\\w+"
message = "Use `const` instead of `let`. If mutation is needed, use immutable operations."

[rules.code_quality.small_functions]
name = "Small Functions"
description = "Functions should be small and focused"
severity = "warning"
languages = ["typescript", "javascript", "php", "python"]
max_lines = 30
message = "Function exceeds {max_lines} lines. Consider splitting into smaller functions."

[rules.code_quality.no_inline_comments]
name = "No Inline Comments"
description = "Avoid inline comments"
severity = "info"
languages = ["typescript", "javascript", "php"]
pattern = "(?<!^)//.*$"
message = "Avoid inline comments. Use descriptive variable/function names instead."

[rules.nestjs]

[rules.nestjs.structured_logging]
name = "Structured Logging"
description = "All logger calls must include context object"
severity = "error"
languages = ["typescript"]
frameworks = ["nestjs"]
pattern = "this\\.logger\\.(log|warn|error|debug)\\([^,]+\\)(?!.*,\\s*\\{)"
message = "Logger call missing context object. Add { accountId, userId, ... } as second parameter."

[rules.nestjs.pubsub_async_ack]
name = "PubSub Async Acknowledge"
description = "PubSub handlers must use @PubSubAsyncAcknowledge"
severity = "error"
languages = ["typescript"]
frameworks = ["nestjs"]
check_decorator = "@PubSubAsyncAcknowledge"
message = "PubSub handler missing @PubSubAsyncAcknowledge decorator."

[rules.nestjs.dependency_injection]
name = "Dependency Injection"
description = "Use NestJS DI, avoid manual instantiation"
severity = "warning"
languages = ["typescript"]
frameworks = ["nestjs"]
pattern = "new\\s+(\\w+Service|\\w+Repository|\\w+Provider)\\s*\\("
message = "Avoid manual instantiation. Use constructor injection instead."

[rules.security]

[rules.security.no_hardcoded_secrets]
name = "No Hardcoded Secrets"
description = "Secrets should not be hardcoded"
severity = "error"
languages = ["all"]
patterns = [
    "(?i)(password|secret|api_key|apikey|token)\\s*=\\s*['\"][^'\"]{8,}['\"]",
    "sk-[a-zA-Z0-9]{32,}",
    "ghp_[a-zA-Z0-9]{36}"
]
message = "Potential hardcoded secret detected. Use environment variables."

[rules.security.sql_injection]
name = "SQL Injection Prevention"
description = "Avoid string interpolation in SQL queries"
severity = "error"
languages = ["typescript", "javascript", "php", "python"]
pattern = "(query|execute)\\s*\\([^)]*\\$\\{|f['\"].*SELECT.*\\{|\\\"SELECT.*\\\" \\+ |'SELECT.*' \\. "
message = "Potential SQL injection. Use parameterized queries."

[rules.testing]

[rules.testing.test_coverage]
name = "Test Coverage Required"
description = "New files should have corresponding test files"
severity = "warning"
languages = ["typescript"]
check_type = "file_pair"
source_pattern = "src/.*\\.ts$"
test_pattern = "src/.*\\.spec\\.ts$"
message = "New source file without test coverage. Add corresponding .spec.ts file."
```

### Rules Engine

```python
# pr_agent/tools/custom_rules_engine.py
import re
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class RuleViolation:
    rule_id: str
    rule_name: str
    severity: str
    file_path: str
    line_number: int
    message: str
    code_snippet: str
    autofix_suggestion: Optional[str]

class CustomRulesEngine:
    """Apply custom rules to PR changes."""
    
    def __init__(self, rules: List[CustomRule]):
        self.rules = rules
    
    def analyze_file(self, file_path: str, content: str, language: str) -> List[RuleViolation]:
        violations = []
        lines = content.split('\n')
        
        applicable_rules = [r for r in self.rules if language in r.languages or 'all' in r.languages]
        
        for rule in applicable_rules:
            if rule.pattern:
                for i, line in enumerate(lines, 1):
                    if re.search(rule.pattern, line):
                        violations.append(RuleViolation(
                            rule_id=rule.rule_id,
                            rule_name=rule.name,
                            severity=rule.severity,
                            file_path=file_path,
                            line_number=i,
                            message=rule.message_template,
                            code_snippet=line.strip(),
                            autofix_suggestion=rule.autofix_template
                        ))
        
        return violations
    
    def check_test_coverage(self, added_files: List[str]) -> List[RuleViolation]:
        """Check if new source files have corresponding tests."""
        violations = []
        source_files = [f for f in added_files if f.endswith('.ts') and not f.endswith('.spec.ts')]
        test_files = set(f for f in added_files if f.endswith('.spec.ts'))
        
        for source in source_files:
            expected_test = source.replace('.ts', '.spec.ts')
            if expected_test not in test_files:
                violations.append(RuleViolation(
                    rule_id='test_coverage',
                    rule_name='Test Coverage Required',
                    severity='warning',
                    file_path=source,
                    line_number=1,
                    message=f'New file without test coverage. Consider adding {expected_test}',
                    code_snippet='',
                    autofix_suggestion=None
                ))
        
        return violations
```

---

## 5. Language Analyzers

### Base Analyzer

```python
# pr_agent/tools/language_analyzers/base_analyzer.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class CodeElement:
    name: str
    element_type: str  # 'function', 'class', 'method', 'import', etc.
    file_path: str
    start_line: int
    end_line: int
    signature: Optional[str]
    dependencies: List[str]
    metadata: Dict

@dataclass
class AnalysisResult:
    file_path: str
    language: str
    elements: List[CodeElement]
    imports: List[str]
    exports: List[str]
    api_calls: List[Dict]
    database_queries: List[Dict]
    pubsub_events: List[Dict]
    issues: List[Dict]

class BaseAnalyzer(ABC):
    """Base class for language-specific analyzers."""
    
    @abstractmethod
    def analyze(self, file_path: str, content: str) -> AnalysisResult:
        pass
    
    @abstractmethod
    def detect_language(self, file_path: str, content: str) -> bool:
        pass
    
    def extract_functions(self, content: str) -> List[CodeElement]:
        pass
    
    def extract_imports(self, content: str) -> List[str]:
        pass
```

### NestJS Analyzer

```python
# pr_agent/tools/language_analyzers/nestjs_analyzer.py
import re
from typing import List, Dict
from .base_analyzer import BaseAnalyzer, AnalysisResult, CodeElement

class NestJSAnalyzer(BaseAnalyzer):
    """Analyzer for NestJS TypeScript code."""
    
    def detect_language(self, file_path: str, content: str) -> bool:
        if not file_path.endswith('.ts'):
            return False
        nestjs_indicators = [
            '@Injectable()', '@Controller(', '@Module(',
            '@Get(', '@Post(', '@Put(', '@Delete(',
            'from \'@nestjs/'
        ]
        return any(ind in content for ind in nestjs_indicators)
    
    def analyze(self, file_path: str, content: str) -> AnalysisResult:
        return AnalysisResult(
            file_path=file_path,
            language='nestjs',
            elements=self._extract_elements(content),
            imports=self._extract_imports(content),
            exports=self._extract_exports(content),
            api_calls=self._extract_api_calls(content),
            database_queries=self._extract_db_queries(content),
            pubsub_events=self._extract_pubsub_events(content),
            issues=self._check_issues(content)
        )
    
    def _extract_elements(self, content: str) -> List[CodeElement]:
        elements = []
        
        # Extract classes
        class_pattern = r'@(Injectable|Controller|Module)\([^)]*\)\s*export\s+class\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            elements.append(CodeElement(
                name=match.group(2),
                element_type=f'nestjs_{match.group(1).lower()}',
                file_path='',
                start_line=content[:match.start()].count('\n') + 1,
                end_line=0,
                signature=match.group(0),
                dependencies=[],
                metadata={'decorator': match.group(1)}
            ))
        
        return elements
    
    def _extract_pubsub_events(self, content: str) -> List[Dict]:
        events = []
        
        # PubSub handlers
        handler_pattern = r'@PubSubTopic\([\'"](\w+)[\'"]\)'
        for match in re.finditer(handler_pattern, content):
            events.append({
                'topic': match.group(1),
                'type': 'subscribe',
                'line': content[:match.start()].count('\n') + 1
            })
        
        return events
    
    def _check_issues(self, content: str) -> List[Dict]:
        issues = []
        
        # Check for logger without context
        logger_pattern = r'this\.logger\.(log|warn|error|debug)\([^,)]+\)(?!\s*,)'
        for match in re.finditer(logger_pattern, content):
            issues.append({
                'type': 'logger_missing_context',
                'line': content[:match.start()].count('\n') + 1,
                'message': 'Logger call missing context object'
            })
        
        # Check for let usage
        let_pattern = r'\blet\s+\w+'
        for match in re.finditer(let_pattern, content):
            issues.append({
                'type': 'let_usage',
                'line': content[:match.start()].count('\n') + 1,
                'message': 'Use const instead of let'
            })
        
        return issues
```

### PHP Analyzer

```python
# pr_agent/tools/language_analyzers/php_analyzer.py
import re
from typing import List, Dict
from .base_analyzer import BaseAnalyzer, AnalysisResult, CodeElement

class PHPAnalyzer(BaseAnalyzer):
    """Analyzer for PHP code (Laravel/Eloquent)."""
    
    def detect_language(self, file_path: str, content: str) -> bool:
        return file_path.endswith('.php')
    
    def analyze(self, file_path: str, content: str) -> AnalysisResult:
        return AnalysisResult(
            file_path=file_path,
            language='php',
            elements=self._extract_elements(content),
            imports=self._extract_imports(content),
            exports=[],
            api_calls=self._extract_api_calls(content),
            database_queries=self._extract_db_queries(content),
            pubsub_events=[],
            issues=self._check_issues(content)
        )
    
    def _extract_db_queries(self, content: str) -> List[Dict]:
        queries = []
        
        # Raw SQL
        raw_sql = r'DB::raw\s*\([\'"]([^"\']+)[\'"]\)'
        for match in re.finditer(raw_sql, content):
            queries.append({
                'type': 'raw_sql',
                'query': match.group(1),
                'line': content[:match.start()].count('\n') + 1
            })
        
        # Eloquent queries
        eloquent_pattern = r'(\w+)::(?:where|find|get|first|all)\s*\('
        for match in re.finditer(eloquent_pattern, content):
            queries.append({
                'type': 'eloquent',
                'model': match.group(1),
                'line': content[:match.start()].count('\n') + 1
            })
        
        return queries
    
    def _check_issues(self, content: str) -> List[Dict]:
        issues = []
        
        # Check for dd() or dump()
        debug_pattern = r'\b(dd|dump|var_dump|print_r)\s*\('
        for match in re.finditer(debug_pattern, content):
            issues.append({
                'type': 'debug_statement',
                'line': content[:match.start()].count('\n') + 1,
                'message': f'Debug statement {match.group(1)}() should be removed'
            })
        
        # Check for raw SQL with variables
        sql_injection = r'DB::(?:select|insert|update|delete)\s*\([^)]*\$'
        for match in re.finditer(sql_injection, content):
            issues.append({
                'type': 'sql_injection',
                'line': content[:match.start()].count('\n') + 1,
                'message': 'Potential SQL injection - use parameterized queries'
            })
        
        return issues
```

### React Analyzer

```python
# pr_agent/tools/language_analyzers/react_analyzer.py
import re
from typing import List, Dict
from .base_analyzer import BaseAnalyzer, AnalysisResult, CodeElement

class ReactAnalyzer(BaseAnalyzer):
    """Analyzer for React TypeScript code."""
    
    def detect_language(self, file_path: str, content: str) -> bool:
        if not (file_path.endswith('.tsx') or file_path.endswith('.jsx')):
            return False
        react_indicators = ['import React', 'from \'react\'', 'useState', 'useEffect']
        return any(ind in content for ind in react_indicators)
    
    def analyze(self, file_path: str, content: str) -> AnalysisResult:
        return AnalysisResult(
            file_path=file_path,
            language='react',
            elements=self._extract_components(content),
            imports=self._extract_imports(content),
            exports=self._extract_exports(content),
            api_calls=self._extract_api_calls(content),
            database_queries=[],
            pubsub_events=[],
            issues=self._check_issues(content)
        )
    
    def _extract_styles(self, content: str) -> Dict:
        """Extract inline styles for Figma comparison."""
        styles = {
            'colors': set(),
            'fonts': set(),
            'spacing': set()
        }
        
        # Extract color values
        color_pattern = r'(?:color|backgroundColor|borderColor):\s*[\'"]?(#[0-9a-fA-F]{3,6}|rgb[a]?\([^)]+\))[\'"]?'
        for match in re.finditer(color_pattern, content):
            styles['colors'].add(match.group(1))
        
        # Extract font sizes
        font_pattern = r'fontSize:\s*[\'"]?(\d+(?:px|rem|em)?)[\'"]?'
        for match in re.finditer(font_pattern, content):
            styles['fonts'].add(match.group(1))
        
        return {k: list(v) for k, v in styles.items()}
    
    def _check_issues(self, content: str) -> List[Dict]:
        issues = []
        
        # Check for useEffect without deps
        effect_pattern = r'useEffect\s*\(\s*\(\)\s*=>\s*\{[^}]+\}\s*\)'
        for match in re.finditer(effect_pattern, content):
            if ', [' not in match.group(0) and ', []' not in match.group(0):
                issues.append({
                    'type': 'useeffect_no_deps',
                    'line': content[:match.start()].count('\n') + 1,
                    'message': 'useEffect missing dependency array'
                })
        
        # Check for missing key prop in lists
        map_pattern = r'\.map\s*\([^)]+\)\s*=>\s*(?:<\w+(?!\s+key=))'
        for match in re.finditer(map_pattern, content):
            issues.append({
                'type': 'missing_key',
                'line': content[:match.start()].count('\n') + 1,
                'message': 'List item missing key prop'
            })
        
        return issues
```

### Python Analyzer

```python
# pr_agent/tools/language_analyzers/python_analyzer.py
import re
from typing import List, Dict
from .base_analyzer import BaseAnalyzer, AnalysisResult, CodeElement

class PythonAnalyzer(BaseAnalyzer):
    """Analyzer for Python code (FastAPI/Django)."""
    
    def detect_language(self, file_path: str, content: str) -> bool:
        return file_path.endswith('.py')
    
    def analyze(self, file_path: str, content: str) -> AnalysisResult:
        framework = self._detect_framework(content)
        
        return AnalysisResult(
            file_path=file_path,
            language=f'python_{framework}' if framework else 'python',
            elements=self._extract_elements(content),
            imports=self._extract_imports(content),
            exports=[],
            api_calls=self._extract_api_calls(content),
            database_queries=self._extract_db_queries(content),
            pubsub_events=[],
            issues=self._check_issues(content, framework)
        )
    
    def _detect_framework(self, content: str) -> str:
        if 'from fastapi' in content or 'FastAPI' in content:
            return 'fastapi'
        if 'from django' in content:
            return 'django'
        return ''
    
    def _extract_db_queries(self, content: str) -> List[Dict]:
        queries = []
        
        # SQLAlchemy raw queries
        raw_pattern = r'(?:execute|text)\s*\([\'"]([^"\']+)[\'"]'
        for match in re.finditer(raw_pattern, content):
            queries.append({
                'type': 'sqlalchemy_raw',
                'query': match.group(1),
                'line': content[:match.start()].count('\n') + 1
            })
        
        # asyncpg queries
        asyncpg_pattern = r'(?:fetch|execute)\s*\([\'"]([^"\']+)[\'"]'
        for match in re.finditer(asyncpg_pattern, content):
            queries.append({
                'type': 'asyncpg',
                'query': match.group(1),
                'line': content[:match.start()].count('\n') + 1
            })
        
        return queries
    
    def _check_issues(self, content: str, framework: str) -> List[Dict]:
        issues = []
        
        # Check for print statements
        print_pattern = r'\bprint\s*\('
        for match in re.finditer(print_pattern, content):
            issues.append({
                'type': 'print_statement',
                'line': content[:match.start()].count('\n') + 1,
                'message': 'Use logging instead of print()'
            })
        
        # FastAPI sync endpoints
        if framework == 'fastapi':
            sync_pattern = r'@(?:app|router)\.(get|post|put|delete)\([^)]*\)\s*\ndef\s+'
            for match in re.finditer(sync_pattern, content):
                issues.append({
                    'type': 'sync_endpoint',
                    'line': content[:match.start()].count('\n') + 1,
                    'message': 'Consider using async def for FastAPI endpoints'
                })
        
        return issues
```

---

## 6. Database Analyzers

### SQL Analyzer

```python
# pr_agent/tools/sql_analyzer.py
import re
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class SQLIssue:
    issue_type: str
    severity: str
    message: str
    line_number: int
    query_snippet: str
    suggestion: str

class SQLAnalyzer:
    """Analyze SQL queries for potential issues."""
    
    def analyze_mysql_query(self, query: str, line: int = 0) -> List[SQLIssue]:
        issues = []
        query_upper = query.upper()
        
        # SELECT * detection
        if 'SELECT *' in query_upper:
            issues.append(SQLIssue(
                issue_type='select_star',
                severity='warning',
                message='Avoid SELECT * - specify columns explicitly',
                line_number=line,
                query_snippet=query[:100],
                suggestion='List required columns explicitly'
            ))
        
        # LIMIT without ORDER BY
        if 'LIMIT' in query_upper and 'ORDER BY' not in query_upper:
            issues.append(SQLIssue(
                issue_type='limit_without_order',
                severity='warning',
                message='LIMIT without ORDER BY may return inconsistent results',
                line_number=line,
                query_snippet=query[:100],
                suggestion='Add ORDER BY clause'
            ))
        
        # String interpolation (potential injection)
        if re.search(r'\$\{|\+\s*\w+\s*\+|%s|format\(', query):
            issues.append(SQLIssue(
                issue_type='sql_injection',
                severity='error',
                message='Potential SQL injection - use parameterized queries',
                line_number=line,
                query_snippet=query[:100],
                suggestion='Use prepared statements'
            ))
        
        return issues
    
    def analyze_mongodb_query(self, query: str, line: int = 0) -> List[SQLIssue]:
        issues = []
        
        # $regex without anchor
        if '$regex' in query and '^' not in query:
            issues.append(SQLIssue(
                issue_type='regex_no_anchor',
                severity='warning',
                message='$regex without ^ anchor cannot use indexes efficiently',
                line_number=line,
                query_snippet=query[:100],
                suggestion='Add ^ anchor to regex pattern'
            ))
        
        # Large $in array
        if '$in' in query:
            in_match = re.search(r'\$in[\'"]?\s*:\s*\[([^\]]+)\]', query)
            if in_match and in_match.group(1).count(',') > 100:
                issues.append(SQLIssue(
                    issue_type='large_in_array',
                    severity='warning',
                    message='Large $in array may cause performance issues',
                    line_number=line,
                    query_snippet=query[:100],
                    suggestion='Consider using $lookup or batching'
                ))
        
        return issues
```

---

## 7. PubSub Event System

### PubSub Analyzer

```python
# pr_agent/tools/pubsub_analyzer.py
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass
import re

@dataclass
class PubSubEvent:
    topic: str
    event_name: str
    event_type: str  # 'publish' or 'subscribe'
    repository: str
    file_path: str
    line_number: int
    handler_name: str
    message_schema: str

class PubSubAnalyzer:
    """Analyze PubSub event patterns and topology."""
    
    def __init__(self, db):
        self.db = db
    
    def extract_events_from_nestjs(self, content: str, file_path: str, repo: str) -> List[PubSubEvent]:
        events = []
        
        # @PubSubTopic decorator
        topic_pattern = r'@PubSubTopic\s*\(\s*[\'"]([^\'"]+)[\'"]'
        event_pattern = r'@PubSubEvent\s*\(\s*[\'"]([^\'"]+)[\'"]'
        handler_pattern = r'(?:async\s+)?(\w+)\s*\(\s*@PubSubPayload'
        
        lines = content.split('\n')
        current_topic = None
        
        for i, line in enumerate(lines, 1):
            topic_match = re.search(topic_pattern, line)
            if topic_match:
                current_topic = topic_match.group(1)
            
            event_match = re.search(event_pattern, line)
            if event_match and current_topic:
                events.append(PubSubEvent(
                    topic=current_topic,
                    event_name=event_match.group(1),
                    event_type='subscribe',
                    repository=repo,
                    file_path=file_path,
                    line_number=i,
                    handler_name='',
                    message_schema=''
                ))
        
        return events
    
    async def build_topology(self) -> Dict:
        """Build complete event topology across all repos."""
        async with self.db.connection() as conn:
            events = await conn.fetch("SELECT * FROM pubsub_events")
        
        topology = {
            'topics': {},
            'orphan_publishers': [],
            'orphan_subscribers': []
        }
        
        publishers = {}
        subscribers = {}
        
        for event in events:
            topic = event['topic']
            if event['event_type'] == 'publish':
                publishers.setdefault(topic, []).append(event)
            else:
                subscribers.setdefault(topic, []).append(event)
        
        # Find orphans
        for topic in set(publishers.keys()) - set(subscribers.keys()):
            topology['orphan_publishers'].extend(publishers[topic])
        
        for topic in set(subscribers.keys()) - set(publishers.keys()):
            topology['orphan_subscribers'].extend(subscribers[topic])
        
        return topology
    
    def check_patterns(self, events: List[PubSubEvent], content: str) -> List[Dict]:
        """Check for PubSub anti-patterns."""
        issues = []
        
        # Check for missing @PubSubAsyncAcknowledge
        if '@PubSubTopic' in content and '@PubSubAsyncAcknowledge' not in content:
            issues.append({
                'type': 'missing_async_ack',
                'severity': 'error',
                'message': 'PubSub handler missing @PubSubAsyncAcknowledge decorator'
            })
        
        # Check for sync handlers
        if '@PubSubEvent' in content:
            handler_pattern = r'@PubSubEvent[^)]+\)[^}]*\n\s*(?!async\s)'
            if re.search(handler_pattern, content):
                issues.append({
                    'type': 'sync_handler',
                    'severity': 'warning',
                    'message': 'PubSub handler should be async'
                })
        
        return issues
```

---

## 8. Integrations

### 8.1 Jira Integration

```python
# pr_agent/integrations/jira_client.py
from jira import JIRA
from typing import List, Dict, Optional
from dataclasses import dataclass
import asyncio

@dataclass
class JiraTicket:
    key: str
    summary: str
    description: str
    issue_type: str
    status: str
    priority: str
    assignee: str
    labels: List[str]
    components: List[str]
    linked_issues: List[str]
    comments: List[Dict]
    attachments: List[str]

class JiraClient:
    """Client for Jira API integration."""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        self.jira = JIRA(
            server=base_url,
            basic_auth=(email, api_token)
        )
    
    def get_ticket(self, ticket_key: str) -> Optional[JiraTicket]:
        try:
            issue = self.jira.issue(ticket_key, expand='changelog,comments')
            return JiraTicket(
                key=issue.key,
                summary=issue.fields.summary,
                description=issue.fields.description or '',
                issue_type=issue.fields.issuetype.name,
                status=issue.fields.status.name,
                priority=issue.fields.priority.name if issue.fields.priority else 'None',
                assignee=issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                labels=issue.fields.labels,
                components=[c.name for c in issue.fields.components],
                linked_issues=[link.outwardIssue.key for link in issue.fields.issuelinks if hasattr(link, 'outwardIssue')],
                comments=[{'author': c.author.displayName, 'body': c.body} for c in issue.fields.comment.comments],
                attachments=[a.filename for a in issue.fields.attachment]
            )
        except Exception:
            return None
    
    def get_related_tickets(self, ticket_key: str) -> List[JiraTicket]:
        """Get tickets related to this one (linked, same component, similar summary)."""
        ticket = self.get_ticket(ticket_key)
        if not ticket:
            return []
        
        related = []
        
        # Get linked issues
        for linked_key in ticket.linked_issues:
            linked = self.get_ticket(linked_key)
            if linked:
                related.append(linked)
        
        # Search for similar tickets
        if ticket.components:
            jql = f'component in ({",".join(ticket.components)}) AND key != {ticket_key} ORDER BY updated DESC'
            issues = self.jira.search_issues(jql, maxResults=5)
            for issue in issues:
                related.append(self.get_ticket(issue.key))
        
        return related
    
    def extract_figma_url(self, ticket_key: str) -> Optional[str]:
        """Extract Figma URL from ticket description or attachments."""
        ticket = self.get_ticket(ticket_key)
        if not ticket:
            return None
        
        import re
        figma_pattern = r'https://(?:www\.)?figma\.com/(?:file|design)/([a-zA-Z0-9]+)'
        
        # Check description
        if ticket.description:
            match = re.search(figma_pattern, ticket.description)
            if match:
                return match.group(0)
        
        # Check comments
        for comment in ticket.comments:
            match = re.search(figma_pattern, comment['body'])
            if match:
                return match.group(0)
        
        return None
```

### 8.2 RepoSwarm Integration

RepoSwarm is based on [royosherove/repo-swarm](https://github.com/royosherove/repo-swarm), an AI-powered multi-repo architecture discovery platform. We extract and adapt its core components (prompts and investigator logic) to work within PR Agent without requiring Temporal or DynamoDB.

#### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        RepoSwarm Integration (Embedded)                          │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│   Original RepoSwarm                      PR Agent Adaptation                    │
│   ┌─────────────────────┐                 ┌─────────────────────┐               │
│   │  Temporal Workflows │  ──────────►    │  Async Python       │               │
│   │  (orchestration)    │   Replace       │  Functions          │               │
│   └─────────────────────┘                 └─────────────────────┘               │
│                                                                                  │
│   ┌─────────────────────┐                 ┌─────────────────────┐               │
│   │  DynamoDB           │  ──────────►    │  PostgreSQL         │               │
│   │  (caching)          │   Replace       │  + pgvector         │               │
│   └─────────────────────┘                 └─────────────────────┘               │
│                                                                                  │
│   ┌─────────────────────┐                 ┌─────────────────────┐               │
│   │  Direct API calls   │  ──────────►    │  LiteLLM            │               │
│   │  (model-specific)   │   Replace       │  (model-agnostic)   │               │
│   └─────────────────────┘                 └─────────────────────┘               │
│                                                                                  │
│   ┌─────────────────────┐                 ┌─────────────────────┐               │
│   │  prompts/           │  ──────────►    │  prompts/           │               │
│   │  (analysis prompts) │   Keep          │  (same structure)   │               │
│   └─────────────────────┘                 └─────────────────────┘               │
│                                                                                  │
│   ┌─────────────────────┐                 ┌─────────────────────┐               │
│   │  src/investigator/  │  ──────────►    │  tools/reposwarm/   │               │
│   │  (analysis logic)   │   Adapt         │  investigator.py    │               │
│   └─────────────────────┘                 └─────────────────────┘               │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

#### Directory Structure

```
pr_agent/tools/reposwarm/
├── __init__.py
├── investigator.py              # Core analysis logic (adapted from RepoSwarm)
├── repo_type_detector.py        # Detect backend/frontend/mobile/etc
├── structure_analyzer.py        # Build file tree and structure
├── context_loader.py            # Load analysis results for PR review
└── prompts/                     # Copied from RepoSwarm
    ├── backend/
    │   ├── nestjs/
    │   │   ├── prompts.json
    │   │   ├── api-endpoints.md
    │   │   ├── database-entities.md
    │   │   └── pubsub-events.md
    │   ├── nodejs/
    │   ├── python/
    │   └── php/
    ├── frontend/
    │   └── react/
    │       ├── prompts.json
    │       ├── components.md
    │       └── state-management.md
    ├── mobile/
    ├── libraries/
    ├── infra-as-code/
    └── shared/
        ├── security/
        ├── auth/
        └── monitoring/
```

#### Core Investigator (Adapted from RepoSwarm)

```python
# pr_agent/tools/reposwarm/investigator.py
"""
Repository architecture investigator.
Adapted from https://github.com/royosherove/repo-swarm
Removes Temporal/DynamoDB dependencies, uses PostgreSQL and LiteLLM.
"""
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler


class RepositoryInvestigator:
    """
    Analyzes repository architecture and generates context for PR reviews.
    Adapted from RepoSwarm without Temporal dependency.
    """
    
    def __init__(self, db_conn, ai_handler: BaseAiHandler, prompts_dir: Path = None):
        self.db = db_conn
        self.ai = ai_handler
        self.prompts_dir = prompts_dir or Path(__file__).parent / "prompts"
    
    def investigate(self, repo_url: str, branch: str = None) -> Dict:
        """
        Main entry point - analyzes a repository.
        Replaces Temporal workflow with simple synchronous execution.
        """
        # 1. Check cache
        cached = self._check_cache(repo_url, branch)
        if cached:
            return cached
        
        # 2. Clone repository
        repo_path = self._clone_repo(repo_url, branch)
        
        try:
            # 3. Detect repo type
            repo_type = self._detect_repo_type(repo_path)
            
            # 4. Get structure
            structure = self._get_structure(repo_path)
            
            # 5. Load prompts for this repo type
            prompts = self._load_prompts(repo_type)
            
            # 6. Run AI analysis
            results = self._analyze_with_prompts(repo_path, structure, prompts)
            
            # 7. Store results
            self._store_results(repo_url, branch, repo_type, results)
            
            return {
                'repo_url': repo_url,
                'branch': branch,
                'repo_type': repo_type,
                'analysis': results
            }
            
        finally:
            # 8. Cleanup
            self._cleanup(repo_path)
    
    def _check_cache(self, repo_url: str, branch: str) -> Optional[Dict]:
        """Check if analysis is cached in PostgreSQL."""
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT analysis_result, analyzed_at, commit_sha
                FROM repo_analysis_cache
                WHERE repo_url = %s AND (branch = %s OR branch IS NULL)
                AND analyzed_at > NOW() - INTERVAL '7 days'
                ORDER BY analyzed_at DESC
                LIMIT 1
            """, (repo_url, branch))
            row = cur.fetchone()
            if row:
                return json.loads(row[0])
        return None
    
    def _clone_repo(self, repo_url: str, branch: str = None) -> Path:
        """Clone repository to temporary directory."""
        temp_dir = Path(tempfile.mkdtemp(prefix="reposwarm_"))
        
        cmd = ["git", "clone", "--depth", "1"]
        if branch:
            cmd.extend(["--branch", branch])
        cmd.extend([repo_url, str(temp_dir / "repo")])
        
        subprocess.run(cmd, check=True, capture_output=True)
        return temp_dir / "repo"
    
    def _detect_repo_type(self, repo_path: Path) -> str:
        """
        Detect repository type based on files present.
        Returns path like 'backend/nestjs' or 'frontend/react'.
        """
        # Check for package.json (Node.js projects)
        package_json = repo_path / "package.json"
        if package_json.exists():
            pkg = json.loads(package_json.read_text())
            deps = {
                **pkg.get("dependencies", {}),
                **pkg.get("devDependencies", {})
            }
            
            # NestJS
            if "@nestjs/core" in deps:
                return "backend/nestjs"
            
            # React frontend
            if "react" in deps:
                if "next" in deps:
                    return "frontend/nextjs"
                return "frontend/react"
            
            # Plain Node.js
            if "express" in deps or "fastify" in deps:
                return "backend/nodejs"
        
        # PHP (Laravel, etc.)
        if (repo_path / "composer.json").exists():
            composer = json.loads((repo_path / "composer.json").read_text())
            require = composer.get("require", {})
            if "laravel/framework" in require:
                return "backend/laravel"
            return "backend/php"
        
        # Python
        if (repo_path / "requirements.txt").exists() or (repo_path / "pyproject.toml").exists():
            # Check for FastAPI/Django/Flask
            reqs_file = repo_path / "requirements.txt"
            if reqs_file.exists():
                reqs = reqs_file.read_text().lower()
                if "fastapi" in reqs:
                    return "backend/python-fastapi"
                if "django" in reqs:
                    return "backend/python-django"
            return "backend/python"
        
        # Infrastructure
        if (repo_path / "terraform").exists() or (repo_path / "main.tf").exists():
            return "infra-as-code/terraform"
        if (repo_path / "helm").exists():
            return "infra-as-code/helm"
        
        return "backend/generic"
    
    def _get_structure(self, repo_path: Path, max_depth: int = 4) -> Dict:
        """Build file tree structure."""
        def build_tree(path: Path, depth: int = 0) -> Dict:
            if depth > max_depth:
                return {"truncated": True}
            
            result = {"name": path.name, "type": "directory", "children": []}
            
            try:
                for item in sorted(path.iterdir()):
                    # Skip hidden and common ignore patterns
                    if item.name.startswith('.') or item.name in [
                        'node_modules', 'venv', '__pycache__', 'dist', 'build',
                        '.git', 'coverage', '.next'
                    ]:
                        continue
                    
                    if item.is_dir():
                        result["children"].append(build_tree(item, depth + 1))
                    else:
                        result["children"].append({
                            "name": item.name,
                            "type": "file",
                            "size": item.stat().st_size
                        })
            except PermissionError:
                pass
            
            return result
        
        return build_tree(repo_path)
    
    def _load_prompts(self, repo_type: str) -> List[Dict]:
        """Load analysis prompts for the detected repo type."""
        prompts_file = self.prompts_dir / repo_type / "prompts.json"
        
        if prompts_file.exists():
            return json.loads(prompts_file.read_text())
        
        # Fallback to generic prompts
        generic_prompts = self.prompts_dir / "backend" / "generic" / "prompts.json"
        if generic_prompts.exists():
            return json.loads(generic_prompts.read_text())
        
        # Default minimal prompts
        return [
            {
                "name": "overview",
                "prompt_file": "overview.md",
                "description": "General architecture overview"
            }
        ]
    
    def _analyze_with_prompts(
        self, 
        repo_path: Path, 
        structure: Dict, 
        prompts: List[Dict]
    ) -> Dict:
        """Run AI analysis using the loaded prompts."""
        results = {}
        
        for prompt_config in prompts:
            prompt_name = prompt_config["name"]
            prompt_file = self.prompts_dir / prompt_config.get("prompt_file", f"{prompt_name}.md")
            
            if not prompt_file.exists():
                continue
            
            prompt_template = prompt_file.read_text()
            
            # Gather relevant files based on prompt type
            relevant_files = self._gather_relevant_files(repo_path, prompt_name)
            
            # Build the full prompt
            full_prompt = f"""
{prompt_template}

## Repository Structure
```json
{json.dumps(structure, indent=2)[:5000]}
```

## Relevant Files
{relevant_files[:50000]}
"""
            
            # Call AI (via LiteLLM)
            response, _ = self.ai.chat_completion(
                model=self.ai.model,
                system="You are an expert software architect analyzing repository structure.",
                user=full_prompt
            )
            
            results[prompt_name] = response
        
        return results
    
    def _gather_relevant_files(self, repo_path: Path, prompt_name: str) -> str:
        """Gather file contents relevant to the analysis type."""
        patterns = {
            "api-endpoints": ["*.controller.ts", "*.controller.js", "routes/*.ts", "routes/*.js"],
            "database-entities": ["*.entity.ts", "models/*.ts", "models/*.py", "*.model.ts"],
            "pubsub-events": ["*.subscriber.ts", "*.publisher.ts", "*pubsub*", "*event*"],
            "components": ["*.tsx", "*.jsx", "components/**/*"],
            "security": ["*auth*", "*security*", "*guard*", "*middleware*"],
            "overview": ["README.md", "package.json", "composer.json", "requirements.txt"]
        }
        
        file_patterns = patterns.get(prompt_name, ["*.ts", "*.js", "*.py", "*.php"])
        
        content_parts = []
        total_size = 0
        max_size = 50000  # Limit total content size
        
        for pattern in file_patterns:
            for file_path in repo_path.rglob(pattern.replace("**/*", "*")):
                if total_size > max_size:
                    break
                if file_path.is_file() and file_path.stat().st_size < 10000:
                    try:
                        content = file_path.read_text()
                        rel_path = file_path.relative_to(repo_path)
                        content_parts.append(f"### {rel_path}\n```\n{content}\n```\n")
                        total_size += len(content)
                    except Exception:
                        pass
        
        return "\n".join(content_parts)
    
    def _store_results(
        self, 
        repo_url: str, 
        branch: str, 
        repo_type: str, 
        results: Dict
    ) -> None:
        """Store analysis results in PostgreSQL."""
        with self.db.cursor() as cur:
            cur.execute("""
                INSERT INTO repo_analysis_cache 
                (repo_url, branch, repo_type, analysis_result, analyzed_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (repo_url, branch) DO UPDATE SET
                    repo_type = EXCLUDED.repo_type,
                    analysis_result = EXCLUDED.analysis_result,
                    analyzed_at = EXCLUDED.analyzed_at
            """, (repo_url, branch, repo_type, json.dumps(results)))
        self.db.commit()
    
    def _cleanup(self, repo_path: Path) -> None:
        """Remove temporary clone directory."""
        try:
            shutil.rmtree(repo_path.parent)
        except Exception:
            pass
```

#### Context Loader for PR Reviews

```python
# pr_agent/tools/reposwarm/context_loader.py
"""Load RepoSwarm analysis results for PR review context."""
import json
from typing import Dict, List, Optional


class RepoSwarmContextLoader:
    """Load architectural context from RepoSwarm analysis stored in PostgreSQL."""
    
    def __init__(self, db_conn):
        self.db = db_conn
        self._cache = {}
    
    def get_architecture_context(self, repo_url: str) -> Optional[Dict]:
        """Get cached analysis for a repository."""
        if repo_url in self._cache:
            return self._cache[repo_url]
        
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT repo_type, analysis_result, analyzed_at
                FROM repo_analysis_cache
                WHERE repo_url = %s
                ORDER BY analyzed_at DESC
                LIMIT 1
            """, (repo_url,))
            row = cur.fetchone()
            
            if row:
                result = {
                    'repo_type': row[0],
                    'analysis': json.loads(row[1]),
                    'analyzed_at': row[2]
                }
                self._cache[repo_url] = result
                return result
        
        return None
    
    def get_related_services(self, repo_url: str) -> List[Dict]:
        """Get services that interact with this repo based on analysis."""
        context = self.get_architecture_context(repo_url)
        if not context or 'analysis' not in context:
            return []
        
        analysis = context['analysis']
        related = []
        
        # Extract from API endpoints analysis
        if 'api-endpoints' in analysis:
            endpoints = analysis['api-endpoints']
            # Parse HTTP calls to other services
            import re
            service_calls = re.findall(
                r'(?:fetch|axios|http)\s*\(\s*[\'"`]https?://([a-zA-Z-]+)',
                endpoints
            )
            for svc in service_calls:
                related.append({'service': svc, 'type': 'http'})
        
        # Extract from PubSub analysis
        if 'pubsub-events' in analysis:
            events = analysis['pubsub-events']
            # Parse topic subscriptions
            topics = re.findall(r'topic[:\s]+[\'"`]([^\'"`]+)', events, re.I)
            for topic in topics:
                related.append({'topic': topic, 'type': 'pubsub'})
        
        return related
    
    def get_cross_repo_context_for_pr(
        self, 
        pr_repo_url: str, 
        changed_files: List[str]
    ) -> str:
        """
        Build cross-repository context string for a PR review.
        This is the main method called by WorkizPRReviewer.
        """
        context_parts = []
        
        # Get analysis for the PR's repository
        repo_context = self.get_architecture_context(pr_repo_url)
        if repo_context:
            context_parts.append(f"## Repository Architecture ({repo_context['repo_type']})")
            
            analysis = repo_context.get('analysis', {})
            
            # Add relevant sections based on changed files
            if any(f.endswith(('.controller.ts', '.controller.js')) for f in changed_files):
                if 'api-endpoints' in analysis:
                    context_parts.append("### API Endpoints")
                    context_parts.append(analysis['api-endpoints'][:2000])
            
            if any('entity' in f.lower() or 'model' in f.lower() for f in changed_files):
                if 'database-entities' in analysis:
                    context_parts.append("### Database Entities")
                    context_parts.append(analysis['database-entities'][:2000])
            
            if any('pubsub' in f.lower() or 'event' in f.lower() for f in changed_files):
                if 'pubsub-events' in analysis:
                    context_parts.append("### PubSub Events")
                    context_parts.append(analysis['pubsub-events'][:2000])
        
        # Get related services context
        related = self.get_related_services(pr_repo_url)
        if related:
            context_parts.append("## Related Services")
            for rel in related[:5]:  # Limit to top 5
                if rel['type'] == 'http':
                    context_parts.append(f"- HTTP dependency: `{rel['service']}`")
                elif rel['type'] == 'pubsub':
                    context_parts.append(f"- PubSub topic: `{rel['topic']}`")
        
        return "\n\n".join(context_parts) if context_parts else ""
```

#### Database Schema for RepoSwarm

```sql
-- Add to migrations/002_reposwarm.sql

-- Cache for repository analysis results
CREATE TABLE IF NOT EXISTS repo_analysis_cache (
    id SERIAL PRIMARY KEY,
    repo_url TEXT NOT NULL,
    branch TEXT,
    repo_type VARCHAR(100),
    analysis_result JSONB NOT NULL,
    commit_sha VARCHAR(40),
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repo_url, branch)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_repo_analysis_repo_url 
    ON repo_analysis_cache(repo_url);

-- Track analysis history for debugging
CREATE TABLE IF NOT EXISTS repo_analysis_history (
    id SERIAL PRIMARY KEY,
    repo_url TEXT NOT NULL,
    branch TEXT,
    trigger_type VARCHAR(50),  -- 'scheduled', 'push', 'manual'
    status VARCHAR(20),        -- 'success', 'failed', 'skipped'
    duration_ms INT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Prompts Structure (from RepoSwarm)

The prompts are organized by repository type. Here's the structure based on [RepoSwarm](https://github.com/royosherove/repo-swarm):

```
prompts/
├── backend/
│   ├── nestjs/
│   │   ├── prompts.json          # List of analyses to run
│   │   ├── api-endpoints.md      # Extract REST/GraphQL endpoints
│   │   ├── database-entities.md  # Extract TypeORM entities
│   │   ├── pubsub-events.md      # Extract PubSub publishers/subscribers
│   │   └── dependencies.md       # Extract service dependencies
│   ├── nodejs/
│   ├── python/
│   ├── php/
│   └── generic/
├── frontend/
│   └── react/
│       ├── prompts.json
│       ├── components.md         # Component hierarchy
│       ├── state-management.md   # Redux/Context/Zustand usage
│       └── api-calls.md          # HTTP client calls
├── shared/
│   ├── security/
│   │   └── security-analysis.md
│   └── auth/
│       └── auth-patterns.md
└── infra-as-code/
    ├── terraform/
    └── helm/
```

Example `prompts/backend/nestjs/prompts.json`:

```json
[
  {
    "name": "api-endpoints",
    "prompt_file": "api-endpoints.md",
    "description": "Extract all REST and GraphQL endpoints"
  },
  {
    "name": "database-entities",
    "prompt_file": "database-entities.md",
    "description": "Extract TypeORM entities and relationships"
  },
  {
    "name": "pubsub-events",
    "prompt_file": "pubsub-events.md",
    "description": "Extract PubSub publishers and subscribers"
  },
  {
    "name": "dependencies",
    "prompt_file": "dependencies.md",
    "description": "Extract HTTP calls to other services"
  }
]
```

Example `prompts/backend/nestjs/api-endpoints.md`:

~~~markdown
Analyze this NestJS repository and extract all API endpoints.

For each endpoint, identify:
1. HTTP method (GET, POST, PUT, DELETE, PATCH)
2. Route path
3. Controller class and method name
4. Request DTO (if any)
5. Response DTO (if any)
6. Guards and decorators applied
7. Brief description of what it does

Output format:
```yaml
endpoints:
  - method: POST
    path: /users
    controller: UsersController
    handler: create
    request_dto: CreateUserDto
    response_dto: UserResponseDto
    guards: [JwtAuthGuard]
    description: Creates a new user account
```

Focus on:
- Controllers in `src/**/*.controller.ts`
- Route decorators (@Get, @Post, etc.)
- Parameter decorators (@Param, @Query, @Body)
- Guard decorators (@UseGuards)
~~~

### 8.3 Figma Integration

```python
# pr_agent/tools/figma/figma_mcp_client.py
from typing import Dict, List, Optional
import json
import subprocess

class FigmaMCPClient:
    """Client for interacting with Figma via MCP."""
    
    def __init__(self, mcp_server_path: str):
        self.mcp_server = mcp_server_path
    
    async def get_file_data(self, file_key: str) -> Optional[Dict]:
        """Get Figma file data via MCP."""
        result = subprocess.run(
            ['npx', '-y', '@anthropic/mcp-figma', 'get-file', file_key],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    
    async def extract_design_tokens(self, file_key: str) -> Dict:
        """Extract design tokens (colors, typography, spacing) from Figma."""
        file_data = await self.get_file_data(file_key)
        if not file_data:
            return {}
        
        tokens = {
            'colors': self._extract_colors(file_data),
            'typography': self._extract_typography(file_data),
            'spacing': self._extract_spacing(file_data)
        }
        
        return tokens
    
    def _extract_colors(self, data: Dict) -> List[Dict]:
        colors = []
        # Traverse Figma document structure for color styles
        def traverse(node):
            if 'fills' in node:
                for fill in node.get('fills', []):
                    if fill.get('type') == 'SOLID':
                        color = fill.get('color', {})
                        colors.append({
                            'name': node.get('name', 'unnamed'),
                            'hex': self._rgb_to_hex(color)
                        })
            for child in node.get('children', []):
                traverse(child)
        
        if 'document' in data:
            traverse(data['document'])
        
        return colors
    
    def _rgb_to_hex(self, color: Dict) -> str:
        r = int(color.get('r', 0) * 255)
        g = int(color.get('g', 0) * 255)
        b = int(color.get('b', 0) * 255)
        return f'#{r:02x}{g:02x}{b:02x}'


class DesignVerificationAgent:
    """Agent for comparing React implementation against Figma design."""
    
    def __init__(self, figma_client: FigmaMCPClient, ai_handler):
        self.figma = figma_client
        self.ai_handler = ai_handler
    
    async def verify_design(
        self,
        figma_url: str,
        react_files: List[Dict],
        threshold: float = 0.9
    ) -> Dict:
        """Compare React code against Figma design."""
        # Extract Figma file key from URL
        import re
        match = re.search(r'figma\.com/(?:file|design)/([a-zA-Z0-9]+)', figma_url)
        if not match:
            return {'error': 'Invalid Figma URL'}
        
        file_key = match.group(1)
        
        # Get design tokens from Figma
        design_tokens = await self.figma.extract_design_tokens(file_key)
        
        # Extract styles from React code
        code_styles = self._extract_react_styles(react_files)
        
        # Compare using AI
        comparison = await self._ai_compare(design_tokens, code_styles)
        
        return comparison
    
    def _extract_react_styles(self, files: List[Dict]) -> Dict:
        """Extract style definitions from React files."""
        styles = {'colors': [], 'fonts': [], 'spacing': []}
        
        for file in files:
            content = file.get('content', '')
            
            # Extract inline colors
            import re
            color_pattern = r'(?:color|backgroundColor|borderColor):\s*[\'"]?(#[0-9a-fA-F]{6})[\'"]?'
            for match in re.finditer(color_pattern, content):
                styles['colors'].append(match.group(1))
            
            # Extract font sizes
            font_pattern = r'fontSize:\s*[\'"]?(\d+)[\'"]?'
            for match in re.finditer(font_pattern, content):
                styles['fonts'].append(match.group(1))
        
        return styles
    
    async def _ai_compare(self, design: Dict, code: Dict) -> Dict:
        """Use AI to compare design tokens vs code styles."""
        prompt = f"""Compare these Figma design tokens with React code styles.

Design Tokens:
- Colors: {design.get('colors', [])}
- Typography: {design.get('typography', [])}
- Spacing: {design.get('spacing', [])}

Code Styles:
- Colors used: {code.get('colors', [])}
- Fonts used: {code.get('fonts', [])}
- Spacing used: {code.get('spacing', [])}

List any mismatches as review comments."""
        
        response = await self.ai_handler.chat_completion(
            model=self.config.get("llm.model", "gemini-3-pro"),
            system="You are a design reviewer comparing Figma designs to React implementations.",
            user=prompt
        )
        
        return {'analysis': response}
```

---

## 9. Auto-Fix Agent

### Core Implementation

```python
# pr_agent/tools/autofix_agent.py
from typing import List, Dict, Optional
from dataclasses import dataclass
import asyncio

@dataclass
class ReviewComment:
    id: str
    body: str
    path: str
    line: int
    diff_hunk: str
    user: str

@dataclass
class FixResult:
    comment_id: str
    success: bool
    file_path: str
    original_code: str
    fixed_code: str
    error: Optional[str]

class AutoFixAgent:
    """Agent that automatically fixes review comments."""
    
    def __init__(self, git_provider, ai_handler, config):
        self.git_provider = git_provider
        self.ai_handler = ai_handler
        self.config = config
        self.max_iterations = config.get('autofix.max_iterations', 5)
        self.models = [
            config.get('llm.model', 'gemini-3-pro'),  # Primary from config
            "gemini-2.5-pro",                           # Fallback
        ]
    
    async def run(self, pr_url: str) -> Dict:
        """Run the auto-fix loop."""
        results = {
            'iterations': 0,
            'comments_fixed': 0,
            'comments_failed': 0,
            'fixes_pr_url': None
        }
        
        # Create fixes branch
        base_branch = await self.git_provider.get_pr_branch(pr_url)
        fixes_branch = f"autofix/{base_branch}"
        await self.git_provider.create_branch(fixes_branch, base_branch)
        
        for iteration in range(self.max_iterations):
            results['iterations'] = iteration + 1
            
            # Get unresolved comments
            comments = await self.git_provider.get_review_comments(pr_url)
            unresolved = [c for c in comments if not c.get('resolved')]
            
            if not unresolved:
                break
            
            # Fix each comment
            for comment in unresolved:
                fix_result = await self._fix_comment(comment, fixes_branch)
                if fix_result.success:
                    results['comments_fixed'] += 1
                    await self.git_provider.resolve_review_comment(comment['id'])
                else:
                    results['comments_failed'] += 1
            
            # Commit fixes
            await self.git_provider.commit(
                fixes_branch,
                f"Auto-fix: iteration {iteration + 1}"
            )
            
            # Run review on fixes
            review_result = await self._run_review(fixes_branch)
            if review_result.get('issues_count', 0) == 0:
                break
        
        # Create draft PR
        if results['comments_fixed'] > 0:
            fixes_pr = await self.git_provider.create_pr(
                title=f"[Auto-Fix] Fixes for {base_branch}",
                body=self._generate_pr_body(results),
                head=fixes_branch,
                base=base_branch,
                draft=True
            )
            results['fixes_pr_url'] = fixes_pr.url
        
        return results
    
    async def _fix_comment(self, comment: Dict, branch: str) -> FixResult:
        """Fix a single review comment."""
        file_path = comment['path']
        line = comment['line']
        comment_body = comment['body']
        
        # Get file content
        content = await self.git_provider.get_file_content(file_path, branch)
        lines = content.split('\n')
        
        # Get context around the line
        start = max(0, line - 10)
        end = min(len(lines), line + 10)
        context = '\n'.join(f"{i+1}: {l}" for i, l in enumerate(lines[start:end], start))
        
        # Generate fix using AI
        BACKTICKS = '`' * 3
        prompt = f"""You are an expert code fixer. Fix the code according to the review comment.

## Review Comment
{comment_body}

## File: {file_path}
## Target Line: {line}

## Code Context (with line numbers)
{context}

## Instructions
1. Understand what the review comment is asking to fix
2. Generate the corrected code
3. Return ONLY the fixed code snippet
4. Include enough context so the fix can be applied correctly
5. Do NOT include line numbers in your output

## Fixed Code
"""
        
        for model in self.models:
            try:
                response = await self.ai_handler.chat_completion(
                    model=model,
                    system="You are a code fixer. Output only the fixed code.",
                    user=prompt,
                    temperature=0.1
                )
                
                fixed_code = self._extract_code_from_response(response)
                
                if fixed_code:
                    # Apply fix
                    await self.git_provider.update_file(
                        file_path,
                        self._apply_fix(content, line, fixed_code),
                        branch
                    )
                    
                    return FixResult(
                        comment_id=comment['id'],
                        success=True,
                        file_path=file_path,
                        original_code=lines[line-1] if line <= len(lines) else '',
                        fixed_code=fixed_code,
                        error=None
                    )
            except Exception as e:
                continue
        
        return FixResult(
            comment_id=comment['id'],
            success=False,
            file_path=file_path,
            original_code='',
            fixed_code='',
            error="All models failed to generate fix"
        )
    
    def _extract_code_from_response(self, response: str) -> str:
        """Extract code block from AI response."""
        import re
        BACKTICKS = '`' * 3
        code_pattern = rf'{BACKTICKS}(?:\w+)?\n(.*?){BACKTICKS}'
        match = re.search(code_pattern, response, re.DOTALL)
        if match:
            return match.group(1).strip()
        return response.strip()
    
    def _apply_fix(self, content: str, target_line: int, fixed_code: str) -> str:
        """Apply the fix to file content."""
        lines = content.split('\n')
        fixed_lines = fixed_code.split('\n')
        
        # Simple replacement of target line area
        # In production, use more sophisticated diff matching
        lines[target_line-1:target_line-1+len(fixed_lines)] = fixed_lines
        
        return '\n'.join(lines)
    
    def _generate_pr_body(self, results: Dict) -> str:
        return f"""## Auto-Fix Summary

This PR was automatically generated to fix review comments.

### Statistics
- **Iterations**: {results['iterations']}
- **Comments Fixed**: {results['comments_fixed']}
- **Comments Failed**: {results['comments_failed']}

### ⚠️ Important
This is a **draft PR**. Please review all changes before merging.

---
*Generated by Workiz PR Agent Auto-Fix*
"""
```

### Trigger Mechanisms

Add to webhook handler:

```python
# In github_app.py

@router.post("/api/v1/github_webhooks")
async def handle_github_webhook(request: Request):
    payload = await request.json()
    event = request.headers.get("X-GitHub-Event")
    
    # Handle check_run for Auto-Fix button
    if event == "check_run":
        if payload.get("action") == "requested_action":
            if payload.get("requested_action", {}).get("identifier") == "autofix":
                pr_url = extract_pr_url_from_check_run(payload)
                asyncio.create_task(run_autofix(pr_url))
                return {"status": "autofix_started"}
    
    # Handle comment command
    if event == "issue_comment":
        body = payload.get("comment", {}).get("body", "")
        if "/autofix" in body.lower():
            pr_url = payload.get("issue", {}).get("pull_request", {}).get("html_url")
            if pr_url:
                asyncio.create_task(run_autofix(pr_url))
                return {"status": "autofix_started"}
```

---

## 10. Auto-Discovery System

### GitHub Discovery Service

```python
# pr_agent/services/discovery_service.py
from typing import List, Dict, Optional
import aiohttp
import json
import re

class GitHubDiscoveryService:
    """Auto-discover GitHub repositories."""
    
    def __init__(self, token: str, db):
        self.token = token
        self.db = db
        self.base_url = "https://api.github.com"
        self.exclude_patterns = [
            r'.*-archive$',
            r'.*-deprecated$',
            r'.*-old$',
            r'^\..*'
        ]
    
    async def discover_org_repos(self, org: str) -> List[Dict]:
        """Discover all repositories in an organization."""
        repos = []
        page = 1
        
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.base_url}/orgs/{org}/repos?per_page=100&page={page}"
                headers = {
                    "Authorization": f"token {self.token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        break
                    
                    page_repos = await response.json()
                    if not page_repos:
                        break
                    
                    for repo in page_repos:
                        if not self._should_exclude(repo['name']):
                            detected = await self._detect_stack(session, org, repo['name'])
                            repos.append({
                                'org': org,
                                'name': repo['name'],
                                'url': repo['html_url'],
                                'default_branch': repo['default_branch'],
                                'language': repo['language'],
                                **detected
                            })
                    
                    page += 1
        
        return repos
    
    def _should_exclude(self, repo_name: str) -> bool:
        """Check if repo should be excluded."""
        return any(re.match(p, repo_name) for p in self.exclude_patterns)
    
    async def _detect_stack(self, session, org: str, repo: str) -> Dict:
        """Detect frameworks and databases from repo files."""
        result = {
            'frameworks': [],
            'databases': [],
            'is_monorepo': False
        }
        
        # Check package.json
        pkg = await self._get_file(session, org, repo, 'package.json')
        if pkg:
            deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
            
            if '@nestjs/core' in deps:
                result['frameworks'].append('nestjs')
            if 'react' in deps:
                result['frameworks'].append('react')
            if 'express' in deps:
                result['frameworks'].append('express')
            
            if 'mysql2' in deps or 'mysql' in deps:
                result['databases'].append('mysql')
            if 'mongodb' in deps or 'mongoose' in deps:
                result['databases'].append('mongodb')
            if '@elastic/elasticsearch' in deps:
                result['databases'].append('elasticsearch')
            if 'pg' in deps or 'asyncpg' in deps:
                result['databases'].append('postgresql')
        
        # Check composer.json for PHP
        composer = await self._get_file(session, org, repo, 'composer.json')
        if composer:
            result['frameworks'].append('php')
            deps = composer.get('require', {})
            if 'laravel/framework' in deps:
                result['frameworks'].append('laravel')
        
        # Check requirements.txt for Python
        reqs = await self._get_raw_file(session, org, repo, 'requirements.txt')
        if reqs:
            result['frameworks'].append('python')
            if 'fastapi' in reqs.lower():
                result['frameworks'].append('fastapi')
            if 'django' in reqs.lower():
                result['frameworks'].append('django')
        
        # Check for monorepo
        lerna = await self._get_file(session, org, repo, 'lerna.json')
        nx = await self._get_file(session, org, repo, 'nx.json')
        if lerna or nx:
            result['is_monorepo'] = True
        
        return result
    
    async def _get_file(self, session, org: str, repo: str, path: str) -> Optional[Dict]:
        """Get JSON file from repo."""
        content = await self._get_raw_file(session, org, repo, path)
        if content:
            try:
                return json.loads(content)
            except:
                pass
        return None
    
    async def _get_raw_file(self, session, org: str, repo: str, path: str) -> Optional[str]:
        """Get raw file content from repo."""
        url = f"https://raw.githubusercontent.com/{org}/{repo}/HEAD/{path}"
        headers = {"Authorization": f"token {self.token}"}
        
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.text()
        return None
    
    async def sync_repos_to_database(self, org: str) -> Dict:
        """Sync discovered repos to database."""
        repos = await self.discover_org_repos(org)
        
        async with self.db.connection() as conn:
            for repo in repos:
                await conn.execute("""
                    INSERT INTO repositories 
                    (org_name, repo_name, github_url, default_branch, 
                     primary_language, detected_frameworks, detected_databases, is_monorepo)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (org_name, repo_name) DO UPDATE SET
                        detected_frameworks = EXCLUDED.detected_frameworks,
                        detected_databases = EXCLUDED.detected_databases,
                        is_monorepo = EXCLUDED.is_monorepo
                """, org, repo['name'], repo['url'], repo['default_branch'],
                    repo['language'], json.dumps(repo['frameworks']),
                    json.dumps(repo['databases']), repo['is_monorepo'])
        
        return {'synced': len(repos)}
```

---

## 11. NPM Package Management

### Overview

Workiz internal packages are hosted on **GitHub Packages** (not npmjs.org):

- **Registry**: `https://npm.pkg.github.com/`
- **Scope**: `@workiz`
- **Source**: `Workiz/architecture` repository, `packages/` directory
- **Publishing**: Automatic via `release-packages.yml` workflow on push to `main`
- **Authentication**: 
  - Install: `NPM_READONLY_TOKEN`
  - Publish: `GH_TOKEN_PACKAGES`

### .npmrc Configuration

Services that use `@workiz` packages must have this `.npmrc`:

```
@workiz:registry=https://npm.pkg.github.com/
//npm.pkg.github.com/:_authToken=${NPM_READONLY_TOKEN}
```

### Package Analyzer

```python
# pr_agent/tools/npm_package_analyzer.py
from typing import List, Dict, Optional
from dataclasses import dataclass
import json
import aiohttp
from packaging import version

@dataclass
class PackageDependencyIssue:
    package_name: str
    issue_type: str
    message: str
    severity: str
    current_version: str
    recommended_version: Optional[str]
    affected_file: str

class NPMPackageAnalyzer:
    """Analyze NPM package dependencies in PRs."""
    
    def __init__(self, db, github_token: str, internal_packages: List[str] = None):
        self.db = db
        self.github_token = github_token
        self.internal_packages = internal_packages or ['@workiz/']
        # GitHub Packages registry for @workiz packages
        self.github_packages_api = "https://api.github.com/orgs/Workiz/packages/npm"
        # Public NPM registry for external packages
        self.npm_registry = "https://registry.npmjs.org"
    
    def is_internal_package(self, package_name: str) -> bool:
        return any(package_name.startswith(p) for p in self.internal_packages)
    
    async def analyze_package_json_changes(
        self, 
        old_content: str, 
        new_content: str,
        file_path: str
    ) -> List[PackageDependencyIssue]:
        issues = []
        
        try:
            old_pkg = json.loads(old_content) if old_content else {}
            new_pkg = json.loads(new_content)
        except json.JSONDecodeError:
            return issues
        
        old_deps = {**old_pkg.get('dependencies', {}), **old_pkg.get('devDependencies', {})}
        new_deps = {**new_pkg.get('dependencies', {}), **new_pkg.get('devDependencies', {})}
        
        for pkg_name, new_version in new_deps.items():
            old_version = old_deps.get(pkg_name)
            
            # New package added
            if old_version is None:
                if self.is_internal_package(pkg_name):
                    issue = await self._check_internal_package(pkg_name, new_version, file_path)
                    if issue:
                        issues.append(issue)
            
            # Version changed
            elif old_version != new_version:
                issues.extend(await self._check_version_change(pkg_name, old_version, new_version, file_path))
        
        return issues
    
    async def _check_version_change(
        self, pkg_name: str, old_version: str, new_version: str, file_path: str
    ) -> List[PackageDependencyIssue]:
        issues = []
        
        old_v = self._parse_version(old_version)
        new_v = self._parse_version(new_version)
        
        if not old_v or not new_v:
            return issues
        
        old_parsed = version.parse(old_v)
        new_parsed = version.parse(new_v)
        
        # Check for major version bump
        if hasattr(old_parsed, 'major') and hasattr(new_parsed, 'major'):
            if new_parsed.major > old_parsed.major:
                issues.append(PackageDependencyIssue(
                    package_name=pkg_name,
                    issue_type='breaking_change',
                    message=f"Major version bump: {old_version} -> {new_version}. Check changelog.",
                    severity='warning',
                    current_version=old_version,
                    recommended_version=new_version,
                    affected_file=file_path
                ))
        
        # Check for downgrade
        if new_parsed < old_parsed:
            issues.append(PackageDependencyIssue(
                package_name=pkg_name,
                issue_type='downgrade',
                message=f"Package downgraded: {old_version} -> {new_version}",
                severity='warning',
                current_version=old_version,
                recommended_version=old_version,
                affected_file=file_path
            ))
        
        return issues
    
    def _parse_version(self, version_spec: str) -> Optional[str]:
        import re
        clean = re.sub(r'^[\^~>=<]+', '', version_spec)
        clean = re.sub(r'[^0-9.].*$', '', clean)
        return clean if clean else None
    
    async def _get_internal_package_latest(self, pkg_name: str) -> Optional[str]:
        """Get latest version of internal @workiz package from GitHub Packages."""
        # First check database cache
        async with self.db.connection() as conn:
            row = await conn.fetchrow("""
                SELECT latest_version FROM internal_packages
                WHERE package_name = $1
            """, pkg_name)
            if row:
                return row['latest_version']
        
        # Query GitHub Packages API
        # Package name without scope: @workiz/config-loader -> config-loader
        package_short_name = pkg_name.replace('@workiz/', '')
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.github_packages_api}/{package_short_name}/versions"
                headers = {
                    "Authorization": f"Bearer {self.github_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        versions = await response.json()
                        if versions:
                            # Versions are returned newest first
                            return versions[0].get('name', '').lstrip('v')
        except Exception as e:
            pass
        
        return None
    
    async def _check_internal_package(
        self, 
        pkg_name: str, 
        version_spec: str,
        file_path: str
    ) -> Optional[PackageDependencyIssue]:
        """Check internal @workiz package for issues."""
        latest = await self._get_internal_package_latest(pkg_name)
        
        if not latest:
            return None
        
        current = self._parse_version(version_spec)
        
        if current and latest and version.parse(current) < version.parse(latest):
            return PackageDependencyIssue(
                package_name=pkg_name,
                issue_type='outdated_internal',
                message=f"Internal package '{pkg_name}' has newer version: {latest} (current: {current})",
                severity='info',
                current_version=version_spec,
                recommended_version=f"^{latest}",
                affected_file=file_path
            )
        
        return None


class InternalPackageRegistry:
    """Manage registry of internal @workiz packages from GitHub Packages."""
    
    def __init__(self, db, github_token: str):
        self.db = db
        self.github_token = github_token
        self.github_api = "https://api.github.com/orgs/Workiz/packages"
    
    async def sync_from_github_packages(self) -> Dict:
        """Sync internal packages from GitHub Packages registry."""
        synced = 0
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.github_api}?package_type=npm"
            headers = {
                "Authorization": f"Bearer {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    return {'error': f"Failed to fetch from GitHub: {response.status}"}
                
                packages = await response.json()
                
                for pkg in packages:
                    name = pkg.get('name')
                    
                    # Get latest version
                    version_url = f"{self.github_api}/npm/{name}/versions"
                    async with session.get(version_url, headers=headers) as ver_response:
                        if ver_response.status == 200:
                            versions = await ver_response.json()
                            latest_version = versions[0].get('name', '').lstrip('v') if versions else None
                            
                            if latest_version:
                                await self._register_package(
                                    f"@workiz/{name}",
                                    latest_version,
                                    pkg.get('html_url', '')
                                )
                                synced += 1
                
                return {'synced': synced, 'total_found': len(packages)}
    
    async def _register_package(self, name: str, version: str, url: str) -> None:
        """Register or update an internal package in the database."""
        async with self.db.connection() as conn:
            await conn.execute("""
                INSERT INTO internal_packages 
                (package_name, latest_version, repo_url)
                VALUES ($1, $2, $3)
                ON CONFLICT (package_name) DO UPDATE SET
                    latest_version = EXCLUDED.latest_version,
                    updated_at = CURRENT_TIMESTAMP
            """, name, version, url)
```

---

## 12. Admin UI

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Admin UI Architecture                              │
├─────────────────────────────────────────────────────────────────────────────┤
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                      React Admin Dashboard                           │   │
│   │  (Next.js / Vite + React + TailwindCSS + shadcn/ui)                 │   │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│   │  │Dashboard │ │  Repos   │ │  Rules   │ │ Analytics│ │ Settings │  │   │
│   │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│   │                                                                      │   │
│   │  ┌──────────────────────────────────────────────────────────────┐   │   │
│   │  │                   🤖 Knowledge Assistant                      │   │   │
│   │  │  "Ask anything about your codebase, PRs, tickets..."         │   │   │
│   │  └──────────────────────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    │ REST API                                │
│                                    ▼                                         │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                         Admin API (FastAPI)                          │   │
│   │  /api/admin/dashboard    /api/admin/repositories                     │   │
│   │  /api/admin/rules        /api/admin/analytics                        │   │
│   │  /api/admin/costs        /api/admin/settings                         │   │
│   │  /api/admin/ask          ← NEW: Knowledge Assistant                  │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Pages

1. **Dashboard**: System overview, recent activity, key metrics
2. **Repositories**: List, add, index repositories
3. **Custom Rules**: CRUD for review rules
4. **Analytics**: Review quality, auto-fix success, API costs
5. **RepoSwarm Status**: Architecture analysis status
6. **Settings**: Model configuration, thresholds, team management
7. **🤖 Knowledge Assistant**: Ask questions about your codebase (NEW!)

### Admin API Endpoints

```python
# pr_agent/servers/admin_api.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

admin_router = APIRouter(prefix="/api/admin", tags=["admin"])

@admin_router.get("/dashboard")
async def get_dashboard():
    return {
        "prs_reviewed_today": 45,
        "comments_made_today": 123,
        "auto_fixes_today": 8,
        "api_cost_today": 12.50,
        "api_cost_month": 142.50
    }

@admin_router.get("/repositories")
async def list_repositories(language: Optional[str] = None, page: int = 1):
    pass

@admin_router.post("/repositories/{repo_id}/index")
async def trigger_indexing(repo_id: int):
    pass

@admin_router.get("/rules")
async def list_rules():
    pass

@admin_router.post("/rules")
async def create_rule(rule: dict):
    pass

@admin_router.get("/analytics")
async def get_analytics(start_date: str, end_date: str):
    pass

@admin_router.get("/costs")
async def get_costs(period: str = "month"):
    pass
```

---

## 12.1 Knowledge Assistant

A ChatGPT-like interface that lets developers ask questions about the entire codebase using RAG.

### What Can You Ask?

| Category | Example Questions |
|----------|-------------------|
| **Architecture** | "How does the notification service communicate with the user service?" |
| **Code** | "Where is the payment processing logic?" |
| **APIs** | "What endpoints does the auth service expose?" |
| **PubSub** | "Which services subscribe to the USER_CREATED event?" |
| **Developers** | "Who worked on the checkout flow recently?" |
| **PRs** | "What PRs were merged to the payments service this month?" |
| **Commits** | "What changed in the auth service last week?" |
| **Jira** | "What bugs were reported for the mobile app?" |
| **Dependencies** | "Which services use @workiz/config-loader?" |
| **Reviews** | "What are the common issues found in code reviews?" |

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Knowledge Assistant Flow                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User Question                                                               │
│  "Which services call the users API?"                                        │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Question Classifier                               │    │
│  │  Determines which data sources to query:                            │    │
│  │  • code_chunks (RAG)                                                │    │
│  │  • repo_analysis_cache (RepoSwarm)                                  │    │
│  │  • jira_tickets                                                     │    │
│  │  • review_history                                                   │    │
│  │  • GitHub API (commits, PRs, contributors)                          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    Context Retrieval                                 │    │
│  │                                                                      │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │    │
│  │  │ Vector Search│  │ SQL Queries  │  │ GitHub API   │               │    │
│  │  │ (pgvector)   │  │ (metadata)   │  │ (real-time)  │               │    │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │    │
│  │         │                 │                 │                        │    │
│  │         └─────────────────┼─────────────────┘                        │    │
│  │                           ▼                                          │    │
│  │                    Combined Context                                  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│       │                                                                      │
│       ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         LLM (Gemini)                                 │    │
│  │  System: "You are a helpful assistant with access to Workiz         │    │
│  │          codebase knowledge. Answer based on the context below."    │    │
│  │                                                                      │    │
│  │  Context: [Retrieved chunks, analysis, tickets, commits...]         │    │
│  │                                                                      │    │
│  │  Question: "Which services call the users API?"                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│       │                                                                      │
│       ▼                                                                      │
│  Answer with sources:                                                        │
│  "Based on the RepoSwarm analysis, the following services call the          │
│   users API:                                                                 │
│   - notifications-service (GET /users/:id) - src/services/user.service.ts  │
│   - payments-service (GET /users/:id/billing) - src/api/users.ts           │
│   - auth-service (POST /users) - src/controllers/auth.controller.ts"       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Database Schema Addition

```sql
-- Conversation history for Knowledge Assistant
CREATE TABLE IF NOT EXISTS assistant_conversations (
    id SERIAL PRIMARY KEY,
    session_id UUID NOT NULL,
    user_id VARCHAR(255),
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    context_used JSONB,         -- Sources used for the answer
    tokens_used INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_assistant_conversations_session 
    ON assistant_conversations(session_id);

-- Track which commits/PRs we've indexed for contributor queries
CREATE TABLE IF NOT EXISTS github_activity (
    id SERIAL PRIMARY KEY,
    repository_id INT REFERENCES repositories(id),
    activity_type VARCHAR(50),  -- 'commit', 'pr', 'review'
    github_id VARCHAR(100),     -- SHA for commits, PR number for PRs
    author VARCHAR(255),
    title TEXT,
    description TEXT,
    files_changed JSONB,
    created_at TIMESTAMP,
    synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repository_id, activity_type, github_id)
);

CREATE INDEX idx_github_activity_author ON github_activity(author);
CREATE INDEX idx_github_activity_created ON github_activity(created_at);
```

### API Implementation

```python
# pr_agent/servers/admin_api.py

from pydantic import BaseModel
from typing import List, Optional
import uuid

class AskRequest(BaseModel):
    question: str
    session_id: Optional[str] = None
    include_sources: bool = True

class Source(BaseModel):
    type: str  # 'code', 'architecture', 'jira', 'commit', 'pr', 'review'
    title: str
    url: Optional[str]
    snippet: Optional[str]

class AskResponse(BaseModel):
    answer: str
    sources: List[Source]
    session_id: str


@admin_router.post("/ask", response_model=AskResponse)
async def ask_knowledge_assistant(request: AskRequest):
    """
    Ask questions about your codebase, PRs, tickets, commits, etc.
    Uses RAG to find relevant context and LLM to generate answer.
    """
    from pr_agent.tools.knowledge_assistant import KnowledgeAssistant
    
    session_id = request.session_id or str(uuid.uuid4())
    
    assistant = KnowledgeAssistant(
        db=get_db_connection(),
        ai_handler=get_ai_handler(),
        github_token=os.environ.get('GITHUB_USER_TOKEN')
    )
    
    result = await assistant.ask(
        question=request.question,
        session_id=session_id,
        include_sources=request.include_sources
    )
    
    return AskResponse(
        answer=result['answer'],
        sources=result['sources'],
        session_id=session_id
    )


@admin_router.get("/ask/history/{session_id}")
async def get_conversation_history(session_id: str):
    """Get conversation history for a session."""
    conn = get_db_connection()
    with conn.cursor() as cur:
        cur.execute("""
            SELECT role, content, context_used, created_at
            FROM assistant_conversations
            WHERE session_id = %s
            ORDER BY created_at ASC
        """, (session_id,))
        rows = cur.fetchall()
    
    return [
        {
            "role": row[0],
            "content": row[1],
            "sources": row[2],
            "timestamp": row[3]
        }
        for row in rows
    ]
```

### Knowledge Assistant Core

```python
# pr_agent/tools/knowledge_assistant.py

from typing import Dict, List, Optional
from dataclasses import dataclass
import json


@dataclass
class RetrievedContext:
    type: str
    content: str
    metadata: Dict
    relevance_score: float


class KnowledgeAssistant:
    """
    RAG-based assistant for answering questions about the codebase.
    Combines multiple data sources: code, architecture, Jira, GitHub activity.
    """
    
    def __init__(self, db, ai_handler, github_token: str):
        self.db = db
        self.ai_handler = ai_handler
        self.github_token = github_token
    
    async def ask(
        self, 
        question: str, 
        session_id: str,
        include_sources: bool = True
    ) -> Dict:
        """Answer a question using RAG."""
        
        # 1. Classify the question to determine which sources to query
        query_plan = await self._classify_question(question)
        
        # 2. Retrieve relevant context from each source
        contexts = await self._retrieve_context(question, query_plan)
        
        # 3. Build the prompt with context
        prompt = self._build_prompt(question, contexts)
        
        # 4. Get answer from LLM
        answer, tokens = await self.ai_handler.chat_completion(
            model=self.config.get("llm.model", "gemini-3-pro"),
            system=self._get_system_prompt(),
            user=prompt
        )
        
        # 5. Extract sources from contexts
        sources = self._format_sources(contexts) if include_sources else []
        
        # 6. Save to conversation history
        await self._save_conversation(session_id, question, answer, sources, tokens)
        
        return {
            'answer': answer,
            'sources': sources
        }
    
    async def _classify_question(self, question: str) -> Dict:
        """Determine which data sources to query based on the question."""
        
        # Use LLM to classify
        classification_prompt = f"""
        Classify this question about a codebase. Return JSON with boolean fields:
        - needs_code_search: true if question is about specific code/implementation
        - needs_architecture: true if question is about service structure/APIs/events
        - needs_jira: true if question is about tickets/bugs/features
        - needs_commits: true if question is about recent changes/who changed what
        - needs_prs: true if question is about pull requests/reviews
        - needs_contributors: true if question is about who works on what
        
        Question: {question}
        
        Return only valid JSON, no explanation.
        """
        
        response, _ = await self.ai_handler.chat_completion(
            model=self.config.get("llm.model", "gemini-3-pro"),
            system="You classify questions. Return only JSON.",
            user=classification_prompt
        )
        
        try:
            return json.loads(response)
        except:
            # Default to searching everything
            return {
                'needs_code_search': True,
                'needs_architecture': True,
                'needs_jira': False,
                'needs_commits': False,
                'needs_prs': False,
                'needs_contributors': False
            }
    
    async def _retrieve_context(
        self, 
        question: str, 
        query_plan: Dict
    ) -> List[RetrievedContext]:
        """Retrieve relevant context from multiple sources."""
        contexts = []
        
        # 1. Code chunks (vector search)
        if query_plan.get('needs_code_search'):
            code_contexts = await self._search_code_chunks(question)
            contexts.extend(code_contexts)
        
        # 2. RepoSwarm architecture analysis
        if query_plan.get('needs_architecture'):
            arch_contexts = await self._search_architecture(question)
            contexts.extend(arch_contexts)
        
        # 3. Jira tickets
        if query_plan.get('needs_jira'):
            jira_contexts = await self._search_jira(question)
            contexts.extend(jira_contexts)
        
        # 4. GitHub commits
        if query_plan.get('needs_commits'):
            commit_contexts = await self._search_commits(question)
            contexts.extend(commit_contexts)
        
        # 5. Pull requests
        if query_plan.get('needs_prs'):
            pr_contexts = await self._search_prs(question)
            contexts.extend(pr_contexts)
        
        # 6. Contributors
        if query_plan.get('needs_contributors'):
            contributor_contexts = await self._search_contributors(question)
            contexts.extend(contributor_contexts)
        
        # Sort by relevance and limit
        contexts.sort(key=lambda x: x.relevance_score, reverse=True)
        return contexts[:10]  # Top 10 most relevant
    
    async def _search_code_chunks(self, question: str) -> List[RetrievedContext]:
        """Vector search in code_chunks table."""
        # Generate embedding for question
        embedding = await self._get_embedding(question)
        
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT 
                    c.file_path,
                    c.chunk_content,
                    c.chunk_type,
                    r.repo_name,
                    1 - (c.embedding <=> %s::vector) as similarity
                FROM code_chunks c
                JOIN repositories r ON c.repository_id = r.id
                WHERE c.embedding IS NOT NULL
                ORDER BY c.embedding <=> %s::vector
                LIMIT 5
            """, (embedding, embedding))
            
            rows = cur.fetchall()
        
        return [
            RetrievedContext(
                type='code',
                content=row[1],
                metadata={
                    'file_path': row[0],
                    'chunk_type': row[2],
                    'repo': row[3]
                },
                relevance_score=row[4]
            )
            for row in rows
        ]
    
    async def _search_architecture(self, question: str) -> List[RetrievedContext]:
        """Search RepoSwarm analysis results."""
        # Simple text search in JSONB
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT 
                    repo_url,
                    repo_type,
                    analysis_result
                FROM repo_analysis_cache
                WHERE analysis_result::text ILIKE %s
                LIMIT 5
            """, (f'%{question.split()[0]}%',))  # Simple keyword match
            
            rows = cur.fetchall()
        
        contexts = []
        for row in rows:
            analysis = row[2] if isinstance(row[2], dict) else json.loads(row[2])
            for key, value in analysis.items():
                if isinstance(value, str) and len(value) > 50:
                    contexts.append(RetrievedContext(
                        type='architecture',
                        content=f"## {key}\n{value[:2000]}",
                        metadata={
                            'repo_url': row[0],
                            'repo_type': row[1],
                            'analysis_type': key
                        },
                        relevance_score=0.7
                    ))
        
        return contexts[:3]
    
    async def _search_jira(self, question: str) -> List[RetrievedContext]:
        """Search Jira tickets."""
        embedding = await self._get_embedding(question)
        
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT 
                    ticket_key,
                    summary,
                    description,
                    status,
                    issue_type,
                    1 - (embedding <=> %s::vector) as similarity
                FROM jira_tickets
                WHERE embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector
                LIMIT 5
            """, (embedding, embedding))
            
            rows = cur.fetchall()
        
        return [
            RetrievedContext(
                type='jira',
                content=f"[{row[0]}] {row[1]}\n{row[2][:500] if row[2] else ''}",
                metadata={
                    'ticket_key': row[0],
                    'status': row[3],
                    'type': row[4]
                },
                relevance_score=row[5]
            )
            for row in rows
        ]
    
    async def _search_commits(self, question: str) -> List[RetrievedContext]:
        """Search recent commits."""
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT 
                    g.author,
                    g.title,
                    g.description,
                    g.created_at,
                    r.repo_name,
                    g.files_changed
                FROM github_activity g
                JOIN repositories r ON g.repository_id = r.id
                WHERE g.activity_type = 'commit'
                AND (g.title ILIKE %s OR g.description ILIKE %s)
                ORDER BY g.created_at DESC
                LIMIT 5
            """, (f'%{question}%', f'%{question}%'))
            
            rows = cur.fetchall()
        
        return [
            RetrievedContext(
                type='commit',
                content=f"Commit by {row[0]} in {row[4]}: {row[1]}",
                metadata={
                    'author': row[0],
                    'repo': row[4],
                    'date': str(row[3]),
                    'files': row[5]
                },
                relevance_score=0.6
            )
            for row in rows
        ]
    
    async def _search_prs(self, question: str) -> List[RetrievedContext]:
        """Search pull requests."""
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT 
                    g.github_id,
                    g.author,
                    g.title,
                    g.description,
                    g.created_at,
                    r.repo_name
                FROM github_activity g
                JOIN repositories r ON g.repository_id = r.id
                WHERE g.activity_type = 'pr'
                AND (g.title ILIKE %s OR g.description ILIKE %s)
                ORDER BY g.created_at DESC
                LIMIT 5
            """, (f'%{question}%', f'%{question}%'))
            
            rows = cur.fetchall()
        
        return [
            RetrievedContext(
                type='pr',
                content=f"PR #{row[0]} by {row[1]} in {row[5]}: {row[2]}",
                metadata={
                    'pr_number': row[0],
                    'author': row[1],
                    'repo': row[5],
                    'date': str(row[4])
                },
                relevance_score=0.6
            )
            for row in rows
        ]
    
    async def _search_contributors(self, question: str) -> List[RetrievedContext]:
        """Search for contributor information."""
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT 
                    author,
                    r.repo_name,
                    COUNT(*) as activity_count,
                    MAX(g.created_at) as last_active
                FROM github_activity g
                JOIN repositories r ON g.repository_id = r.id
                WHERE g.author ILIKE %s
                GROUP BY author, r.repo_name
                ORDER BY activity_count DESC
                LIMIT 10
            """, (f'%{question}%',))
            
            rows = cur.fetchall()
        
        return [
            RetrievedContext(
                type='contributor',
                content=f"{row[0]} - {row[2]} activities in {row[1]}, last active: {row[3]}",
                metadata={
                    'author': row[0],
                    'repo': row[1],
                    'activity_count': row[2]
                },
                relevance_score=0.5
            )
            for row in rows
        ]
    
    def _get_system_prompt(self) -> str:
        return """You are a helpful assistant with deep knowledge of the Workiz codebase.
        
You have access to:
- Code from all repositories
- Architecture analysis (APIs, events, dependencies)
- Jira tickets (bugs, features, tasks)
- Recent commits and PRs
- Developer activity

When answering:
1. Be specific and cite sources (file paths, ticket numbers, PR numbers)
2. If you find relevant code, include snippets
3. If asked about who worked on something, mention the developer names
4. If you don't have enough information, say so
5. Format your answer with markdown for readability
"""
    
    def _build_prompt(self, question: str, contexts: List[RetrievedContext]) -> str:
        context_text = "\n\n---\n\n".join([
            f"**[{ctx.type.upper()}]** {ctx.metadata.get('repo', '')}\n{ctx.content}"
            for ctx in contexts
        ])
        
        return f"""Based on the following context from the codebase, answer the question.

## Context

{context_text}

## Question

{question}

## Answer
"""
    
    def _format_sources(self, contexts: List[RetrievedContext]) -> List[Dict]:
        sources = []
        for ctx in contexts:
            source = {
                'type': ctx.type,
                'title': '',
                'url': None,
                'snippet': ctx.content[:200] if ctx.content else None
            }
            
            if ctx.type == 'code':
                source['title'] = f"{ctx.metadata.get('repo')}/{ctx.metadata.get('file_path')}"
                source['url'] = f"https://github.com/Workiz/{ctx.metadata.get('repo')}/blob/main/{ctx.metadata.get('file_path')}"
            elif ctx.type == 'architecture':
                source['title'] = f"Architecture: {ctx.metadata.get('repo_type')}"
            elif ctx.type == 'jira':
                source['title'] = ctx.metadata.get('ticket_key')
                source['url'] = f"https://workiz.atlassian.net/browse/{ctx.metadata.get('ticket_key')}"
            elif ctx.type == 'pr':
                source['title'] = f"PR #{ctx.metadata.get('pr_number')} in {ctx.metadata.get('repo')}"
                source['url'] = f"https://github.com/Workiz/{ctx.metadata.get('repo')}/pull/{ctx.metadata.get('pr_number')}"
            elif ctx.type == 'commit':
                source['title'] = f"Commit in {ctx.metadata.get('repo')} by {ctx.metadata.get('author')}"
            elif ctx.type == 'contributor':
                source['title'] = ctx.metadata.get('author')
            
            sources.append(source)
        
        return sources
    
    async def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI."""
        import openai
        
        client = openai.OpenAI()
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    
    async def _save_conversation(
        self, 
        session_id: str, 
        question: str, 
        answer: str, 
        sources: List[Dict],
        tokens: int
    ):
        """Save conversation to history."""
        with self.db.cursor() as cur:
            # Save user question
            cur.execute("""
                INSERT INTO assistant_conversations 
                (session_id, role, content, tokens_used)
                VALUES (%s, 'user', %s, 0)
            """, (session_id, question))
            
            # Save assistant answer
            cur.execute("""
                INSERT INTO assistant_conversations 
                (session_id, role, content, context_used, tokens_used)
                VALUES (%s, 'assistant', %s, %s, %s)
            """, (session_id, answer, json.dumps(sources), tokens))
        
        self.db.commit()
```

### Frontend Component (React)

```tsx
// admin-ui/src/components/KnowledgeAssistant.tsx

import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, ExternalLink } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  sources?: Source[];
}

interface Source {
  type: string;
  title: string;
  url?: string;
  snippet?: string;
}

export function KnowledgeAssistant() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const question = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: question }]);
    setLoading(true);

    try {
      const response = await fetch('/api/admin/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          session_id: sessionId,
          include_sources: true
        })
      });

      const data = await response.json();
      setSessionId(data.session_id);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        sources: data.sources
      }]);
    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-200px)] bg-gray-900 rounded-lg">
      {/* Header */}
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-xl font-semibold flex items-center gap-2">
          <Bot className="w-6 h-6 text-blue-400" />
          Knowledge Assistant
        </h2>
        <p className="text-sm text-gray-400">
          Ask anything about code, PRs, tickets, commits, and more
        </p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-8">
            <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Ask me anything about your codebase!</p>
            <div className="mt-4 grid grid-cols-2 gap-2 max-w-md mx-auto text-sm">
              {[
                "How does auth work?",
                "Who worked on payments?",
                "Recent bugs in mobile app",
                "What APIs does users-service expose?"
              ].map((suggestion, i) => (
                <button
                  key={i}
                  onClick={() => setInput(suggestion)}
                  className="p-2 bg-gray-800 rounded hover:bg-gray-700 text-left"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}
          >
            {msg.role === 'assistant' && (
              <Bot className="w-8 h-8 text-blue-400 shrink-0" />
            )}
            <div
              className={`max-w-[80%] rounded-lg p-3 ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-100'
              }`}
            >
              <div className="prose prose-invert prose-sm">
                {msg.content}
              </div>
              
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-700">
                  <p className="text-xs text-gray-400 mb-2">Sources:</p>
                  <div className="space-y-1">
                    {msg.sources.map((source, j) => (
                      <a
                        key={j}
                        href={source.url || '#'}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-xs text-blue-400 hover:underline"
                      >
                        <span className="px-1 py-0.5 bg-gray-700 rounded text-[10px]">
                          {source.type}
                        </span>
                        {source.title}
                        {source.url && <ExternalLink className="w-3 h-3" />}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
            {msg.role === 'user' && (
              <User className="w-8 h-8 text-gray-400 shrink-0" />
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3">
            <Bot className="w-8 h-8 text-blue-400 shrink-0" />
            <div className="bg-gray-800 rounded-lg p-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100" />
                <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-700">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about code, PRs, tickets, commits..."
            className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-lg px-4 py-2"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </form>
    </div>
  );
}
```

---

## 13. Error Handling

### Rate Limiter

```python
# pr_agent/middleware/rate_limiter.py
import asyncio
import redis.asyncio as redis

class RateLimiter:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.limits = {
            'github': {'requests': 5000, 'window': 3600},
            'openai': {'requests': 500, 'window': 60},
            'anthropic': {'requests': 60, 'window': 60},
        }
    
    async def check_and_increment(self, provider: str) -> bool:
        from datetime import datetime
        key = f"ratelimit:{provider}:{datetime.now().strftime('%Y%m%d%H%M')}"
        limit = self.limits.get(provider, {'requests': 100, 'window': 60})
        
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, limit['window'])
        
        return current <= limit['requests']
```

### Circuit Breaker

```python
# pr_agent/middleware/circuit_breaker.py
from datetime import datetime, timedelta
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
    
    async def call(self, func, *args, **kwargs):
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker open")
        
        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        self.failures = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        self.failures += 1
        self.last_failure_time = datetime.now()
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
    
    def _should_attempt_reset(self) -> bool:
        if not self.last_failure_time:
            return True
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
```

---

## 14. Bugbot-Style Inline Review Comments

The Workiz PR Agent uses **individual inline review comments** (like Cursor Bugbot) for code findings and suggestions. Each finding appears as a separate comment directly on the affected code line.

### How It Works

| Command | Output |
|---------|--------|
| **`/review`** | AI review summary is **always published** + static analyzer findings as inline comments |
| **`/improve`** | AI suggestions are published as **individual inline comments** (not batched) |

### Key Design Decisions

| Aspect | Our Approach | Why |
|--------|--------------|-----|
| **AI Review** | Always published | PR description, type, and file walkthrough always visible |
| **Findings** | Individual inline comments | Visible in both "Conversation" AND "Files Changed" tabs |
| **Suggestions** | Individual inline comments | Each AI suggestion is a separate, actionable comment |
| **Blocking** | Non-blocking (`event: "COMMENT"`) | Informational, doesn't prevent merge |
| **Buttons** | Markdown links via HTTPS redirect | GitHub blocks `cursor://` URLs |

### Visual Reference (What We Implement)

```
┌────────────────────────────────────────────────────────────────────────────┐
│ 🤖 workiz-pr-agent [bot] reviewed just now         View reviewed changes   │
├────────────────────────────────────────────────────────────────────────────┤
│  src/services/user.service.ts                                              │
│       41 |   const users = [];                                             │
│       42 | + let result = await this.repo.find();                          │
│       43 |   return result;                                                │
├────────────────────────────────────────────────────────────────────────────┤
│ 🤖 workiz-pr-agent [bot] just now                                          │
│                                                                            │
│ **Use const instead of let**                                               │
│                                                                            │
│ **Medium Severity**                                                        │
│                                                                            │
│ The variable `result` is never reassigned. Per Workiz coding standards,    │
│ use `const` for variables that don't change. This improves code clarity    │
│ and prevents accidental reassignment.                                      │
│                                                                            │
│ **Suggested fix:** Change `let result` to `const result`                   │
│                                                                            │
│ [🔧 Fix in Cursor](https://...) | [↗ Fix in Web](https://vscode.dev/...)   │
│                                                                            │
│ 😊                                                                         │
│ ┌────────────────────────────────────────────────────────────────────────┐│
│ │ Reply...                                                               ││
│ └────────────────────────────────────────────────────────────────────────┘│
│ [Resolve conversation]                                                     │
└────────────────────────────────────────────────────────────────────────────┘
```

### GitHub Pull Request Review API

We use GitHub's **Pull Request Review API** to create inline comments:

```
POST /repos/{owner}/{repo}/pulls/{pull_number}/reviews
```

**Request body:**
```json
{
  "commit_id": "abc123def456...",
  "event": "COMMENT",
  "comments": [
    {
      "path": "src/services/user.service.ts",
      "line": 42,
      "body": "**Use const instead of let**\n\n**Medium Severity**\n\nThe variable `result` is never reassigned..."
    },
    {
      "path": "src/api/controller.ts", 
      "line": 15,
      "body": "**Business logic in controller**\n\n**High Severity**\n\nMove this logic to a service..."
    }
  ]
}
```

**Key Points:**
- `event: "COMMENT"` = **Non-blocking** (doesn't prevent merge)
- `event: "REQUEST_CHANGES"` = Blocking (we DON'T use this)
- Each comment appears inline on the specific code line
- Comments show in BOTH "Conversation" tab AND "Files Changed" tab

### Cursor Redirect Service

Since GitHub blocks `cursor://` URLs, we host an HTTPS redirect page that:
1. Opens the file at the correct line via `cursor://file/{path}:{line}:1`
2. Shows the prompt for copy/paste (user must manually paste into Cursor's AI chat)

**⚠️ Important Limitation:** Cursor's `cursor://agent/prompt?prompt=...` URL scheme **only works for Cursor's own Bugbot**. Third-party tools cannot pre-fill prompts via URL for security reasons. See: [Cursor Forum Discussion](https://forum.cursor.com/t/does-cursor-schema-support-prompts/133027)

**What works:**
- `cursor://file/{path}:{line}:{column}` - Opens file at specific location ✅
- `cursor://file/{path}` - Opens file ✅

**What doesn't work:**
- `cursor://agent/prompt?prompt=...` - Only works for Bugbot ❌

### Cursor Extension (Recommended)

Install the **Workiz PR Agent Cursor Extension** for the best experience:

- **With extension**: Clicking "Fix in Cursor" opens the file AND pre-fills the AI chat with the fix prompt!
- **Without extension**: Opens the file only; prompt shown on redirect page for copy/paste

See [`cursor-extension/README.md`](../cursor-extension/README.md) for installation instructions.

### Persistent Prompt Storage

Prompts are stored persistently in PostgreSQL (with in-memory fallback) to:
- Avoid URL length limits when passing prompts
- Enable analytics on "Fix in Cursor" usage
- Track click-through rates and access patterns

**Architecture:**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                          Fix in Cursor Flow                                   │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  1. PR Comment Created                                                        │
│     └─► cursor_redirect endpoint called                                       │
│          └─► save_prompt() stores in DB → returns UUID                        │
│               └─► Redirect URL: cursor://...?id={uuid}&baseUrl={server}       │
│                                                                               │
│  2. User Clicks "Fix in Cursor"                                               │
│     └─► Opens redirect page in browser                                        │
│          └─► Page triggers cursor:// deep link                                │
│               └─► Extension activates with id + baseUrl params                │
│                                                                               │
│  3. Extension Fetches Prompt                                                  │
│     └─► GET {baseUrl}/api/v1/prompt/{id}                                      │
│          └─► get_prompt() returns full prompt + updates access_count          │
│               └─► Opens file + Opens AI chat with pre-filled prompt           │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Database Module (`pr_agent/db/cursor_prompts.py`):**

```python
def save_prompt(
    prompt: str,
    file_path: str | None = None,
    line_number: int | None = None,
    repository: str | None = None,
    pr_number: int | None = None,
    pr_url: str | None = None,
    comment_type: str | None = None,  # 'static_analyzer', 'ai_suggestion'
    severity: str | None = None,
    finding_id: str | None = None,
) -> str | None:
    """Save prompt and return UUID. Returns None if DB unavailable (falls back to in-memory)."""

def get_prompt(prompt_id: str, accessed_by: str | None = None) -> dict | None:
    """Retrieve prompt by ID and update access tracking."""

def get_prompt_analytics(repository: str = None, start_date: datetime = None, end_date: datetime = None) -> dict:
    """Get analytics: total_prompts, accessed_prompts, click_through_rate, by_type, etc."""
```

**Redirect endpoint:** `GET /api/v1/cursor-redirect`

```python
# pr_agent/servers/github_app.py

@router.get("/api/v1/cursor-redirect", response_class=HTMLResponse)
async def cursor_redirect(
    request: Request,
    prompt: str = Query(...),
    file: Optional[str] = Query(None),
    line: Optional[int] = Query(None),
    repository: Optional[str] = Query(None),
    pr_number: Optional[int] = Query(None),
    pr_url: Optional[str] = Query(None),
    comment_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    finding_id: Optional[str] = Query(None),
):
    """
    Stores prompt in DB (with context for analytics) and redirects to Cursor.
    Falls back to in-memory storage if DB unavailable.
    """
    from pr_agent.db.cursor_prompts import save_prompt as db_save_prompt
    
    # Store in DB with full context
    prompt_id = db_save_prompt(
        prompt=prompt,
        file_path=file,
        line_number=line,
        repository=repository,
        pr_number=pr_number,
        pr_url=pr_url,
        comment_type=comment_type,
        severity=severity,
        finding_id=finding_id,
    )
    
    # Fallback to in-memory if DB unavailable
    if not prompt_id:
        prompt_id = str(uuid.uuid4())
        prompt_store[prompt_id] = {"prompt": prompt, "file": file, "line": line}
    
    base_url = str(request.base_url).rstrip('/')
    extension_url = f"cursor://workiz.workiz-pr-agent-fix/fix?id={prompt_id}&baseUrl={quote(base_url, safe='')}"
    
    # Returns HTML page that triggers cursor:// deep link
    return HTMLResponse(content=html_template)
```

**Prompt Retrieval Endpoint:** `GET /api/v1/prompt/{prompt_id}`

```python
@router.get("/api/v1/prompt/{prompt_id}")
async def get_prompt_endpoint(prompt_id: str, accessed_by: Optional[str] = Query(None)):
    """
    Retrieve stored prompt by ID. Updates access tracking in DB.
    Falls back to in-memory storage if not found in DB.
    """
    from pr_agent.db.cursor_prompts import get_prompt as db_get_prompt
    
    prompt_data = db_get_prompt(prompt_id, accessed_by=accessed_by)
    
    if not prompt_data:
        # Fallback to in-memory
        prompt_data = prompt_store.get(prompt_id)
        if not prompt_data:
            raise HTTPException(status_code=404, detail="Prompt not found or expired")
    
    return {"prompt": prompt_data["prompt"], "file": prompt_data.get("file"), "line": prompt_data.get("line")}
```

### Comment Formatter

```python
# pr_agent/tools/inline_comment_formatter.py

from urllib.parse import quote
from typing import Optional

def format_inline_comment(
    title: str,
    severity: str,
    description: str,
    file_path: str,
    line: int,
    suggestion: str = "",
    org: str = "",
    repo: str = "",
    branch: str = "main",
    cursor_redirect_base: str = "",
) -> str:
    """
    Format a single inline review comment in Bugbot style.
    
    Args:
        title: Issue title (e.g., "Use const instead of let")
        severity: "High", "Medium", or "Low"
        description: Detailed explanation
        file_path: Path to file
        line: Line number
        suggestion: Suggested fix (optional)
        org: GitHub org name
        repo: Repository name
        branch: Branch name
        cursor_redirect_base: Base URL for cursor redirect service
    
    Returns:
        Formatted markdown comment body
    """
    body = f"**{title}**\n\n"
    body += f"**{severity} Severity**\n\n"
    body += f"{description}\n"
    
    if suggestion:
        body += f"\n**Suggested fix:** {suggestion}\n"
    
    # Build fix button URLs
    prompt = _build_cursor_prompt(title, file_path, line, description, suggestion)
    
    if cursor_redirect_base:
        cursor_url = f"{cursor_redirect_base}?prompt={quote(prompt)}&file={quote(file_path)}&line={line}"
        body += f"\n[🔧 Fix in Cursor]({cursor_url})"
    
    if org and repo:
        vscode_url = f"https://vscode.dev/github/{org}/{repo}/blob/{branch}/{file_path}#L{line}"
        body += f" | [↗ Fix in Web]({vscode_url})"
    
    return body


def _build_cursor_prompt(
    title: str,
    file_path: str,
    line: int,
    description: str,
    suggestion: str
) -> str:
    """Build the prompt text for Cursor AI."""
    prompt = f"""Fix the following code review issue:

## Issue: {title}

**File:** {file_path}
**Line:** {line}

**Problem:** {description}
"""
    if suggestion:
        prompt += f"\n**Suggested Fix:** {suggestion}\n"
    
    prompt += """
## Instructions:
1. First verify this issue exists at the specified location
2. Apply the suggested fix or an appropriate solution
3. Ensure the fix follows project coding standards
4. Check that the fix doesn't break existing functionality
"""
    return prompt
```

### Configuration

Add to `configuration.toml`:

```toml
[workiz.inline_comments]
# Enable inline comments (in addition to standard AI review)
# - /review: AI review summary always published + static analyzer findings as inline comments
# - /improve: AI suggestions published as individual inline comments
enabled = true

# Maximum comments per review (to avoid spam)
max_comments = 20

# Minimum severity to show ("high", "medium", "low")
severity_threshold = "low"

# Base URL for cursor redirect service
cursor_redirect_url = "https://pr-agent.workiz.com/api/v1/cursor-redirect"

# Show Fix in Web button (vscode.dev)
show_web_fallback = true
```

### GithubProvider Integration

```python
# pr_agent/git_providers/github_provider.py

def create_review_with_inline_comments(
    self,
    comments: list[dict],
    event: str = "COMMENT"
) -> dict:
    """
    Create a PR review with individual inline comments.
    
    Each comment appears:
    - Inline on the code in "Files Changed" tab
    - In the "Conversation" tab
    
    Args:
        comments: List of {path, line, body} dicts
        event: "COMMENT" (non-blocking) or "REQUEST_CHANGES" (blocking)
    
    Returns:
        API response dict
    """
    payload = {
        "commit_id": self.last_commit_id.sha,
        "event": event,  # "COMMENT" = non-blocking!
        "comments": [
            {
                "path": c["path"],
                "line": c["line"],
                "body": c["body"]
            }
            for c in comments
        ]
    }
    
    headers, data = self.pr._requester.requestJsonAndCheck(
        "POST",
        f"{self.pr.url}/reviews",
        input=payload
    )
    return data
```

### WorkizPRReviewer Integration

```python
# pr_agent/tools/workiz_pr_reviewer.py

async def _publish_inline_comments(self, findings: list[dict]) -> None:
    """
    Publish each finding as an individual inline comment.
    
    Called in addition to the standard AI review (which is always published).
    """
    if not findings:
        return
    
    # Sort by severity (high first) and limit
    sorted_findings = sorted(
        findings,
        key=lambda f: {"high": 0, "medium": 1, "low": 2}.get(f.get("severity", "").lower(), 3)
    )
    max_comments = get_settings().workiz.inline_comments.max_comments
    limited_findings = sorted_findings[:max_comments]
    
    # Format each as inline comment
    comments = []
    for finding in limited_findings:
        body = format_inline_comment(
            title=finding["title"],
            severity=finding["severity"],
            description=finding["message"],
            file_path=finding["file"],
            line=finding["line"],
            suggestion=finding.get("suggestion", ""),
            org=self.git_provider.repo.split("/")[0],
            repo=self.git_provider.repo.split("/")[1],
            cursor_redirect_base=get_settings().workiz.inline_comments.cursor_redirect_url,
        )
        comments.append({
            "path": finding["file"],
            "line": finding["line"],
            "body": body
        })
    
    # Create non-blocking review with inline comments
    self.git_provider.create_review_with_inline_comments(
        comments=comments,
        event="COMMENT"  # Non-blocking!
    )
    
    get_logger().info(f"Published {len(comments)} inline review comments", {
        "pr_url": self.pr_url,
        "comment_count": len(comments),
        "total_findings": len(findings),
    })
```

### User Experience Flow

```
1. Developer creates PR
                │
                ▼
2. PR Agent reviews (triggered by webhook)
   - Generates and PUBLISHES AI review summary (PR type, description, walkthrough)
   - Runs static analyzers (language analyzers, custom rules)
   - Generates AI suggestions (if /improve runs)
                │
                ▼
3. AI review summary published
   - PR description, type, file walkthrough
   - Always visible as a regular GitHub comment
                │
                ▼
4. Individual inline comments created
   - Static analyzer findings → inline comments on code lines
   - AI suggestions → inline comments on code lines (from /improve)
   - Visible in "Files Changed" AND "Conversation" tabs
   - Non-blocking (doesn't prevent merge)
                │
                ▼
5. Developer sees inline comment on their code:
   ┌─────────────────────────────────────────────────┐
   │ 🤖 workiz-pr-agent [bot]                        │
   │                                                  │
   │ **Use const instead of let**                    │
   │ **Medium Severity**                              │
   │                                                  │
   │ The variable is never reassigned...             │
   │                                                  │
   │ [🔧 Fix in Cursor] | [↗ Fix in Web]            │
   └─────────────────────────────────────────────────┘
                │
                ▼
6. Developer clicks "Fix in Cursor"
   - Browser opens redirect page
   - Redirect page tries cursor:// deep link
   - Cursor opens with pre-filled prompt
   - (Fallback: copy prompt manually)
                │
                ▼
7. Developer applies fix in Cursor
   - AI assistant fixes the code
   - Commit and push
   - Resolve conversation on GitHub
```

### Important Notes

1. **Non-Blocking**: We use `event: "COMMENT"` which is purely informational and doesn't block merge
2. **GitHub Limits**: Max ~60 comments per review; we limit to 20 by default
3. **Redirect Required**: GitHub blocks `cursor://` URLs, so we use HTTPS redirect page
4. **Both Tabs**: Inline comments appear in BOTH "Conversation" AND "Files Changed" tabs

### Smart Line Adjustment

**Problem:** AI suggestions often target "context lines" (unchanged lines shown around changes in the diff). GitHub's API only allows inline comments on lines that are actually in the diff hunks.

**Solution:** Smart line adjustment validates and adjusts comment line numbers:

```python
def _adjust_suggestion_to_diff(self, suggestion: dict, hunk_ranges: dict) -> dict:
    """
    Adjust suggestion line to valid diff line.
    
    - Inside hunk: Use as-is
    - Within PROXIMITY_THRESHOLD (10) lines: Adjust to nearest hunk boundary
    - Far from any hunk: Mark as skip_inline=True
    """
    file_ranges = hunk_ranges.get(suggestion['file'], [])
    suggested_line = suggestion.get('line', 1)
    
    # Check if inside any hunk
    for hunk in file_ranges:
        if hunk['start'] <= suggested_line <= hunk['end']:
            return suggestion  # Valid, use as-is
    
    # Try to adjust to nearest hunk
    PROXIMITY_THRESHOLD = 10
    for hunk in file_ranges:
        if abs(suggested_line - hunk['start']) <= PROXIMITY_THRESHOLD:
            return {**suggestion, 'line': hunk['start'], 'adjusted': True}
        if abs(suggested_line - hunk['end']) <= PROXIMITY_THRESHOLD:
            return {**suggestion, 'line': hunk['end'], 'adjusted': True}
    
    # Too far from any hunk
    return {**suggestion, 'skip_inline': True}
```

**Logging:** The system logs adjustment statistics:
```
Published 12 inline comments (5 adjusted to hunk boundary, 3 skipped - not in diff)
```

### Comment Format (Future Unification)

Currently, static analyzer findings and AI suggestions use different comment formats:

| Component | Static Analyzer (`format_inline_comment`) | AI Suggestion (`format_suggestion_comment`) |
|-----------|-------------------------------------------|---------------------------------------------|
| Title | `**[RULE_ID] Title**` | `**Summary**` |
| Classification | `**High Severity**` | `*Label* (e.g., "Enhancement")` |
| Code Diff | None | Collapsible code comparison |
| Structure | Title → Severity → Description | Title → Label → Description → Code Diff |

**Planned:** Unify both formats to use identical structure and severity classification:
- Map AI labels to severity levels (e.g., "performance" → Medium, "security" → High)
- Single unified formatter function
- Consistent filtering and tooling based on severity

---

## Next Steps

See [Deployment & Implementation](./DEPLOYMENT_AND_IMPLEMENTATION.md) for:
- Local development setup
- Production deployment guide
- Data initialization
- Implementation checklists
- Testing strategy


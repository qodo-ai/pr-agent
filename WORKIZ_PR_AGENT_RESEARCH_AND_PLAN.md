# Workiz PR Agent - Comprehensive Research and Implementation Plan

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Current Architecture Analysis](#current-architecture-analysis)
3. [Requirements Overview](#requirements-overview)
4. [Component Deep Dive](#component-deep-dive)
5. [Implementation Plan](#implementation-plan)
6. [Database Architecture](#database-architecture)
7. [Multi-Agent Architecture](#multi-agent-architecture)
8. [Local Development Setup](#local-development-setup)
9. [Configuration Guide](#configuration-guide)
10. [Detailed Component Implementation](#detailed-component-implementation)
11. [Deployment Strategy](#deployment-strategy)
12. [Timeline and Milestones](#timeline-and-milestones)

---

## Executive Summary

This document outlines a comprehensive plan to transform the qodo-ai/pr-agent fork into a customized, hosted PR review solution for Workiz. The enhanced agent will include:

- **Cross-Repository Context (RAG)**: Find related code across all Workiz repositories
- **Jira Integration**: Compare code against tickets and historical bug fixes
- **Extended Review Comments**: Display more than 2-3 comments per review
- **Custom Styling Rules**: Enforce functional programming, NestJS patterns, etc.
- **SQL Review**: Deep SQL query analysis
- **Security Checks**: Standard and custom security validations
- **Multi-Agent Architecture**: Parallel processing with orchestration

---

## Current Architecture Analysis

### Core Components

```
pr_agent/
├── agent/
│   └── pr_agent.py              # Main agent orchestration
├── algo/
│   ├── ai_handlers/             # LLM integrations
│   │   ├── base_ai_handler.py   # Abstract base class
│   │   ├── litellm_ai_handler.py # Primary handler (LiteLLM)
│   │   ├── langchain_ai_handler.py # LangChain support
│   │   └── openai_ai_handler.py # Direct OpenAI
│   ├── pr_processing.py         # Diff processing
│   ├── token_handler.py         # Token management
│   └── utils.py                 # Utility functions
├── git_providers/
│   ├── github_provider.py       # GitHub API integration
│   └── ...                      # Other providers
├── servers/
│   ├── github_app.py            # FastAPI webhook server
│   └── ...                      # Other server implementations
├── settings/
│   ├── configuration.toml       # Main configuration
│   ├── pr_reviewer_prompts.toml # Review prompts
│   └── ...                      # Other prompt files
└── tools/
    ├── pr_reviewer.py           # Review tool
    ├── pr_code_suggestions.py   # Improve tool
    ├── pr_similar_issue.py      # RAG-based similar issues
    └── ...                      # Other tools
```

### Request Flow

1. **Webhook Reception** (`github_app.py`):
   - GitHub sends webhook to `/api/v1/github_webhooks`
   - Request is validated and parsed
   - Background task created for async processing

2. **Command Routing** (`pr_agent.py`):
   - `command2class` maps commands to tool classes
   - `PRAgent.handle_request()` routes to appropriate tool
   - Supports: `review`, `improve`, `describe`, `ask`, etc.

3. **Review Execution** (`pr_reviewer.py`):
   - `PRReviewer.__init__()`: Initializes with PR URL, loads git provider
   - `run()`: Main execution method
   - `_prepare_prediction()`: Generates diff, calls AI
   - `_get_prediction()`: Sends prompts to LLM via AI handler
   - `_prepare_pr_review()`: Formats AI response to markdown

4. **AI Handler** (`litellm_ai_handler.py`):
   - `chat_completion()`: Async method for LLM calls
   - Supports multiple providers via LiteLLM
   - Handles retries, fallback models, streaming

### Existing RAG Implementation

The `pr_similar_issue.py` demonstrates existing RAG capability:

```python
# Supports three vector DBs:
vectordb = "pinecone"  # or "lancedb", "qdrant"

# Embeddings via OpenAI
MODEL = "text-embedding-ada-002"

# Data structures
class Metadata(BaseModel):
    repo: str
    username: str
    created_at: str
    level: IssueLevel  # ISSUE or COMMENT

class Record(BaseModel):
    id: str
    text: str
    metadata: Metadata
```

### Ticket Integration

Current implementation in `ticket_pr_compliance_check.py`:

```python
# Extracts GitHub issues from PR description
GITHUB_TICKET_PATTERN = re.compile(
    r'(https://github[^/]+/[^/]+/[^/]+/issues/\d+)|...'
)

# Also supports Jira ticket patterns
patterns = [
    r'\b[A-Z]{2,10}-\d{1,7}\b',  # Standard JIRA format
    r'(?:https?://[^\s/]+/browse/)?([A-Z]{2,10}-\d{1,7})\b'
]
```

### Configuration System

Uses **Dynaconf** with TOML files:

```python
# config_loader.py
global_settings = Dynaconf(
    envvar_prefix=False,
    settings_files=[...],  # Multiple TOML files
    merge_enabled=True     # Merge configurations
)
```

Settings hierarchy:
1. Default settings (`configuration.toml`)
2. Repo-specific (`.pr_agent.toml` in repo)
3. Environment variables
4. Secrets (`.secrets.toml`)

---

## Requirements Overview

### Requirement 1: Cross-Repository Context (RAG)

**Goal**: When reviewing a PR in service A, find related code in services B, C, D that call or are called by the changed code.

**Use Cases**:
- Notification service PR → Find all HTTP/PubSub callers
- API endpoint change → Find all frontend consumers
- Shared library change → Find all dependent services

### Requirement 2: Jira Integration

**Goal**: Connect to Jira to compare PR against ticket requirements and historical fixes.

**Use Cases**:
- Compare implementation against acceptance criteria
- Check if similar bugs were fixed before
- Pull context from related tickets

### Requirement 3: Extended Comments

**Goal**: Display more than the current 2-3 comments limit per review.

**Current Limitation**:
```toml
# configuration.toml
num_max_findings = 3
```

### Requirement 4: Custom Styling Rules

**Goal**: Add Workiz-specific code style checks:
- Functional programming patterns
- Small functions
- NestJS patterns
- No inline comments
- Structured logging

### Requirement 5: SQL Review

**Goal**: Deep analysis of SQL queries for:
- Performance issues
- Security vulnerabilities
- Schema compatibility
- Query optimization

### Requirement 6: Security Checks

**Goal**: Enhanced security analysis:
- Standard OWASP checks
- Workiz-specific security patterns
- API key/secret detection
- Authorization checks

---

## Component Deep Dive

### AI Handler Architecture

```python
# base_ai_handler.py
class BaseAiHandler(ABC):
    @abstractmethod
    async def chat_completion(
        self, 
        model: str, 
        system: str, 
        user: str, 
        temperature: float = 0.2,
        img_path: str = None
    ):
        pass
```

**Extension Point**: Create custom handlers for specialized tasks.

### Prompt System

Prompts are Jinja2 templates in TOML format:

```toml
# pr_reviewer_prompts.toml
[pr_review_prompt]
system="""You are PR-Reviewer...
{%- if extra_instructions %}
Extra instructions:
{{ extra_instructions }}
{%- endif %}
"""

user="""
--PR Info--
Title: '{{title}}'
Branch: '{{branch}}'
The PR code diff:
{{ diff|trim }}
"""
```

**Variables Available**:
- `title`, `branch`, `description`
- `diff`, `language`
- `extra_instructions`
- `related_tickets`
- `commit_messages_str`

### Git Provider Interface

```python
# git_provider.py
class GitProvider:
    def get_diff_files(self) -> list[FilePatchInfo]
    def get_pr_description(self, ...)
    def publish_comment(self, pr_comment: str, ...)
    def publish_inline_comments(self, comments: list[dict], ...)
    def get_repo_settings(self)
    # ... many more methods
```

### Token Management

```python
# token_handler.py
class TokenHandler:
    def count_tokens(self, text: str) -> int
    # Uses tiktoken for accurate counting
```

---

## Implementation Plan

### Phase 1: Foundation (Week 1-2)

#### 1.1 PostgreSQL Database Setup

Create new module: `pr_agent/db/`

```python
# pr_agent/db/__init__.py
# pr_agent/db/models.py
# pr_agent/db/repositories.py
# pr_agent/db/embeddings.py
```

**Database Schema**:

```sql
-- Repositories and their metadata
CREATE TABLE repositories (
    id SERIAL PRIMARY KEY,
    org_name VARCHAR(255) NOT NULL,
    repo_name VARCHAR(255) NOT NULL,
    github_url TEXT,
    last_indexed_at TIMESTAMP,
    settings JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_name, repo_name)
);

-- Code chunks for RAG
CREATE TABLE code_chunks (
    id SERIAL PRIMARY KEY,
    repository_id INT REFERENCES repositories(id),
    file_path TEXT NOT NULL,
    chunk_content TEXT NOT NULL,
    chunk_type VARCHAR(50), -- 'function', 'class', 'endpoint', 'pubsub'
    start_line INT,
    end_line INT,
    embedding vector(1536), -- pgvector
    metadata JSONB,
    last_updated TIMESTAMP,
    commit_sha VARCHAR(40),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Jira tickets cache
CREATE TABLE jira_tickets (
    id SERIAL PRIMARY KEY,
    ticket_key VARCHAR(50) UNIQUE NOT NULL, -- e.g., 'WORK-1234'
    title TEXT,
    description TEXT,
    status VARCHAR(50),
    ticket_type VARCHAR(50),
    acceptance_criteria TEXT,
    labels TEXT[],
    embedding vector(1536),
    raw_data JSONB,
    last_synced TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Review history for learning
CREATE TABLE review_history (
    id SERIAL PRIMARY KEY,
    pr_url TEXT NOT NULL,
    repository_id INT REFERENCES repositories(id),
    review_type VARCHAR(50), -- 'full', 'incremental'
    suggestions JSONB,
    accepted_suggestions JSONB,
    review_context JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Custom rules configuration
CREATE TABLE custom_rules (
    id SERIAL PRIMARY KEY,
    repository_id INT REFERENCES repositories(id),
    rule_type VARCHAR(50), -- 'style', 'security', 'sql'
    rule_name VARCHAR(255),
    rule_content TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;
CREATE INDEX ON code_chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX ON jira_tickets USING ivfflat (embedding vector_cosine_ops);
```

#### 1.2 Configuration Extensions

Update `configuration.toml`:

```toml
[workiz]
# Database configuration
database_url = ""  # PostgreSQL connection string
enable_cross_repo_context = true
enable_jira_integration = true
enable_custom_rules = true
enable_sql_review = true
enable_enhanced_security = true

# RAG settings
rag_similarity_threshold = 0.75
rag_max_chunks = 10
rag_embedding_model = "text-embedding-ada-002"

# Review settings
max_review_comments = 10
enable_inline_suggestions = true

[jira]
base_url = ""  # https://workiz.atlassian.net
api_token = ""
email = ""
project_keys = []  # List of Jira project keys to index

[custom_rules]
# Workiz-specific rules
enable_functional_style = true
enable_nestjs_patterns = true
enable_small_functions = true
max_function_lines = 50
enable_structured_logging = true
```

### Phase 2: Cross-Repository Context (Week 2-4)

#### 2.1 Repository Indexer

Create: `pr_agent/tools/repo_indexer.py`

```python
from typing import List, Dict, Optional
from dataclasses import dataclass
import ast
import re

@dataclass
class CodeChunk:
    file_path: str
    content: str
    chunk_type: str  # 'function', 'class', 'endpoint', 'pubsub_handler'
    start_line: int
    end_line: int
    metadata: Dict

class RepositoryIndexer:
    """Index code repositories for RAG-based context retrieval."""
    
    def __init__(self, db_connection, embedding_handler):
        self.db = db_connection
        self.embedder = embedding_handler
    
    async def index_repository(self, repo_url: str, github_token: str) -> None:
        """Clone and index an entire repository."""
        # Clone repo
        # Parse all files
        # Extract chunks
        # Generate embeddings
        # Store in PostgreSQL
        pass
    
    def extract_chunks(self, file_content: str, file_path: str) -> List[CodeChunk]:
        """Extract meaningful code chunks from file."""
        chunks = []
        
        # Extract HTTP endpoints (NestJS)
        chunks.extend(self._extract_nestjs_endpoints(file_content, file_path))
        
        # Extract PubSub handlers
        chunks.extend(self._extract_pubsub_handlers(file_content, file_path))
        
        # Extract functions/methods
        chunks.extend(self._extract_functions(file_content, file_path))
        
        # Extract interfaces/types
        chunks.extend(self._extract_interfaces(file_content, file_path))
        
        return chunks
    
    def _extract_nestjs_endpoints(self, content: str, path: str) -> List[CodeChunk]:
        """Extract NestJS controller endpoints."""
        patterns = [
            r'@(Get|Post|Put|Delete|Patch)\([\'"]([^\'"]*)[\'"]?\)',
            r'@Controller\([\'"]([^\'"]*)[\'"]?\)',
        ]
        # Implementation
        pass
    
    def _extract_pubsub_handlers(self, content: str, path: str) -> List[CodeChunk]:
        """Extract PubSub event handlers."""
        patterns = [
            r'@PubSubTopic\([\'"]([^\'"]*)[\'"]',
            r'@PubSubEvent\([\'"]([^\'"]*)[\'"]',
            r'@OnEvent\([\'"]([^\'"]*)[\'"]',
        ]
        # Implementation
        pass
```

#### 2.2 Context Retriever

Create: `pr_agent/tools/context_retriever.py`

```python
class CrossRepoContextRetriever:
    """Retrieve relevant context from other repositories."""
    
    def __init__(self, db_connection, embedding_handler):
        self.db = db_connection
        self.embedder = embedding_handler
    
    async def find_related_code(
        self, 
        changed_files: List[FilePatchInfo],
        current_repo: str
    ) -> List[Dict]:
        """Find related code across all indexed repositories."""
        related_chunks = []
        
        for file in changed_files:
            # Analyze what the file does
            analysis = self._analyze_file(file)
            
            # Find HTTP callers if this is an endpoint
            if analysis.get('endpoints'):
                callers = await self._find_endpoint_callers(analysis['endpoints'])
                related_chunks.extend(callers)
            
            # Find PubSub publishers if this is a handler
            if analysis.get('pubsub_handlers'):
                publishers = await self._find_pubsub_publishers(analysis['pubsub_handlers'])
                related_chunks.extend(publishers)
            
            # Find semantic similar code
            similar = await self._find_similar_code(file.patch, current_repo)
            related_chunks.extend(similar)
        
        return self._deduplicate_and_rank(related_chunks)
    
    async def _find_endpoint_callers(self, endpoints: List[str]) -> List[Dict]:
        """Find code that calls these endpoints."""
        query = """
            SELECT cc.*, r.repo_name 
            FROM code_chunks cc
            JOIN repositories r ON cc.repository_id = r.id
            WHERE cc.chunk_type = 'http_call'
            AND cc.metadata->>'endpoint' = ANY(%s)
        """
        # Implementation
        pass
    
    async def _find_pubsub_publishers(self, topics: List[str]) -> List[Dict]:
        """Find code that publishes to these topics."""
        query = """
            SELECT cc.*, r.repo_name 
            FROM code_chunks cc
            JOIN repositories r ON cc.repository_id = r.id
            WHERE cc.chunk_type = 'pubsub_publisher'
            AND cc.metadata->>'topic' = ANY(%s)
        """
        # Implementation
        pass
    
    async def _find_similar_code(
        self, 
        code: str, 
        exclude_repo: str,
        limit: int = 5
    ) -> List[Dict]:
        """Find semantically similar code using embeddings."""
        embedding = await self.embedder.create_embedding(code)
        
        query = """
            SELECT cc.*, r.repo_name,
                   1 - (cc.embedding <=> %s) as similarity
            FROM code_chunks cc
            JOIN repositories r ON cc.repository_id = r.id
            WHERE r.repo_name != %s
            ORDER BY cc.embedding <=> %s
            LIMIT %s
        """
        # Implementation using pgvector
        pass
```

### Phase 3: Jira Integration (Week 4-5)

#### 3.1 Jira Client

Create: `pr_agent/integrations/jira_client.py`

```python
from jira import JIRA
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class JiraTicket:
    key: str
    title: str
    description: str
    status: str
    ticket_type: str
    acceptance_criteria: str
    labels: List[str]
    linked_issues: List[str]
    comments: List[Dict]

class JiraClient:
    """Jira API client for ticket retrieval and analysis."""
    
    def __init__(self, base_url: str, email: str, api_token: str):
        self.jira = JIRA(
            server=base_url,
            basic_auth=(email, api_token)
        )
    
    def get_ticket(self, ticket_key: str) -> JiraTicket:
        """Retrieve full ticket information."""
        issue = self.jira.issue(ticket_key, expand='changelog')
        return JiraTicket(
            key=issue.key,
            title=issue.fields.summary,
            description=issue.fields.description or "",
            status=issue.fields.status.name,
            ticket_type=issue.fields.issuetype.name,
            acceptance_criteria=self._extract_acceptance_criteria(issue),
            labels=[label for label in issue.fields.labels],
            linked_issues=self._get_linked_issues(issue),
            comments=self._get_comments(issue)
        )
    
    def search_related_tickets(self, query: str) -> List[JiraTicket]:
        """Search for related tickets using JQL."""
        jql = f'text ~ "{query}" ORDER BY created DESC'
        issues = self.jira.search_issues(jql, maxResults=10)
        return [self.get_ticket(i.key) for i in issues]
    
    def get_ticket_history(self, ticket_key: str) -> List[Dict]:
        """Get complete history of a ticket including all changes."""
        issue = self.jira.issue(ticket_key, expand='changelog')
        history = []
        for history_item in issue.changelog.histories:
            for item in history_item.items:
                history.append({
                    'date': history_item.created,
                    'author': history_item.author.displayName,
                    'field': item.field,
                    'from': item.fromString,
                    'to': item.toString
                })
        return history
    
    def _extract_acceptance_criteria(self, issue) -> str:
        """Extract acceptance criteria from custom fields."""
        # Check common custom field names
        for field_name in ['customfield_10001', 'acceptance_criteria', 'Definition of Done']:
            if hasattr(issue.fields, field_name):
                return getattr(issue.fields, field_name) or ""
        return ""
```

#### 3.2 Jira Context Provider

Create: `pr_agent/tools/jira_context_provider.py`

```python
class JiraContextProvider:
    """Provide Jira context for PR reviews."""
    
    def __init__(self, jira_client: JiraClient, db_connection, embedder):
        self.jira = jira_client
        self.db = db_connection
        self.embedder = embedder
    
    async def get_pr_ticket_context(
        self, 
        pr_description: str,
        pr_title: str
    ) -> Dict:
        """Extract and enrich ticket context from PR."""
        context = {
            'tickets': [],
            'related_bugs': [],
            'historical_fixes': []
        }
        
        # Extract ticket keys from PR
        ticket_keys = self._extract_ticket_keys(pr_description + " " + pr_title)
        
        for key in ticket_keys:
            ticket = self.jira.get_ticket(key)
            context['tickets'].append({
                'key': ticket.key,
                'title': ticket.title,
                'description': ticket.description,
                'acceptance_criteria': ticket.acceptance_criteria,
                'status': ticket.status,
                'type': ticket.ticket_type
            })
            
            # Find similar past bugs
            if ticket.ticket_type == 'Bug':
                similar_bugs = await self._find_similar_bugs(ticket)
                context['related_bugs'].extend(similar_bugs)
            
            # Find historical fixes for this area
            historical = await self._find_historical_fixes(ticket)
            context['historical_fixes'].extend(historical)
        
        return context
    
    async def _find_similar_bugs(self, ticket: JiraTicket) -> List[Dict]:
        """Find similar bugs that were fixed in the past."""
        # Create embedding from ticket description
        embedding = await self.embedder.create_embedding(
            f"{ticket.title} {ticket.description}"
        )
        
        # Search in cached Jira tickets
        query = """
            SELECT * FROM jira_tickets
            WHERE ticket_type = 'Bug'
            AND status = 'Done'
            AND ticket_key != %s
            ORDER BY embedding <=> %s
            LIMIT 5
        """
        # Implementation
        pass
    
    async def _find_historical_fixes(self, ticket: JiraTicket) -> List[Dict]:
        """Find PRs that fixed similar issues."""
        query = """
            SELECT rh.*, jt.ticket_key, jt.title as ticket_title
            FROM review_history rh
            JOIN jira_tickets jt ON rh.review_context->>'ticket_key' = jt.ticket_key
            WHERE jt.ticket_type = 'Bug'
            ORDER BY jt.embedding <=> %s
            LIMIT 5
        """
        # Implementation
        pass
    
    def _extract_ticket_keys(self, text: str) -> List[str]:
        """Extract Jira ticket keys from text."""
        pattern = r'\b[A-Z]{2,10}-\d{1,7}\b'
        return list(set(re.findall(pattern, text)))
```

### Phase 4: Custom Review Rules (Week 5-6)

#### 4.1 Custom Rules Engine

Create: `pr_agent/tools/custom_rules_engine.py`

```python
from abc import ABC, abstractmethod
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class RuleViolation:
    rule_name: str
    file_path: str
    line_number: int
    message: str
    severity: str  # 'error', 'warning', 'info'
    suggestion: str

class BaseRule(ABC):
    """Base class for custom code review rules."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @abstractmethod
    def check(self, file_content: str, file_path: str) -> List[RuleViolation]:
        pass

class FunctionalStyleRule(BaseRule):
    """Enforce functional programming style."""
    
    @property
    def name(self) -> str:
        return "functional-style"
    
    @property
    def description(self) -> str:
        return "Enforce functional programming patterns"
    
    def check(self, file_content: str, file_path: str) -> List[RuleViolation]:
        violations = []
        lines = file_content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Check for 'let' usage (should use 'const')
            if re.search(r'\blet\s+\w+\s*=', line):
                violations.append(RuleViolation(
                    rule_name=self.name,
                    file_path=file_path,
                    line_number=i,
                    message="Use 'const' instead of 'let' for immutability",
                    severity='warning',
                    suggestion=line.replace('let ', 'const ')
                ))
            
            # Check for imperative loops
            if re.search(r'\bfor\s*\(', line) or re.search(r'\bwhile\s*\(', line):
                violations.append(RuleViolation(
                    rule_name=self.name,
                    file_path=file_path,
                    line_number=i,
                    message="Consider using array methods (map, filter, reduce) instead of loops",
                    severity='info',
                    suggestion=""
                ))
            
            # Check for direct mutation
            if re.search(r'\.push\(|\.splice\(|\.shift\(|\.unshift\(', line):
                violations.append(RuleViolation(
                    rule_name=self.name,
                    file_path=file_path,
                    line_number=i,
                    message="Avoid mutating arrays directly, use spread operator or concat",
                    severity='warning',
                    suggestion=""
                ))
        
        return violations

class SmallFunctionsRule(BaseRule):
    """Enforce small function size."""
    
    def __init__(self, max_lines: int = 50):
        self.max_lines = max_lines
    
    @property
    def name(self) -> str:
        return "small-functions"
    
    @property
    def description(self) -> str:
        return f"Functions should be less than {self.max_lines} lines"
    
    def check(self, file_content: str, file_path: str) -> List[RuleViolation]:
        violations = []
        # Parse TypeScript/JavaScript functions and check their length
        # Implementation using AST or regex
        pass

class StructuredLoggingRule(BaseRule):
    """Enforce structured logging with context objects."""
    
    @property
    def name(self) -> str:
        return "structured-logging"
    
    @property
    def description(self) -> str:
        return "Logger calls must include context objects"
    
    def check(self, file_content: str, file_path: str) -> List[RuleViolation]:
        violations = []
        lines = file_content.split('\n')
        
        # Pattern for logger calls without context
        bad_patterns = [
            r'this\.logger\.(log|warn|error|debug)\s*\(\s*[\'"`][^,]+\s*\)',
            r'this\.logger\.(log|warn|error|debug)\s*\(\s*`[^`]+`\s*\)',
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in bad_patterns:
                if re.search(pattern, line):
                    violations.append(RuleViolation(
                        rule_name=self.name,
                        file_path=file_path,
                        line_number=i,
                        message="Logger calls must include a context object as second parameter",
                        severity='warning',
                        suggestion="Add context: this.logger.log('message', { contextData })"
                    ))
        
        return violations

class NestJSPatternsRule(BaseRule):
    """Enforce NestJS best practices."""
    
    @property
    def name(self) -> str:
        return "nestjs-patterns"
    
    @property
    def description(self) -> str:
        return "Enforce NestJS architectural patterns"
    
    def check(self, file_content: str, file_path: str) -> List[RuleViolation]:
        violations = []
        
        # Check for business logic in controllers
        if '.controller.ts' in file_path:
            # Look for complex logic that should be in services
            if re.search(r'(if|for|while|switch)\s*\(', file_content):
                violations.append(RuleViolation(
                    rule_name=self.name,
                    file_path=file_path,
                    line_number=0,
                    message="Controllers should be thin - move business logic to services",
                    severity='warning',
                    suggestion=""
                ))
        
        return violations

class CustomRulesEngine:
    """Engine to run custom code review rules."""
    
    def __init__(self, rules: List[BaseRule] = None):
        self.rules = rules or self._default_rules()
    
    def _default_rules(self) -> List[BaseRule]:
        return [
            FunctionalStyleRule(),
            SmallFunctionsRule(),
            StructuredLoggingRule(),
            NestJSPatternsRule(),
        ]
    
    def analyze(
        self, 
        files: List[FilePatchInfo]
    ) -> Dict[str, List[RuleViolation]]:
        """Analyze files against all rules."""
        results = {}
        
        for file in files:
            if not file.head_file:
                continue
            
            file_violations = []
            for rule in self.rules:
                violations = rule.check(file.head_file, file.filename)
                file_violations.extend(violations)
            
            if file_violations:
                results[file.filename] = file_violations
        
        return results
```

#### 4.2 Cursor Rules Loader

Create: `pr_agent/tools/cursor_rules_loader.py`

```python
import os
import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
from pr_agent.log import get_logger

@dataclass
class CursorRule:
    """A rule extracted from cursor rules files."""
    source_file: str
    category: str
    rule_text: str
    applies_to: List[str]  # glob patterns

class CursorRulesLoader:
    """Load and parse cursor rules from .cursor directories in repositories."""
    
    RULES_PATTERNS = [
        '.cursor/rules.mdc',
        '.cursor/rules/*.mdc',
        '.cursorrules',
    ]
    
    def __init__(self):
        self._cache: Dict[str, List[CursorRule]] = {}
    
    async def load_rules_from_repo(self, repo_path: str) -> List[CursorRule]:
        """Load all cursor rules from a repository."""
        if repo_path in self._cache:
            return self._cache[repo_path]
        
        rules = []
        
        # Check for .cursor/rules.mdc
        rules_mdc = Path(repo_path) / '.cursor' / 'rules.mdc'
        if rules_mdc.exists():
            rules.extend(self._parse_mdc_file(str(rules_mdc)))
        
        # Check for .cursor/rules/*.mdc
        rules_dir = Path(repo_path) / '.cursor' / 'rules'
        if rules_dir.exists():
            for mdc_file in rules_dir.glob('*.mdc'):
                rules.extend(self._parse_mdc_file(str(mdc_file)))
        
        # Check for .cursorrules (legacy format)
        cursorrules = Path(repo_path) / '.cursorrules'
        if cursorrules.exists():
            rules.extend(self._parse_cursorrules_file(str(cursorrules)))
        
        self._cache[repo_path] = rules
        return rules
    
    def _parse_mdc_file(self, file_path: str) -> List[CursorRule]:
        """Parse a .mdc file and extract rules."""
        rules = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse frontmatter
            frontmatter = {}
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    frontmatter = self._parse_frontmatter(parts[1])
                    content = parts[2]
            
            # Extract glob patterns
            globs = frontmatter.get('globs', ['**/*'])
            if isinstance(globs, str):
                globs = [globs]
            
            # Parse sections
            sections = self._extract_sections(content)
            
            for section_name, section_content in sections.items():
                # Extract individual rules from section
                extracted_rules = self._extract_rules_from_section(section_content)
                
                for rule_text in extracted_rules:
                    rules.append(CursorRule(
                        source_file=file_path,
                        category=section_name,
                        rule_text=rule_text,
                        applies_to=globs
                    ))
        
        except Exception as e:
            get_logger().warning(f"Failed to parse cursor rules file {file_path}: {e}")
        
        return rules
    
    def _parse_frontmatter(self, frontmatter_text: str) -> Dict:
        """Parse YAML-like frontmatter."""
        result = {}
        for line in frontmatter_text.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Handle arrays
                if value.startswith('[') and value.endswith(']'):
                    value = [v.strip().strip('"').strip("'") 
                             for v in value[1:-1].split(',')]
                elif value.startswith('-'):
                    # Multi-line array
                    continue
                
                result[key] = value
        
        return result
    
    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract sections from markdown content."""
        sections = {}
        current_section = "general"
        current_content = []
        
        for line in content.split('\n'):
            if line.startswith('## '):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = line[3:].strip().lower().replace(' ', '_')
                current_content = []
            else:
                current_content.append(line)
        
        if current_content:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _extract_rules_from_section(self, section_content: str) -> List[str]:
        """Extract individual rules from a section."""
        rules = []
        
        # Split by bullet points or numbered lists
        lines = section_content.split('\n')
        current_rule = []
        
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('- ') or stripped.startswith('* ') or re.match(r'^\d+\.', stripped):
                if current_rule:
                    rules.append(' '.join(current_rule))
                current_rule = [stripped.lstrip('- *0123456789.').strip()]
            elif stripped and current_rule:
                current_rule.append(stripped)
        
        if current_rule:
            rules.append(' '.join(current_rule))
        
        return [r for r in rules if r]
    
    def _parse_cursorrules_file(self, file_path: str) -> List[CursorRule]:
        """Parse legacy .cursorrules file."""
        rules = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Treat entire file as rules
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    rules.append(CursorRule(
                        source_file=file_path,
                        category='general',
                        rule_text=line,
                        applies_to=['**/*']
                    ))
        
        except Exception as e:
            get_logger().warning(f"Failed to parse cursorrules file {file_path}: {e}")
        
        return rules
    
    def rules_to_prompt_context(self, rules: List[CursorRule]) -> str:
        """Convert cursor rules to prompt context for AI review."""
        if not rules:
            return ""
        
        context = "\n\n## Team Coding Standards (from .cursor rules)\n\n"
        
        # Group by category
        by_category: Dict[str, List[str]] = {}
        for rule in rules:
            if rule.category not in by_category:
                by_category[rule.category] = []
            by_category[rule.category].append(rule.rule_text)
        
        for category, rule_texts in by_category.items():
            context += f"### {category.replace('_', ' ').title()}\n"
            for rule_text in rule_texts:
                context += f"- {rule_text}\n"
            context += "\n"
        
        return context
```

#### 4.3 Integration with PR Review

Update: `pr_agent/tools/pr_reviewer.py`

```python
# Add to PRReviewer class

async def _load_cursor_rules(self) -> str:
    """Load cursor rules from the repository being reviewed."""
    from pr_agent.tools.cursor_rules_loader import CursorRulesLoader
    
    loader = CursorRulesLoader()
    
    # Get repository path or clone URL
    repo_url = self.git_provider.get_repo_url()
    
    # For local repos, load directly
    # For remote repos, the rules should be indexed in DB
    rules = await self._get_indexed_cursor_rules(repo_url)
    
    if rules:
        return loader.rules_to_prompt_context(rules)
    
    return ""

async def _get_indexed_cursor_rules(self, repo_url: str) -> List[Dict]:
    """Get cursor rules from database for a repository."""
    async with self.db.connection() as conn:
        rows = await conn.fetch("""
            SELECT category, rule_text, applies_to
            FROM cursor_rules
            WHERE repository_id = (
                SELECT id FROM repositories WHERE github_url = $1
            )
        """, repo_url)
    
    return [dict(r) for r in rows]
```

#### 4.4 Rules Loader (TOML + Database)

Create: `pr_agent/tools/custom_rules_loader.py`

```python
import re
import toml
from typing import List, Dict, Optional
from dataclasses import dataclass
from pr_agent.config_loader import get_settings
from pr_agent.db.connection import DatabaseManager
from pr_agent.log import get_logger

@dataclass
class RulePattern:
    """Rule pattern loaded from config or database."""
    name: str
    category: str
    language: Optional[str]
    framework: Optional[str]
    pattern: str
    message: str
    severity: str
    suggestion: str
    enabled: bool = True

class CustomRulesLoader:
    """Load custom rules from TOML config and database."""
    
    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db
        self._rules_cache: Dict[str, List[RulePattern]] = {}
    
    async def load_all_rules(self) -> Dict[str, List[RulePattern]]:
        """Load rules from both TOML and database."""
        rules = {}
        
        # Load from TOML config
        toml_rules = self._load_from_toml()
        for category, patterns in toml_rules.items():
            rules[category] = patterns
        
        # Load from database (can override TOML)
        if self.db:
            db_rules = await self._load_from_database()
            for category, patterns in db_rules.items():
                if category in rules:
                    # Merge, db rules can override toml
                    existing_names = {r.name for r in rules[category]}
                    for pattern in patterns:
                        if pattern.name in existing_names:
                            # Replace
                            rules[category] = [
                                p if p.name != pattern.name else pattern 
                                for p in rules[category]
                            ]
                        else:
                            rules[category].append(pattern)
                else:
                    rules[category] = patterns
        
        self._rules_cache = rules
        return rules
    
    def _load_from_toml(self) -> Dict[str, List[RulePattern]]:
        """Load rules from workiz_rules.toml."""
        rules = {}
        
        try:
            settings_path = 'pr_agent/settings/workiz_rules.toml'
            with open(settings_path, 'r') as f:
                config = toml.load(f)
            
            workiz_rules = config.get('workiz_rules', {})
            
            for category, category_config in workiz_rules.items():
                if category == 'functional':
                    # Special handling for functional rules
                    continue
                
                patterns = category_config.get('patterns', [])
                rules[category] = [
                    RulePattern(
                        name=p['name'],
                        category=category,
                        language=category if category in ['php', 'javascript', 'typescript'] else None,
                        framework=p.get('framework') or (category if category in ['nestjs', 'react'] else None),
                        pattern=p['pattern'],
                        message=p['message'],
                        severity=p.get('severity', 'warning'),
                        suggestion=p.get('suggestion', ''),
                        enabled=p.get('enabled', True)
                    )
                    for p in patterns
                ]
        
        except FileNotFoundError:
            get_logger().warning("workiz_rules.toml not found, using defaults")
        except Exception as e:
            get_logger().error(f"Error loading rules from TOML: {e}")
        
        return rules
    
    async def _load_from_database(self) -> Dict[str, List[RulePattern]]:
        """Load rules from database."""
        rules = {}
        
        try:
            async with self.db.connection() as conn:
                rows = await conn.fetch("""
                    SELECT rule_name, category, language, framework, 
                           pattern, message, severity, suggestion, enabled
                    FROM custom_rules
                    WHERE enabled = TRUE
                """)
                
                for row in rows:
                    category = row['category']
                    if category not in rules:
                        rules[category] = []
                    
                    rules[category].append(RulePattern(
                        name=row['rule_name'],
                        category=category,
                        language=row['language'],
                        framework=row['framework'],
                        pattern=row['pattern'],
                        message=row['message'],
                        severity=row['severity'],
                        suggestion=row['suggestion'],
                        enabled=row['enabled']
                    ))
        
        except Exception as e:
            get_logger().error(f"Error loading rules from database: {e}")
        
        return rules
    
    def get_rules_for_file(self, file_path: str) -> List[RulePattern]:
        """Get applicable rules for a specific file."""
        applicable_rules = []
        
        # Determine file type
        ext = file_path.split('.')[-1].lower()
        is_controller = '.controller.' in file_path
        is_service = '.service.' in file_path
        is_component = '.tsx' in file_path or '.jsx' in file_path
        
        # Map extension to language
        lang_map = {
            'php': 'php',
            'js': 'javascript',
            'mjs': 'javascript',
            'ts': 'typescript',
            'tsx': 'typescript',
            'jsx': 'javascript'
        }
        file_language = lang_map.get(ext)
        
        # Determine framework
        file_framework = None
        if is_controller or is_service:
            file_framework = 'nestjs'
        elif is_component:
            file_framework = 'react'
        
        # Collect applicable rules
        for category, patterns in self._rules_cache.items():
            for rule in patterns:
                if not rule.enabled:
                    continue
                
                # Check language match
                if rule.language and rule.language != file_language:
                    continue
                
                # Check framework match
                if rule.framework and rule.framework != file_framework:
                    continue
                
                # Security and database rules apply to all
                if category in ['security', 'database']:
                    applicable_rules.append(rule)
                    continue
                
                # Language-specific rules
                if rule.language == file_language:
                    applicable_rules.append(rule)
                
                # Framework-specific rules
                if rule.framework == file_framework:
                    applicable_rules.append(rule)
        
        return applicable_rules


class DynamicRuleChecker:
    """Check files against dynamically loaded rules."""
    
    def __init__(self, rules_loader: CustomRulesLoader):
        self.loader = rules_loader
    
    def check_file(self, content: str, file_path: str) -> List[Dict]:
        """Check file content against applicable rules."""
        violations = []
        rules = self.loader.get_rules_for_file(file_path)
        
        lines = content.split('\n')
        
        for rule in rules:
            try:
                pattern = re.compile(rule.pattern, re.IGNORECASE | re.MULTILINE)
                
                for i, line in enumerate(lines, 1):
                    if pattern.search(line):
                        violations.append({
                            'rule': rule.name,
                            'category': rule.category,
                            'file': file_path,
                            'line': i,
                            'message': rule.message,
                            'severity': rule.severity,
                            'suggestion': rule.suggestion,
                            'matched_line': line.strip()
                        })
            except re.error as e:
                get_logger().warning(f"Invalid regex in rule {rule.name}: {e}")
        
        return violations
    
    def check_all_files(self, files: List[Dict]) -> Dict[str, List[Dict]]:
        """Check multiple files and return violations by file."""
        results = {}
        
        for file_info in files:
            file_path = file_info.get('filename') or file_info.get('path')
            content = file_info.get('content') or file_info.get('head_file', '')
            
            if not content:
                continue
            
            violations = self.check_file(content, file_path)
            if violations:
                results[file_path] = violations
        
        return results
```

### Phase 5: SQL Review (Week 6-7)

#### 5.1 SQL Analyzer

Create: `pr_agent/tools/sql_analyzer.py`

```python
import re
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class SQLIssue:
    query: str
    issue_type: str
    message: str
    severity: str
    line_number: int
    suggestion: str

class SQLAnalyzer:
    """Analyze SQL queries for issues and improvements."""
    
    def __init__(self):
        self.patterns = self._load_patterns()
    
    def analyze_file(self, content: str, file_path: str) -> List[SQLIssue]:
        """Extract and analyze SQL queries from code."""
        issues = []
        
        # Extract SQL queries
        queries = self._extract_queries(content)
        
        for query_info in queries:
            query = query_info['query']
            line = query_info['line']
            
            # Check for common issues
            issues.extend(self._check_performance(query, line))
            issues.extend(self._check_security(query, line))
            issues.extend(self._check_best_practices(query, line))
        
        return issues
    
    def _extract_queries(self, content: str) -> List[Dict]:
        """Extract SQL queries from TypeScript/JavaScript code."""
        queries = []
        
        # Common patterns for SQL in code
        patterns = [
            r'`([^`]*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)[^`]*)`',
            r'"([^"]*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)[^"]*)"',
            r"'([^']*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER|DROP)[^']*)'",
            r'query\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
            r'execute\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE | re.DOTALL):
                # Find line number
                line_num = content[:match.start()].count('\n') + 1
                queries.append({
                    'query': match.group(1),
                    'line': line_num
                })
        
        return queries
    
    def _check_performance(self, query: str, line: int) -> List[SQLIssue]:
        """Check for performance issues."""
        issues = []
        query_upper = query.upper()
        
        # SELECT * check
        if 'SELECT *' in query_upper:
            issues.append(SQLIssue(
                query=query,
                issue_type='performance',
                message="Avoid SELECT * - specify needed columns explicitly",
                severity='warning',
                line_number=line,
                suggestion="Replace SELECT * with specific column names"
            ))
        
        # Missing index hints (for complex joins)
        if query_upper.count('JOIN') > 2 and 'INDEX' not in query_upper:
            issues.append(SQLIssue(
                query=query,
                issue_type='performance',
                message="Complex join detected - consider adding index hints",
                severity='info',
                line_number=line,
                suggestion="Review execution plan and add appropriate indexes"
            ))
        
        # LIKE with leading wildcard
        if re.search(r"LIKE\s+['\"]%", query_upper):
            issues.append(SQLIssue(
                query=query,
                issue_type='performance',
                message="LIKE with leading wildcard prevents index usage",
                severity='warning',
                line_number=line,
                suggestion="Consider full-text search or reorganize query"
            ))
        
        # Subquery in WHERE clause
        if 'WHERE' in query_upper and 'SELECT' in query_upper.split('WHERE')[-1]:
            issues.append(SQLIssue(
                query=query,
                issue_type='performance',
                message="Subquery in WHERE clause may be slow",
                severity='info',
                line_number=line,
                suggestion="Consider using JOIN instead of subquery"
            ))
        
        return issues
    
    def _check_security(self, query: str, line: int) -> List[SQLIssue]:
        """Check for security vulnerabilities."""
        issues = []
        
        # String concatenation (potential SQL injection)
        if re.search(r'\$\{|\+\s*[\'"]|\'\s*\+', query):
            issues.append(SQLIssue(
                query=query,
                issue_type='security',
                message="Potential SQL injection - use parameterized queries",
                severity='error',
                line_number=line,
                suggestion="Use prepared statements with parameterized values"
            ))
        
        # DROP/TRUNCATE without WHERE (dangerous)
        if ('DROP' in query.upper() or 'TRUNCATE' in query.upper()):
            issues.append(SQLIssue(
                query=query,
                issue_type='security',
                message="Destructive operation detected - ensure proper authorization",
                severity='error',
                line_number=line,
                suggestion="Add confirmation and audit logging"
            ))
        
        return issues
    
    def _check_best_practices(self, query: str, line: int) -> List[SQLIssue]:
        """Check for SQL best practices."""
        issues = []
        query_upper = query.upper()
        
        # Missing explicit columns in INSERT
        if 'INSERT INTO' in query_upper and '(' not in query_upper.split('VALUES')[0]:
            issues.append(SQLIssue(
                query=query,
                issue_type='best_practice',
                message="Specify column names explicitly in INSERT statements",
                severity='warning',
                line_number=line,
                suggestion="INSERT INTO table (col1, col2) VALUES (...)"
            ))
        
        # Implicit JOIN syntax
        if 'FROM' in query_upper and ',' in query_upper and 'JOIN' not in query_upper:
            issues.append(SQLIssue(
                query=query,
                issue_type='best_practice',
                message="Use explicit JOIN syntax instead of implicit joins",
                severity='info',
                line_number=line,
                suggestion="Use JOIN ... ON instead of WHERE clause joins"
            ))
        
        return issues
```

### Phase 6: Enhanced Security (Week 7-8)

#### 6.1 Security Scanner

Create: `pr_agent/tools/security_scanner.py`

```python
from typing import List, Dict
from dataclasses import dataclass
import re

@dataclass
class SecurityFinding:
    finding_type: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    file_path: str
    line_number: int
    message: str
    cwe_id: str  # Common Weakness Enumeration
    recommendation: str

class SecurityScanner:
    """Enhanced security scanner for code review."""
    
    def __init__(self):
        self.patterns = self._load_security_patterns()
    
    def scan_files(self, files: List[FilePatchInfo]) -> List[SecurityFinding]:
        """Scan files for security vulnerabilities."""
        findings = []
        
        for file in files:
            if not file.head_file:
                continue
            
            content = file.head_file
            path = file.filename
            
            # Standard security checks
            findings.extend(self._check_secrets(content, path))
            findings.extend(self._check_injection(content, path))
            findings.extend(self._check_auth(content, path))
            findings.extend(self._check_crypto(content, path))
            
            # Workiz-specific checks
            findings.extend(self._check_api_security(content, path))
            findings.extend(self._check_data_exposure(content, path))
        
        return findings
    
    def _check_secrets(self, content: str, path: str) -> List[SecurityFinding]:
        """Detect hardcoded secrets."""
        findings = []
        lines = content.split('\n')
        
        secret_patterns = [
            (r'(?i)(api[_-]?key|apikey)\s*[=:]\s*[\'"][^\'"]+[\'"]', 'API Key'),
            (r'(?i)(password|passwd|pwd)\s*[=:]\s*[\'"][^\'"]+[\'"]', 'Password'),
            (r'(?i)(secret|token)\s*[=:]\s*[\'"][^\'"]+[\'"]', 'Secret/Token'),
            (r'(?i)(aws_access_key_id)\s*[=:]\s*[\'"][^\'"]+[\'"]', 'AWS Key'),
            (r'-----BEGIN (RSA |DSA |EC )?PRIVATE KEY-----', 'Private Key'),
            (r'(?i)(bearer|authorization)\s*[=:]\s*[\'"][^\'"]+[\'"]', 'Auth Header'),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, secret_type in secret_patterns:
                if re.search(pattern, line):
                    findings.append(SecurityFinding(
                        finding_type='hardcoded_secret',
                        severity='critical',
                        file_path=path,
                        line_number=i,
                        message=f"Potential hardcoded {secret_type} detected",
                        cwe_id='CWE-798',
                        recommendation="Use environment variables or secret manager"
                    ))
        
        return findings
    
    def _check_injection(self, content: str, path: str) -> List[SecurityFinding]:
        """Detect injection vulnerabilities."""
        findings = []
        lines = content.split('\n')
        
        # SQL Injection
        sql_patterns = [
            r'query\s*\(\s*`[^`]*\$\{',
            r'execute\s*\(\s*`[^`]*\$\{',
            r'raw\s*\(\s*`[^`]*\$\{',
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in sql_patterns:
                if re.search(pattern, line):
                    findings.append(SecurityFinding(
                        finding_type='sql_injection',
                        severity='critical',
                        file_path=path,
                        line_number=i,
                        message="Potential SQL injection via string interpolation",
                        cwe_id='CWE-89',
                        recommendation="Use parameterized queries"
                    ))
        
        # Command Injection
        cmd_patterns = [
            r'exec\s*\(\s*`[^`]*\$\{',
            r'spawn\s*\(\s*`[^`]*\$\{',
            r'execSync\s*\(\s*`[^`]*\$\{',
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern in cmd_patterns:
                if re.search(pattern, line):
                    findings.append(SecurityFinding(
                        finding_type='command_injection',
                        severity='critical',
                        file_path=path,
                        line_number=i,
                        message="Potential command injection",
                        cwe_id='CWE-78',
                        recommendation="Validate and sanitize all inputs"
                    ))
        
        return findings
    
    def _check_auth(self, content: str, path: str) -> List[SecurityFinding]:
        """Check authorization patterns."""
        findings = []
        
        # Missing auth decorator on controller
        if '.controller.ts' in path:
            if '@Controller' in content and '@UseGuards' not in content:
                findings.append(SecurityFinding(
                    finding_type='missing_auth',
                    severity='high',
                    file_path=path,
                    line_number=0,
                    message="Controller missing authentication guard",
                    cwe_id='CWE-306',
                    recommendation="Add @UseGuards(AuthGuard) decorator"
                ))
        
        return findings
    
    def _check_api_security(self, content: str, path: str) -> List[SecurityFinding]:
        """Workiz-specific API security checks."""
        findings = []
        lines = content.split('\n')
        
        # Check for missing rate limiting
        if '@Controller' in content and '@Throttle' not in content:
            findings.append(SecurityFinding(
                finding_type='missing_rate_limit',
                severity='medium',
                file_path=path,
                line_number=0,
                message="API endpoint missing rate limiting",
                cwe_id='CWE-770',
                recommendation="Add @Throttle decorator for rate limiting"
            ))
        
        # Check for missing input validation
        for i, line in enumerate(lines, 1):
            if '@Body()' in line and '@IsNotEmpty' not in content and 'ValidationPipe' not in content:
                findings.append(SecurityFinding(
                    finding_type='missing_validation',
                    severity='medium',
                    file_path=path,
                    line_number=i,
                    message="Request body missing validation",
                    cwe_id='CWE-20',
                    recommendation="Add DTO validation with class-validator"
                ))
        
        return findings
    
    def _check_data_exposure(self, content: str, path: str) -> List[SecurityFinding]:
        """Check for sensitive data exposure."""
        findings = []
        lines = content.split('\n')
        
        # Sensitive fields in responses
        sensitive_fields = [
            'password', 'ssn', 'creditCard', 'credit_card',
            'bankAccount', 'bank_account', 'socialSecurity'
        ]
        
        for i, line in enumerate(lines, 1):
            if 'return' in line or 'response' in line.lower():
                for field in sensitive_fields:
                    if field.lower() in line.lower():
                        findings.append(SecurityFinding(
                            finding_type='data_exposure',
                            severity='high',
                            file_path=path,
                            line_number=i,
                            message=f"Potential exposure of sensitive field: {field}",
                            cwe_id='CWE-200',
                            recommendation="Remove or mask sensitive data in responses"
                        ))
        
        return findings
```

### Phase 7: Extended PRReviewer (Week 8-9)

#### 7.1 Enhanced PR Reviewer

Modify: `pr_agent/tools/pr_reviewer.py` (create extended version)

Create: `pr_agent/tools/workiz_pr_reviewer.py`

```python
from pr_agent.tools.pr_reviewer import PRReviewer
from pr_agent.tools.context_retriever import CrossRepoContextRetriever
from pr_agent.tools.jira_context_provider import JiraContextProvider
from pr_agent.tools.custom_rules_engine import CustomRulesEngine
from pr_agent.tools.sql_analyzer import SQLAnalyzer
from pr_agent.tools.security_scanner import SecurityScanner
from pr_agent.config_loader import get_settings

class WorkizPRReviewer(PRReviewer):
    """Enhanced PR Reviewer with Workiz-specific features."""
    
    def __init__(self, pr_url: str, *args, **kwargs):
        super().__init__(pr_url, *args, **kwargs)
        
        # Initialize additional components
        self.context_retriever = CrossRepoContextRetriever(
            db_connection=self._get_db_connection(),
            embedding_handler=self.ai_handler
        )
        self.jira_provider = JiraContextProvider(
            jira_client=self._get_jira_client(),
            db_connection=self._get_db_connection(),
            embedder=self.ai_handler
        )
        self.custom_rules = CustomRulesEngine()
        self.sql_analyzer = SQLAnalyzer()
        self.security_scanner = SecurityScanner()
    
    async def run(self) -> None:
        """Extended run method with additional analysis."""
        try:
            if not self.git_provider.get_files():
                return None
            
            # Get diff files
            diff_files = self.git_provider.get_diff_files()
            
            # Phase 1: Cross-repository context
            cross_repo_context = {}
            if get_settings().workiz.enable_cross_repo_context:
                cross_repo_context = await self.context_retriever.find_related_code(
                    diff_files, 
                    self.git_provider.repo
                )
                self.vars['cross_repo_context'] = self._format_cross_repo_context(cross_repo_context)
            
            # Phase 2: Jira context
            jira_context = {}
            if get_settings().workiz.enable_jira_integration:
                jira_context = await self.jira_provider.get_pr_ticket_context(
                    self.pr_description,
                    self.git_provider.pr.title
                )
                self.vars['jira_context'] = self._format_jira_context(jira_context)
            
            # Phase 3: Custom rules analysis
            rules_violations = {}
            if get_settings().workiz.enable_custom_rules:
                rules_violations = self.custom_rules.analyze(diff_files)
                self.vars['rules_violations'] = self._format_rules_violations(rules_violations)
            
            # Phase 4: SQL analysis
            sql_issues = []
            if get_settings().workiz.enable_sql_review:
                for file in diff_files:
                    if file.head_file:
                        issues = self.sql_analyzer.analyze_file(
                            file.head_file, 
                            file.filename
                        )
                        sql_issues.extend(issues)
                self.vars['sql_issues'] = self._format_sql_issues(sql_issues)
            
            # Phase 5: Security scan
            security_findings = []
            if get_settings().workiz.enable_enhanced_security:
                security_findings = self.security_scanner.scan_files(diff_files)
                self.vars['security_findings'] = self._format_security_findings(security_findings)
            
            # Phase 6: AI-powered review (original flow)
            await super()._prepare_prediction(get_settings().config.model)
            
            # Combine all findings
            pr_review = self._prepare_enhanced_pr_review(
                cross_repo_context,
                jira_context,
                rules_violations,
                sql_issues,
                security_findings
            )
            
            # Publish the review
            if get_settings().config.publish_output:
                self._publish_enhanced_review(pr_review)
            
        except Exception as e:
            get_logger().error(f"Failed to review PR: {e}")
    
    def _prepare_enhanced_pr_review(
        self,
        cross_repo_context: Dict,
        jira_context: Dict,
        rules_violations: Dict,
        sql_issues: List,
        security_findings: List
    ) -> str:
        """Prepare enhanced review output."""
        sections = []
        
        # Standard AI review
        sections.append(super()._prepare_pr_review())
        
        # Cross-repo context section
        if cross_repo_context:
            sections.append(self._render_cross_repo_section(cross_repo_context))
        
        # Jira context section
        if jira_context:
            sections.append(self._render_jira_section(jira_context))
        
        # Custom rules section
        if rules_violations:
            sections.append(self._render_rules_section(rules_violations))
        
        # SQL issues section
        if sql_issues:
            sections.append(self._render_sql_section(sql_issues))
        
        # Security findings section
        if security_findings:
            sections.append(self._render_security_section(security_findings))
        
        return "\n\n---\n\n".join(sections)
```

#### 7.2 Enhanced Prompts

Create: `pr_agent/settings/workiz_prompts.toml`

```toml
[workiz_review_prompt]
system="""You are Workiz PR-Reviewer, an AI specialized in reviewing Pull Requests for Workiz's NestJS microservices architecture.

Your review should focus on:
1. Code correctness and potential bugs
2. Functional programming principles (immutability, pure functions, no side effects)
3. NestJS architectural patterns (thin controllers, services for business logic)
4. Proper error handling and logging
5. Security vulnerabilities
6. Performance considerations

{%- if cross_repo_context %}

## Related Code from Other Services
The following code from other Workiz services is related to this PR:
{{ cross_repo_context }}
Consider how the changes might affect these dependent systems.
{%- endif %}

{%- if jira_context %}

## Jira Ticket Context
{{ jira_context }}
Verify that the implementation matches the ticket requirements.
{%- endif %}

{%- if rules_violations %}

## Custom Rules Violations
The following violations of Workiz coding standards were detected:
{{ rules_violations }}
Address these in your review.
{%- endif %}

{%- if sql_issues %}

## SQL Analysis
The following SQL issues were detected:
{{ sql_issues }}
Include these in your review.
{%- endif %}

{%- if security_findings %}

## Security Findings
The following security concerns were detected:
{{ security_findings }}
Address these as high priority items.
{%- endif %}

Provide up to {{ num_max_findings }} key issues to review.
"""

user="""
--PR Info--
Title: '{{title}}'
Branch: '{{branch}}'

{%- if description %}
PR Description:
{{ description|trim }}
{%- endif %}

The PR code diff:
{{ diff|trim }}

Response (valid YAML):
```yaml
"""
```

### Phase 8: Multi-Agent Architecture (Week 9-10)

#### 8.1 Agent Orchestrator

Create: `pr_agent/agents/orchestrator.py`

```python
import asyncio
from typing import List, Dict, Any
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class AgentResult:
    agent_name: str
    findings: List[Dict]
    metadata: Dict
    success: bool
    error: str = None

class BaseAgent(ABC):
    """Base class for specialized review agents."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    async def analyze(self, context: Dict) -> AgentResult:
        pass

class CodeQualityAgent(BaseAgent):
    """Agent focused on code quality and best practices."""
    
    @property
    def name(self) -> str:
        return "code_quality"
    
    async def analyze(self, context: Dict) -> AgentResult:
        # Use LLM to analyze code quality
        pass

class SecurityAgent(BaseAgent):
    """Agent focused on security analysis."""
    
    @property
    def name(self) -> str:
        return "security"
    
    async def analyze(self, context: Dict) -> AgentResult:
        # Security-focused analysis
        pass

class PerformanceAgent(BaseAgent):
    """Agent focused on performance issues."""
    
    @property
    def name(self) -> str:
        return "performance"
    
    async def analyze(self, context: Dict) -> AgentResult:
        # Performance analysis
        pass

class ArchitectureAgent(BaseAgent):
    """Agent focused on architectural patterns."""
    
    @property
    def name(self) -> str:
        return "architecture"
    
    async def analyze(self, context: Dict) -> AgentResult:
        # Architecture analysis
        pass

class AgentOrchestrator:
    """Orchestrates multiple specialized agents for comprehensive review."""
    
    def __init__(self, ai_handler):
        self.ai_handler = ai_handler
        self.agents: List[BaseAgent] = [
            CodeQualityAgent(ai_handler),
            SecurityAgent(ai_handler),
            PerformanceAgent(ai_handler),
            ArchitectureAgent(ai_handler),
        ]
    
    async def run_parallel_analysis(self, context: Dict) -> List[AgentResult]:
        """Run all agents in parallel."""
        tasks = [agent.analyze(context) for agent in self.agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        agent_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                agent_results.append(AgentResult(
                    agent_name=self.agents[i].name,
                    findings=[],
                    metadata={},
                    success=False,
                    error=str(result)
                ))
            else:
                agent_results.append(result)
        
        return agent_results
    
    async def synthesize_results(
        self, 
        results: List[AgentResult],
        context: Dict
    ) -> str:
        """Use main agent to synthesize results from sub-agents."""
        # Prepare synthesis prompt
        synthesis_context = self._prepare_synthesis_context(results)
        
        # Call main LLM to synthesize
        system_prompt = """You are a senior code reviewer synthesizing insights from multiple specialized review agents.
        
        Combine the findings from different agents into a coherent, prioritized review.
        Remove duplicates and resolve any conflicts.
        Provide a clear, actionable summary."""
        
        user_prompt = f"""
        Agent Findings:
        {synthesis_context}
        
        Original PR Context:
        {context['diff'][:5000]}  # Truncated for token limits
        
        Provide a synthesized review in markdown format.
        """
        
        response, _ = await self.ai_handler.chat_completion(
            model=get_settings().config.model,
            system=system_prompt,
            user=user_prompt
        )
        
        return response
```

---

## Database Architecture

### PostgreSQL with pgvector

**Why PostgreSQL + pgvector?**
- Native vector similarity search
- ACID compliance for data integrity
- JSON support for flexible metadata
- Mature ecosystem with asyncpg for async operations

**Schema Overview**:

```
┌─────────────────┐     ┌──────────────────┐
│  repositories   │────<│   code_chunks    │
└─────────────────┘     └──────────────────┘
        │                       │
        │               ┌───────┴───────┐
        │               │   embedding   │
        │               └───────────────┘
        │
        ├───────────────────────────────────┐
        │                                   │
┌───────┴───────┐               ┌───────────┴───────┐
│ review_history │               │   custom_rules    │
└───────────────┘               └───────────────────┘

┌─────────────────┐
│  jira_tickets   │
│   (embedding)   │
└─────────────────┘
```

### Connection Management

```python
# pr_agent/db/connection.py
import asyncpg
from contextlib import asynccontextmanager

class DatabaseManager:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool = None
    
    async def initialize(self):
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=5,
            max_size=20
        )
    
    @asynccontextmanager
    async def connection(self):
        async with self.pool.acquire() as conn:
            yield conn
    
    async def close(self):
        await self.pool.close()
```

---

## Multi-Agent Architecture

### Agent Flow Diagram

```
                    ┌────────────────────┐
                    │   PR Webhook       │
                    └────────┬───────────┘
                             │
                    ┌────────▼───────────┐
                    │   Orchestrator     │
                    └────────┬───────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼───────┐   ┌────────▼────────┐   ┌──────▼───────┐
│ Code Quality  │   │    Security     │   │ Performance  │
│    Agent      │   │     Agent       │   │    Agent     │
└───────┬───────┘   └────────┬────────┘   └──────┬───────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                    ┌────────▼───────────┐
                    │    Synthesizer     │
                    │   (Main Agent)     │
                    └────────┬───────────┘
                             │
                    ┌────────▼───────────┐
                    │  Publish Review    │
                    └────────────────────┘
```

### Agent Responsibilities

| Agent | Focus Areas | Output |
|-------|-------------|--------|
| Code Quality | Best practices, style, readability | Code suggestions |
| Security | Vulnerabilities, secrets, auth | Security findings |
| Performance | N+1 queries, memory leaks, complexity | Optimization suggestions |
| Architecture | Patterns, coupling, SOLID | Design recommendations |

---

## Webhook Handlers for Continuous Updates

### Add to GitHub App Server

Update: `pr_agent/servers/github_app.py`

```python
# Add these imports at the top
from pr_agent.services.indexing_service import RepositoryIndexingService, IncrementalUpdateService
from pr_agent.services.jira_sync_service import JiraSyncService
from pr_agent.db.connection import DatabaseManager

# Add new endpoints
@router.post("/api/v1/webhooks/push")
async def handle_push_webhook(background_tasks: BackgroundTasks, request: Request):
    """Handle push events for incremental indexing."""
    body = await request.json()
    
    # Verify webhook signature
    if not verify_webhook_signature(request):
        return Response(status_code=401)
    
    # Queue incremental indexing
    background_tasks.add_task(process_push_event, body)
    return {"status": "queued"}

@router.post("/api/v1/webhooks/jira")
async def handle_jira_webhook(background_tasks: BackgroundTasks, request: Request):
    """Handle Jira webhooks for ticket sync."""
    body = await request.json()
    
    # Queue Jira sync
    background_tasks.add_task(process_jira_event, body)
    return {"status": "queued"}

async def process_push_event(payload: Dict):
    """Process GitHub push event for indexing."""
    db = await get_database_manager()
    indexing_service = RepositoryIndexingService(
        db=db,
        github_token=get_settings().github.user_token,
        embedding_handler=None  # Will use default
    )
    update_service = IncrementalUpdateService(indexing_service)
    await update_service.handle_push_webhook(payload)

async def process_jira_event(payload: Dict):
    """Process Jira webhook event."""
    event_type = payload.get('webhookEvent', '')
    
    if event_type in ['jira:issue_created', 'jira:issue_updated']:
        issue_key = payload['issue']['key']
        
        db = await get_database_manager()
        jira_client = get_jira_client()
        jira_sync = JiraSyncService(jira_client, db, None)
        
        # Sync single ticket
        issue = jira_client.jira.issue(issue_key, expand='changelog')
        ticket_data = jira_sync._extract_ticket_data(issue)
        await jira_sync._store_tickets_batch([ticket_data])
```

### Add Admin API Endpoints

Create: `pr_agent/servers/admin_api.py`

```python
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from pr_agent.services.indexing_service import RepositoryIndexingService
from pr_agent.services.jira_sync_service import JiraSyncService, SyncScheduler
from pr_agent.db.connection import DatabaseManager
from pr_agent.config_loader import get_settings

admin_router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

class IndexRequest(BaseModel):
    repository_urls: List[str]
    branch: str = "main"
    full_index: bool = False

class JiraSyncRequest(BaseModel):
    project_keys: List[str]
    full_sync: bool = False

class IndexStatusResponse(BaseModel):
    repositories: List[dict]
    jira_tickets_count: int
    last_sync: Optional[str]

@admin_router.post("/index/repositories")
async def trigger_repo_indexing(
    request: IndexRequest,
    background_tasks: BackgroundTasks
):
    """Trigger repository indexing."""
    async def do_indexing():
        db = DatabaseManager(get_settings().workiz.database_url)
        await db.initialize()
        
        indexing_service = RepositoryIndexingService(
            db=db,
            github_token=get_settings().github.user_token,
            embedding_handler=None
        )
        
        job_type = 'full' if request.full_index else 'incremental'
        for url in request.repository_urls:
            await indexing_service.index_repository(url, request.branch, job_type)
        
        await db.close()
    
    background_tasks.add_task(do_indexing)
    return {"status": "indexing queued", "repositories": len(request.repository_urls)}

@admin_router.post("/sync/jira")
async def trigger_jira_sync(
    request: JiraSyncRequest,
    background_tasks: BackgroundTasks
):
    """Trigger Jira synchronization."""
    async def do_sync():
        db = DatabaseManager(get_settings().workiz.database_url)
        await db.initialize()
        
        from pr_agent.integrations.jira_client import JiraClient
        jira_client = JiraClient(
            base_url=get_settings().jira.base_url,
            email=get_settings().jira.email,
            api_token=get_settings().jira.api_token
        )
        
        jira_sync = JiraSyncService(jira_client, db, None)
        
        if request.full_sync:
            await jira_sync.full_sync(request.project_keys)
        else:
            await jira_sync.incremental_sync(request.project_keys)
        
        await db.close()
    
    background_tasks.add_task(do_sync)
    return {"status": "sync queued", "projects": request.project_keys}

@admin_router.get("/status", response_model=IndexStatusResponse)
async def get_indexing_status():
    """Get current indexing status."""
    db = DatabaseManager(get_settings().workiz.database_url)
    await db.initialize()
    
    async with db.connection() as conn:
        repos = await conn.fetch("""
            SELECT r.org_name, r.repo_name, r.last_indexed_at,
                   COUNT(cc.id) as chunk_count
            FROM repositories r
            LEFT JOIN code_chunks cc ON r.id = cc.repository_id
            GROUP BY r.id
            ORDER BY r.last_indexed_at DESC
        """)
        
        jira_count = await conn.fetchval("SELECT COUNT(*) FROM jira_tickets")
        
        last_job = await conn.fetchrow("""
            SELECT completed_at FROM indexing_jobs 
            WHERE status = 'completed' 
            ORDER BY completed_at DESC LIMIT 1
        """)
    
    await db.close()
    
    return IndexStatusResponse(
        repositories=[dict(r) for r in repos],
        jira_tickets_count=jira_count,
        last_sync=str(last_job['completed_at']) if last_job else None
    )

@admin_router.get("/pubsub/topology")
async def get_pubsub_topology():
    """Get PubSub event topology across all repos."""
    db = DatabaseManager(get_settings().workiz.database_url)
    await db.initialize()
    
    async with db.connection() as conn:
        publishers = await conn.fetch("""
            SELECT pe.topic, r.repo_name, pe.file_path, pe.handler_name
            FROM pubsub_events pe
            JOIN repositories r ON pe.repository_id = r.id
            WHERE pe.event_type = 'publish'
            ORDER BY pe.topic
        """)
        
        subscribers = await conn.fetch("""
            SELECT pe.topic, r.repo_name, pe.file_path, pe.handler_name,
                   pe.message_schema
            FROM pubsub_events pe
            JOIN repositories r ON pe.repository_id = r.id
            WHERE pe.event_type = 'subscribe'
            ORDER BY pe.topic
        """)
    
    await db.close()
    
    # Build topology
    topology = {}
    for pub in publishers:
        topic = pub['topic']
        if topic not in topology:
            topology[topic] = {'publishers': [], 'subscribers': []}
        topology[topic]['publishers'].append({
            'repo': pub['repo_name'],
            'file': pub['file_path'],
            'handler': pub['handler_name']
        })
    
    for sub in subscribers:
        topic = sub['topic']
        if topic not in topology:
            topology[topic] = {'publishers': [], 'subscribers': []}
        topology[topic]['subscribers'].append({
            'repo': sub['repo_name'],
            'file': sub['file_path'],
            'handler': sub['handler_name'],
            'schema': sub['message_schema']
        })
    
    return topology
```

---

## Local Development Setup

### Prerequisites

```bash
# Python 3.12+
python3 --version

# Docker & Docker Compose (recommended for local DB)
docker --version
docker-compose --version

# OR PostgreSQL 15+ with pgvector installed locally
psql --version
```

### Installation Steps

```bash
# 1. Clone the repository
cd /Users/daniellurie/Documents/Github/workiz-pr-agent

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install additional dependencies for Workiz features
pip install asyncpg jira pgvector aiohttp gitpython pyyaml

# 5. Copy secrets template
cp pr_agent/settings/.secrets_template.toml pr_agent/settings/.secrets.toml

# 6. Edit secrets file with your credentials
# See Configuration Guide below
```

### Database Setup

#### Option A: Docker Compose (Recommended)

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

Create `db/init/01_schema.sql`:

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Repositories table
CREATE TABLE repositories (
    id SERIAL PRIMARY KEY,
    org_name VARCHAR(255) NOT NULL,
    repo_name VARCHAR(255) NOT NULL,
    github_url TEXT,
    default_branch VARCHAR(100) DEFAULT 'main',
    last_indexed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(org_name, repo_name)
);

-- Code chunks with embeddings
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
    commit_sha VARCHAR(40),
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repository_id, file_path, start_line)
);

-- Jira tickets
CREATE TABLE jira_tickets (
    id SERIAL PRIMARY KEY,
    ticket_key VARCHAR(50) UNIQUE NOT NULL,
    title TEXT,
    description TEXT,
    status VARCHAR(100),
    ticket_type VARCHAR(100),
    acceptance_criteria TEXT,
    labels TEXT[],
    embedding vector(1536),
    raw_data JSONB,
    last_synced TIMESTAMP
);

-- Jira ticket history
CREATE TABLE jira_ticket_history (
    id SERIAL PRIMARY KEY,
    ticket_key VARCHAR(50) REFERENCES jira_tickets(ticket_key),
    field_changed VARCHAR(255),
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(255),
    changed_at TIMESTAMP,
    comment_text TEXT
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

-- Database queries found in code
CREATE TABLE database_queries (
    id SERIAL PRIMARY KEY,
    repository_id INT REFERENCES repositories(id),
    file_path TEXT NOT NULL,
    line_number INT,
    query_type VARCHAR(50),
    operation VARCHAR(50),
    query_content TEXT,
    tables_collections TEXT[],
    potential_issues JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Custom review rules
CREATE TABLE custom_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    language VARCHAR(50),
    framework VARCHAR(100),
    pattern TEXT,
    message TEXT,
    severity VARCHAR(50) DEFAULT 'warning',
    suggestion TEXT,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexing jobs
CREATE TABLE indexing_jobs (
    id SERIAL PRIMARY KEY,
    repository_id INT REFERENCES repositories(id),
    job_type VARCHAR(50),
    status VARCHAR(50),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    stats JSONB,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_code_chunks_repo ON code_chunks(repository_id);
CREATE INDEX idx_code_chunks_type ON code_chunks(chunk_type);
CREATE INDEX idx_code_chunks_embedding ON code_chunks USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_jira_tickets_embedding ON jira_tickets USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_pubsub_events_topic ON pubsub_events(topic);
CREATE INDEX idx_pubsub_events_type ON pubsub_events(event_type);
CREATE INDEX idx_database_queries_repo ON database_queries(repository_id);
CREATE INDEX idx_indexing_jobs_status ON indexing_jobs(status);

-- Insert default custom rules for Workiz stack
INSERT INTO custom_rules (rule_name, category, language, framework, pattern, message, severity, suggestion) VALUES
-- PHP Rules
('php_avoid_raw_sql', 'security', 'php', 'laravel', 'DB::raw\(|->whereRaw\(', 'Raw SQL queries detected', 'warning', 'Use query builder or prepared statements'),
('php_no_dd', 'code_quality', 'php', NULL, '\bdd\(|\bdump\(', 'Debug statement found', 'error', 'Remove debug statements before merging'),

-- JavaScript/TypeScript Rules
('js_no_console', 'code_quality', 'javascript', NULL, 'console\.(log|debug|info)\(', 'Console statement found', 'warning', 'Remove console statements or use proper logging'),
('ts_no_any', 'code_quality', 'typescript', NULL, ':\s*any\b', 'Explicit any type used', 'info', 'Consider using a more specific type'),

-- NestJS Rules
('nestjs_di_injection', 'architecture', 'typescript', 'nestjs', 'new\s+\w+Service\(|new\s+\w+Repository\(', 'Manual instantiation instead of DI', 'warning', 'Use dependency injection via constructor'),
('nestjs_controller_logic', 'architecture', 'typescript', 'nestjs', '@Controller.*\{[^}]*\b(save|update|delete|create)\b.*\}', 'Business logic in controller', 'info', 'Move business logic to service layer'),
('nestjs_async_handler', 'code_quality', 'typescript', 'nestjs', '@(Get|Post|Put|Delete|Patch)\([^)]*\)\s*\n\s*\w+\([^)]*\):\s*[^P]', 'Handler may not be async', 'info', 'Consider using async handlers'),

-- React Rules
('react_no_inline_styles', 'code_quality', 'typescript', 'react', 'style=\{\{', 'Inline styles detected', 'info', 'Consider using CSS modules or styled-components'),
('react_use_memo', 'performance', 'typescript', 'react', 'useMemo\(\s*\(\)\s*=>\s*\[', 'useMemo with array literal', 'info', 'Verify dependencies array is correct'),

-- Security Rules
('security_hardcoded_secret', 'security', NULL, NULL, '(password|secret|api_key|apikey|token)\s*[:=]\s*[''"][^''"]{8,}[''"]', 'Possible hardcoded secret', 'error', 'Use environment variables for secrets'),
('security_sql_injection', 'security', NULL, NULL, '\$\{.*\}.*(?:SELECT|INSERT|UPDATE|DELETE|WHERE)', 'Possible SQL injection', 'error', 'Use parameterized queries'),

-- Functional Programming Rules
('fp_no_mutation', 'style', 'typescript', NULL, '\.(push|pop|shift|unshift|splice)\(', 'Array mutation detected', 'info', 'Consider using immutable array operations like map, filter, concat'),
('fp_small_functions', 'style', NULL, NULL, 'function\s+\w+\s*\([^)]*\)\s*\{[^}]{500,}\}', 'Large function detected', 'info', 'Consider breaking into smaller functions');
```

Start the database:

```bash
docker-compose -f docker-compose.local.yml up -d
```

#### Option B: Local PostgreSQL

```bash
# Install pgvector (macOS)
brew install postgresql@16 pgvector

# Create database
createdb pr_agent

# Run schema
psql -d pr_agent -f db/init/01_schema.sql
```

### Initial Data Population

Create `repos.yaml` configuration:

```yaml
# repos.yaml - Repository configuration for indexing
# Based on actual Workiz repositories

repositories:
  # =====================================================
  # PHP Backend (Main Legacy Application)
  # =====================================================
  - url: https://github.com/Workiz/backend.git
    language: php
    framework: custom  # PHP with custom MVC, uses MySQL, MongoDB, Elasticsearch
    databases:
      - mysql
      - mongodb
      - elasticsearch
    description: "Main PHP backend with legacy API, uses Traefik for routing"
    
  # =====================================================
  # NestJS Microservices (TypeScript)
  # =====================================================
  - url: https://github.com/Workiz/auth.git
    language: typescript
    framework: nestjs
    databases:
      - mysql
    internal_packages:
      - "@workiz/all-exceptions-filter"
      - "@workiz/config-loader"
      - "@workiz/is-boolean-validation-pipe"
      - "@workiz/jwt-headers-generator"
      - "@workiz/node-logger"
      - "@workiz/pubsub-decorator-reflector"
      - "@workiz/pubsub-publish-client"
      - "@workiz/redis-nestjs"
      - "@workiz/socket-io-updater"
    description: "Authentication service - handles sessions, 2FA, API keys"
    
  - url: https://github.com/Workiz/crm-service.git
    language: typescript
    framework: nestjs
    databases:
      - mysql
    description: "CRM service for customer relationship management"
    
  - url: https://github.com/Workiz/ai-completion-service.git
    language: typescript
    framework: nestjs
    description: "AI completion service for text generation"
    
  - url: https://github.com/Workiz/csv-uploader.git
    language: typescript
    framework: nestjs
    description: "CSV upload and processing service"
    
  - url: https://github.com/Workiz/core-service.git
    language: typescript
    framework: nestjs
    databases:
      - mysql
    description: "Core business logic service"
    
  - url: https://github.com/Workiz/reporting-service.git
    language: typescript
    framework: nestjs
    databases:
      - mysql
      - elasticsearch
    description: "Reporting and analytics service"

  # =====================================================
  # Python Services
  # =====================================================
  - url: https://github.com/Workiz/python-service.git
    language: python
    framework: fastapi  # or django
    databases:
      - postgres
    description: "Python microservice with PostgreSQL"

  # =====================================================
  # React Frontend (TypeScript)
  # =====================================================
  - url: https://github.com/Workiz/web-app.git
    language: typescript
    framework: react
    description: "Main web application frontend"
    
  - url: https://github.com/Workiz/mobile-web.git
    language: typescript
    framework: react
    description: "Mobile-optimized web frontend"

  # =====================================================
  # Internal NPM Packages
  # =====================================================
  - url: https://github.com/Workiz/all-exceptions-filter.git
    language: typescript
    framework: nestjs
    is_internal_package: true
    
  - url: https://github.com/Workiz/config-loader.git
    language: typescript
    framework: nestjs
    is_internal_package: true
    
  - url: https://github.com/Workiz/node-logger.git
    language: typescript
    framework: nestjs
    is_internal_package: true
    
  - url: https://github.com/Workiz/pubsub-decorator-reflector.git
    language: typescript
    framework: nestjs
    is_internal_package: true
    
  - url: https://github.com/Workiz/pubsub-publish-client.git
    language: typescript
    framework: nestjs
    is_internal_package: true
    
  - url: https://github.com/Workiz/redis-nestjs.git
    language: typescript
    framework: nestjs
    is_internal_package: true

# Jira configuration
jira:
  projects:
    - WORK
    - DEVOPS
    - INFRA
    - MOBILE

# Indexing settings
settings:
  branch: main
  exclude_paths:
    - node_modules/
    - vendor/
    - dist/
    - build/
    - __tests__/
    - test/
    - coverage/
    - .next/
    - _assets/
    - gCache/
    - tmp/
    
  # Database patterns to detect
  database_patterns:
    mysql:
      - "mysql2"
      - "typeorm"
      - "knex"
    postgres:
      - "asyncpg"
      - "psycopg2"
      - "sqlalchemy"
    mongodb:
      - "mongoose"
      - "mongodb"
      - "pymongo"
    elasticsearch:
      - "@elastic/elasticsearch"
      - "elasticsearch"
```

---

## Cursor Team Rules Reference

The following cursor rules files define team coding standards. These should be parsed and integrated into the PR review:

### `.cursor/rules.mdc` (Auth Service)

```markdown
# Auth Service Rules

## Test Execution
All tests in the auth service project must be run using: npm run test
Always grep for "fail" and "error" in the test output.
Always check the actual implementation - do not guess or make assumptions.

## Code Style
Avoid writing inline comments.

## PubSub Pattern
Follow the pattern in `.cursor/rules/pubsub-pattern.mdc`
```

### `.cursor/rules/pubsub-pattern.mdc` (Auth Service)

```markdown
When implementing Google Cloud Pub/Sub event handlers in NestJS:

1. Define metadata constants in src/constants/pubsub-metadata.ts:
   RESOURCE_TOPIC_METADATA = '__resource-topic-candidate'
   RESOURCE_EVENT_METADATA = '__resource-event-candidate'

2. Decorator order: @PubSubTopic, @PubSubEvent, @PubSubAsyncAcknowledge

3. Method signature:
   public async onResourceAction(
     @PubSubPayload() _originalMessage: EmittedMessage<any>,
     @PubSubPayload(EventDto) eventData: EventDto
   ): Promise<void>

4. Required imports:
   - PubSubAsyncAcknowledge, PubSubEvent, PubSubPayload, PubSubTopic from @workiz/pubsub-decorator-reflector
   - EmittedMessage from @algoan/pubsub

5. Always log: this.logger.log('Received resource event', eventData)

6. Delegate with log details:
   await this.service.method(eventData, { transport: 'pubsub', payload: maskSensitive(eventData) })

7. Register in main.ts:
   app.get(ReflectDecoratorService).reflectDecorators([Controller], METADATA)

8. Naming: onResourceAction format (onUserCreated, onOrderUpdated)

9. Transport types: 'pubsub', 'internal', 'http'

NEVER:
- Implement business logic in controllers
- Forget to register in main.ts
- Use synchronous method signatures
- Log sensitive data without maskSensitive()
```

### Workspace Rules (From Cursor Settings)

The following rules are applied workspace-wide via Cursor settings:

| Rule | Description |
|------|-------------|
| **Verify Implementation** | Always check actual code before making changes |
| **Ask Ben for Clarification** | Pause and ask if requirements are unclear |
| **Reuse Code** | Check for existing methods/utilities across project |
| **No Inline Comments** | Code should be self-documenting |
| **Structured Logging** | Logger calls must include context objects |
| **Controller Structure** | Follow REST standards, plural nouns, proper responses |
| **Don't Call Non-Existing** | Verify methods exist before calling |
| **Use NestJS DI** | Use @Injectable() and constructor injection |
| **Global Exception Filter** | Use @workiz/all-exceptions-filter, avoid try-catch |
| **Functional Programming** | Prefer const, immutable operations, small functions |
| **Run npm run lint** | After NestJS changes |
| **TypeORM Raw SQL** | Use raw SQL in migrations, not table builder |
| **Async Best Practices** | Proper async/await, don't block event loop |
| **Feature-Based Architecture** | Modular, loosely coupled modules |
| **PubSub Patterns** | Follow exact decorator and registration pattern |
| **Single Responsibility** | One purpose per class/function |
| **Test Files Only** | Only modify test files unless discussed |
| **Run npm run test** | For NestJS projects |
| **Run npx tsc --noEmit** | After TypeScript changes |
| **DTOs with Validation** | Use class-validator for input |

---

## Authentication Architecture (Traefik + Auth Service)

### Overview

Workiz uses **Traefik** as a reverse proxy with **forwardAuth** middleware that delegates authentication to the **Auth Service**. This means:

1. **No guards/middleware needed in services** - Traefik handles auth before requests reach services
2. **X-WORKIZ headers are trustworthy** - Only when coming through Traefik
3. **Security review should focus on** - Data validation, injection prevention, not auth logic

### Traefik Configuration (from `traefik_dynamic.yml`)

```yaml
# Key auth middlewares
middlewares:
  auth:
    forwardAuth:
      address: "http://host.docker.internal:6717/proxy-sessions"
      authResponseHeaders:
        - "X-WORKIZ-AUTHENTICATED"
        - "X-WORKIZ"
        - "X-WORKIZ-ACCOUNT-ID"
  
  auth-crm:
    forwardAuth:
      address: "http://host.docker.internal:6717/proxy-sessions/throwable"
      authResponseHeaders:
        - "X-WORKIZ-AUTHENTICATED"
        - "X-WORKIZ"
        - "X-WORKIZ-ACCOUNT-ID"
  
  auth-api-crm:
    forwardAuth:
      address: "http://host.docker.internal:6717/api-keys/validate"
      authResponseHeaders:
        - "X-WORKIZ"
```

### Auth Flow

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│   Client    │────▶│   Traefik    │────▶│ Auth Service │────▶│  Service    │
│  (Browser)  │     │  (Routing)   │     │ (Validation) │     │ (Business)  │
└─────────────┘     └──────────────┘     └──────────────┘     └─────────────┘
                           │                     │
                           │  forwardAuth        │
                           │─────────────────────│
                           │                     │
                           │  X-WORKIZ headers   │
                           │◀────────────────────│
                           │                     │
                           │  Forward request    │
                           │  with headers       │
                           │─────────────────────────────────────▶
```

### Auth Service Endpoints

| Endpoint | Purpose | Used By |
|----------|---------|---------|
| `/proxy-sessions` | Validate session, return false if invalid | Routes that allow guests |
| `/proxy-sessions/throwable` | Validate session, throw 401 if invalid | Protected routes |
| `/api-keys/validate` | Validate API key for external integrations | CRM API routes |

### Security Review Implications

**DO Review:**
- Input validation (DTOs with class-validator)
- SQL/NoSQL injection prevention
- Sensitive data exposure in logs
- CORS configuration
- Cookie security settings
- Path traversal vulnerabilities

**DON'T Review (Handled by Traefik):**
- Missing auth guards
- JWT validation
- Session management
- Role-based access control (at route level)

### X-WORKIZ Header Structure

```typescript
// Set by Auth Service, consumed by other services
interface WorkizHeaders {
  'X-WORKIZ-AUTHENTICATED': boolean;
  'X-WORKIZ-ACCOUNT-ID': string;
  'X-WORKIZ': {
    accountId: string;
    valid: boolean;
    userId: string;
    apiKeyValidated?: boolean;  // For API key auth
  };
}
```

### Services Reading Auth Headers

```typescript
// Example: Reading auth headers in NestJS service
// These headers are ONLY trustworthy when coming through Traefik

@Get('resource')
async getResource(
  @Headers('x-workiz') workizHeader: string,
  @Headers('x-workiz-account-id') accountId: string,
) {
  const workiz = JSON.parse(workizHeader);
  // workiz.userId, workiz.accountId are validated by Auth Service
}
```

Run initial population:

```bash
# Activate virtual environment
source venv/bin/activate

# Set environment variables
export WORKIZ_DATABASE_URL="postgresql://pr_agent:pr_agent_dev@localhost:5432/pr_agent"
export GITHUB_USER_TOKEN="ghp_your_token_here"
export OPENAI_KEY="sk-your_key_here"
export JIRA_BASE_URL="https://workiz.atlassian.net"
export JIRA_API_TOKEN="your_jira_token"
export JIRA_EMAIL="your_email@workiz.com"

# Run initial indexing (this may take a while)
python -m pr_agent.cli_admin index-repos --config repos.yaml

# Run Jira sync
python -m pr_agent.cli_admin sync-jira --projects WORK,DEVOPS,INFRA,MOBILE --full

# Check status
python -m pr_agent.cli_admin status
```

### Setting Up Continuous Updates

#### GitHub Webhook for Repository Updates

1. Go to your GitHub organization settings → Webhooks
2. Add a new webhook:
   - **Payload URL**: `https://your-server/api/v1/webhooks/push`
   - **Content type**: `application/json`
   - **Secret**: Generate and save in `.secrets.toml`
   - **Events**: Select "Push events" and "Pull request events"

#### Jira Webhook for Ticket Updates

1. Go to Jira Settings → System → Webhooks
2. Create a new webhook:
   - **URL**: `https://your-server/api/v1/webhooks/jira`
   - **Events**: Select:
     - `jira:issue_created`
     - `jira:issue_updated`
     - `jira:issue_deleted`

#### Scheduled Sync (Cron)

For environments without webhook access, set up cron jobs:

```bash
# Add to crontab -e

# Incremental repo sync every 6 hours
0 */6 * * * cd /path/to/workiz-pr-agent && source venv/bin/activate && python -m pr_agent.cli_admin index-repos --config repos.yaml --incremental

# Jira sync every 2 hours
0 */2 * * * cd /path/to/workiz-pr-agent && source venv/bin/activate && python -m pr_agent.cli_admin sync-jira --projects WORK,DEVOPS,INFRA,MOBILE
```

### Running the Server Locally

```bash
# Option 1: Run directly with uvicorn
python -m uvicorn pr_agent.servers.github_app:app --host 0.0.0.0 --port 3000 --reload

# Option 2: Run with the start function
python -c "from pr_agent.servers.github_app import start; start()"

# Option 3: Use CLI for testing
python pr_agent/cli.py --pr_url="https://github.com/org/repo/pull/123" review
```

### Using ngrok for GitHub Webhooks

```bash
# Install ngrok
brew install ngrok

# Expose local server
ngrok http 3000

# Use the ngrok URL as your GitHub webhook URL:
# https://xxxx.ngrok.io/api/v1/github_webhooks
```

---

## Configuration Guide

### 1. Main Configuration (`configuration.toml`)

Add Workiz-specific settings:

```toml
[config]
model="gpt-4o"
fallback_models=["gpt-4o-mini"]
git_provider="github"

[workiz]
database_url = "postgresql://user:pass@localhost:5432/pr_agent"
enable_cross_repo_context = true
enable_jira_integration = true
enable_custom_rules = true
enable_sql_review = true
enable_enhanced_security = true

# RAG settings
rag_similarity_threshold = 0.75
rag_max_chunks = 10

# Review settings
max_review_comments = 10

[jira]
base_url = "https://workiz.atlassian.net"
project_keys = ["WORK", "DEVOPS", "INFRA"]

[pr_reviewer]
num_max_findings = 10  # Increased from 3
require_security_review = true
```

### 2. Secrets Configuration (`.secrets.toml`)

```toml
[openai]
key = "sk-..."

[github]
user_token = "ghp_..."
deployment_type = "user"  # or "app" for GitHub App

# For GitHub App deployment
# private_key = """..."""
# app_id = 123456
# webhook_secret = "..."

[jira]
api_token = "..."
email = "pr-agent@workiz.com"

[workiz]
database_password = "..."
```

### 3. Environment Variables

For production/containerized deployments:

```bash
# OpenAI
export OPENAI_KEY="sk-..."

# GitHub
export GITHUB_USER_TOKEN="ghp_..."

# Database
export WORKIZ_DATABASE_URL="postgresql://..."

# Jira
export JIRA_BASE_URL="https://workiz.atlassian.net"
export JIRA_API_TOKEN="..."
export JIRA_EMAIL="..."
```

### 4. Workiz Internal NPM Packages

Based on the auth service, these are the internal packages used across services:

```toml
[workiz]
# Internal package prefixes to track
internal_package_prefixes = ["@workiz/"]

# Known internal packages (update as needed)
internal_packages = [
    "@workiz/all-exceptions-filter",
    "@workiz/config-loader", 
    "@workiz/is-boolean-validation-pipe",
    "@workiz/jwt-headers-generator",
    "@workiz/node-logger",
    "@workiz/pubsub-decorator-reflector",
    "@workiz/pubsub-publish-client",
    "@workiz/redis-nestjs",
    "@workiz/socket-io-updater"
]
```

### 5. Custom Styling Rules Configuration (From Cursor Rules)

Create `pr_agent/settings/workiz_rules.toml`:

```toml
[workiz_rules]

# =============================================================================
# PHP / Laravel Rules
# =============================================================================

[workiz_rules.php]

[[workiz_rules.php.patterns]]
name = "avoid_raw_sql"
pattern = 'DB::raw\(|->whereRaw\(|->selectRaw\('
message = "Raw SQL queries detected - potential SQL injection risk"
severity = "warning"
suggestion = "Use Laravel query builder methods or parameterized queries"

[[workiz_rules.php.patterns]]
name = "no_dd_dump"
pattern = '\bdd\(|\bdump\(|\bvar_dump\('
message = "Debug statement found"
severity = "error"
suggestion = "Remove debug statements before merging"

[[workiz_rules.php.patterns]]
name = "eloquent_n_plus_one"
pattern = 'foreach.*\$\w+->(\w+)\s*\{'
message = "Potential N+1 query detected in loop"
severity = "warning"
suggestion = "Use eager loading with ->with() to prevent N+1 queries"

[[workiz_rules.php.patterns]]
name = "mass_assignment"
pattern = '\$fillable\s*=\s*\[\s*[''"]?\*[''"]?\s*\]'
message = "Mass assignment vulnerability - all fields fillable"
severity = "error"
suggestion = "Explicitly list fillable fields or use $guarded"

[[workiz_rules.php.patterns]]
name = "env_in_code"
pattern = "env\\(['\"]\\w+['\"]\\)"
message = "Direct env() call outside config files"
severity = "warning"
suggestion = "Use config() instead - env() only works in config files"

# =============================================================================
# JavaScript / Node.js Rules
# =============================================================================

[workiz_rules.javascript]

[[workiz_rules.javascript.patterns]]
name = "no_console"
pattern = 'console\.(log|debug|info|warn|error)\('
message = "Console statement found"
severity = "warning"
suggestion = "Use structured logging (Winston/Pino) instead of console"

[[workiz_rules.javascript.patterns]]
name = "callback_hell"
pattern = '\)\s*\{\s*\n[^\}]*\)\s*\{\s*\n[^\}]*\)\s*\{'
message = "Nested callbacks detected - callback hell"
severity = "warning"
suggestion = "Refactor to use async/await or Promise chains"

[[workiz_rules.javascript.patterns]]
name = "no_var"
pattern = '\bvar\s+\w+'
message = "var keyword used instead of const/let"
severity = "warning"
suggestion = "Use const for constants and let for variables"

[[workiz_rules.javascript.patterns]]
name = "mutation_in_reduce"
pattern = '\.reduce\([^)]+\{\s*[^}]*\.push\('
message = "Array mutation inside reduce"
severity = "info"
suggestion = "Use spread operator or concat for immutable patterns"

# =============================================================================
# TypeScript Rules
# =============================================================================

[workiz_rules.typescript]

[[workiz_rules.typescript.patterns]]
name = "no_any"
pattern = ':\s*any\b(?!\s*\[\])|<any>'
message = "Explicit 'any' type defeats TypeScript's purpose"
severity = "warning"
suggestion = "Use specific types, generics, or 'unknown' if type is truly unknown"

[[workiz_rules.typescript.patterns]]
name = "no_ts_ignore"
pattern = '@ts-ignore|@ts-nocheck'
message = "TypeScript errors suppressed"
severity = "warning"
suggestion = "Fix the type error instead of ignoring it"

[[workiz_rules.typescript.patterns]]
name = "prefer_readonly"
pattern = 'private\s+(?!readonly)\w+:\s*\w+'
message = "Private property without readonly modifier"
severity = "info"
suggestion = "Consider using readonly for properties not reassigned after construction"

[[workiz_rules.typescript.patterns]]
name = "enum_string_values"
pattern = 'enum\s+\w+\s*\{[^}]*=\s*\d+[^}]*\}'
message = "Enum with numeric values"
severity = "info"
suggestion = "Consider using string enums for better debugging and serialization"

# =============================================================================
# =============================================================================
# NestJS Rules (From Cursor Rules)
# =============================================================================

[workiz_rules.nestjs]

# Dependency Injection
[[workiz_rules.nestjs.patterns]]
name = "manual_instantiation"
pattern = 'new\s+\w+(Service|Repository|Provider|Guard|Interceptor)\('
message = "Manual class instantiation instead of dependency injection"
severity = "warning"
suggestion = "Inject dependencies via constructor - let NestJS IoC container manage instances"

# Controller architecture
[[workiz_rules.nestjs.patterns]]
name = "controller_business_logic"
pattern = '@Controller[^}]*\{[^}]*(\.save\(|\.create\(|\.update\(|\.delete\(|\.findOne\()'
message = "Direct repository/ORM calls in controller"
severity = "warning"
suggestion = "Controllers should delegate to services - move business logic to service layer"

[[workiz_rules.nestjs.patterns]]
name = "controller_complex_logic"
pattern = '@Controller[^}]*\{[^}]*(if\s*\(|for\s*\(|while\s*\(|switch\s*\()'
message = "Complex logic in controller - controllers should be thin"
severity = "info"
suggestion = "Move business logic to service layer"

# Structured Logging (From Cursor Rules)
[[workiz_rules.nestjs.patterns]]
name = "no_logger_context"
pattern = 'this\.logger\.(log|warn|error|debug)\s*\(\s*[''"`][^,]+\s*\)'
message = "Logger call without context object"
severity = "warning"
suggestion = "Always include context object: this.logger.log('message', { accountId, userId, ... })"

[[workiz_rules.nestjs.patterns]]
name = "logger_string_concat"
pattern = 'this\.logger\.(log|warn|error|debug)\s*\(\s*`[^`]*\$\{'
message = "String interpolation in logger - use structured logging instead"
severity = "warning"
suggestion = "Use: this.logger.log('message', { variable }) instead of template literals"

# Functional Programming (From Cursor Rules)
[[workiz_rules.nestjs.patterns]]
name = "let_usage"
pattern = '\blet\s+\w+\s*[:=]'
message = "let keyword used - prefer const and immutable patterns"
severity = "info"
suggestion = "Use const with immutable operations (map, filter, spread) instead of let with mutation"

[[workiz_rules.nestjs.patterns]]
name = "var_usage"
pattern = '\bvar\s+\w+'
message = "var keyword is deprecated"
severity = "error"
suggestion = "Use const or let instead of var"

[[workiz_rules.nestjs.patterns]]
name = "array_mutation"
pattern = '\.(push|pop|shift|unshift|splice)\('
message = "Array mutation method used"
severity = "info"
suggestion = "Use immutable methods: [...arr, item], arr.filter(), arr.map()"

[[workiz_rules.nestjs.patterns]]
name = "object_mutation"
pattern = '\w+\.\w+\s*=\s*[^=]'
message = "Object mutation detected"
severity = "info"
suggestion = "Use spread operator: { ...obj, prop: newValue }"

[[workiz_rules.nestjs.patterns]]
name = "imperative_loop"
pattern = '\bfor\s*\([^)]+\)\s*\{'
message = "Imperative for loop"
severity = "info"
suggestion = "Consider using map, filter, reduce for declarative iteration"

# PubSub Patterns (From Cursor Rules - pubsub-pattern.mdc)
[[workiz_rules.nestjs.patterns]]
name = "pubsub_no_ack"
pattern = '@PubSubTopic[^@]*@PubSubEvent(?![^@]*@PubSubAsyncAcknowledge)'
message = "PubSub handler without @PubSubAsyncAcknowledge"
severity = "error"
suggestion = "Always use @PubSubAsyncAcknowledge to prevent message loss"

[[workiz_rules.nestjs.patterns]]
name = "pubsub_sync_handler"
pattern = '@PubSub(Topic|Event)[^}]*public\s+(?!async)\w+\('
message = "PubSub handler is not async"
severity = "error"
suggestion = "PubSub handlers must be async: public async onEventName(...)"

[[workiz_rules.nestjs.patterns]]
name = "pubsub_handler_naming"
pattern = '@PubSubEvent[^}]*public\s+async\s+(?!on[A-Z])\w+\('
message = "PubSub handler should use onResourceAction naming format"
severity = "warning"
suggestion = "Use naming like: onUserCreated, onOrderUpdated"

[[workiz_rules.nestjs.patterns]]
name = "pubsub_missing_original_message"
pattern = '@PubSubPayload\(\)\s+(?!_)\w+:\s+EmittedMessage'
message = "Unused original message should be prefixed with underscore"
severity = "info"
suggestion = "Use: @PubSubPayload() _originalMessage: EmittedMessage<any>"

[[workiz_rules.nestjs.patterns]]
name = "pubsub_no_mask_sensitive"
pattern = 'transport:\s*[''"]pubsub[''"][^}]*payload:\s*(?!maskSensitive)\w+'
message = "PubSub payload logged without maskSensitive()"
severity = "error"
suggestion = "Use maskSensitive(eventData) when logging payloads with passwords/tokens"

[[workiz_rules.nestjs.patterns]]
name = "pubsub_business_in_controller"
pattern = '@PubSub(Topic|Event)[^}]*\.(save|create|update|delete|findOne)\('
message = "Business logic in PubSub controller handler"
severity = "error"
suggestion = "Delegate to service: await this.service.method(eventData, logDetails)"

[[workiz_rules.nestjs.patterns]]
name = "pubsub_missing_log"
pattern = '@PubSubEvent[^}]*public\s+async\s+on\w+\([^)]*\)[^}]*(?!this\.logger\.log)'
message = "PubSub handler without event reception logging"
severity = "warning"
suggestion = "Add: this.logger.log('Received resource event', eventData)"

[[workiz_rules.nestjs.patterns]]
name = "pubsub_wrong_decorator_order"
pattern = '@PubSubEvent[^@]*@PubSubTopic'
message = "PubSub decorators in wrong order"
severity = "error"
suggestion = "Correct order: @PubSubTopic, @PubSubEvent, @PubSubAsyncAcknowledge"

# Exception Handling (From Cursor Rules)
[[workiz_rules.nestjs.patterns]]
name = "catch_without_rethrow"
pattern = 'catch\s*\([^)]*\)\s*\{[^}]*(?!throw)'
message = "Exception caught but not rethrown"
severity = "warning"
suggestion = "Let exceptions propagate to @workiz/all-exceptions-filter, or rethrow after logging"

[[workiz_rules.nestjs.patterns]]
name = "try_catch_in_service"
pattern = 'try\s*\{[^}]+\}\s*catch'
message = "try-catch block in service"
severity = "info"
suggestion = "Avoid try-catch unless absolutely necessary - let global exception filter handle errors"

# Controller REST Standards (From Cursor Rules)
[[workiz_rules.nestjs.patterns]]
name = "singular_route"
pattern = "@Controller\\(['\"](?!.*s['\"])\\w+['\"]\\)"
message = "Controller route should use plural nouns"
severity = "info"
suggestion = "Use plural nouns for routes: /users, /products, /videos"

# TypeORM Migrations (From Cursor Rules)
[[workiz_rules.nestjs.patterns]]
name = "typeorm_table_builder"
pattern = 'createTable\s*\(|dropTable\s*\('
message = "Using TypeORM table builder instead of raw SQL"
severity = "warning"
suggestion = "Use raw SQL queries in migrations: queryRunner.query(`CREATE TABLE...`)"

# Inline Comments (From Cursor Rules)
[[workiz_rules.nestjs.patterns]]
name = "inline_comment"
pattern = '^\s*//(?!\s*(TODO|FIXME|NOTE|HACK|XXX):)'
message = "Inline comment detected - avoid unless necessary"
severity = "info"
suggestion = "Avoid inline comments - code should be self-documenting"

# =============================================================================
# React Rules
# =============================================================================

[workiz_rules.react]

[[workiz_rules.react.patterns]]
name = "inline_styles"
pattern = 'style=\{\{'
message = "Inline styles detected"
severity = "info"
suggestion = "Use CSS modules, styled-components, or Tailwind for better maintainability"

[[workiz_rules.react.patterns]]
name = "missing_key"
pattern = '\.map\([^)]+\)\s*=>\s*<(?!Fragment)[A-Z][^>]*(?!key=)'
message = "Map without key prop on element"
severity = "warning"
suggestion = "Add unique key prop to elements rendered in a loop"

[[workiz_rules.react.patterns]]
name = "index_as_key"
pattern = 'key=\{(index|i|idx)\}'
message = "Array index used as key"
severity = "warning"
suggestion = "Use unique ID from data instead of array index as key"

[[workiz_rules.react.patterns]]
name = "useeffect_no_deps"
pattern = 'useEffect\([^)]+\)\s*$'
message = "useEffect without dependency array"
severity = "warning"
suggestion = "Always specify dependency array to prevent infinite loops"

[[workiz_rules.react.patterns]]
name = "class_component"
pattern = 'class\s+\w+\s+extends\s+(React\.)?Component'
message = "Class component detected"
severity = "info"
suggestion = "Consider refactoring to functional component with hooks"

[[workiz_rules.react.patterns]]
name = "prop_drilling"
pattern = '\(\{[^}]{200,}\}\)'
message = "Many props being passed - possible prop drilling"
severity = "info"
suggestion = "Consider using Context or state management for deeply nested props"

# =============================================================================
# Python Rules (With PostgreSQL/SQLAlchemy Support)
# =============================================================================

[workiz_rules.python]

# Basic Python
[[workiz_rules.python.patterns]]
name = "py_no_print"
pattern = '\bprint\s*\('
message = "print() statement found"
severity = "warning"
suggestion = "Use proper logging (structlog, loguru) instead of print statements"

[[workiz_rules.python.patterns]]
name = "py_bare_except"
pattern = 'except\s*:'
message = "Bare except clause catches all exceptions including KeyboardInterrupt"
severity = "warning"
suggestion = "Use 'except Exception:' or catch specific exceptions"

[[workiz_rules.python.patterns]]
name = "py_mutable_default"
pattern = 'def\s+\w+\s*\([^)]*=\s*(\[\]|\{\})'
message = "Mutable default argument - can cause unexpected behavior"
severity = "error"
suggestion = "Use None as default and create mutable inside function"

[[workiz_rules.python.patterns]]
name = "py_global_var"
pattern = '\bglobal\s+\w+'
message = "Global variable usage detected"
severity = "warning"
suggestion = "Avoid global state - use parameters or class attributes"

[[workiz_rules.python.patterns]]
name = "py_type_hints"
pattern = 'def\s+\w+\s*\([^)]*\)\s*:'
message = "Function without return type hint"
severity = "info"
suggestion = "Add return type annotation: def func() -> ReturnType:"

[[workiz_rules.python.patterns]]
name = "py_star_import"
pattern = 'from\s+\S+\s+import\s+\*'
message = "Star import pollutes namespace"
severity = "warning"
suggestion = "Import specific names instead of using *"

[[workiz_rules.python.patterns]]
name = "py_assert_in_prod"
pattern = '\bassert\s+'
message = "Assert statements are stripped in optimized mode (-O)"
severity = "info"
suggestion = "Use proper validation with exceptions for production code"

[[workiz_rules.python.patterns]]
name = "py_hardcoded_password"
pattern = '(password|secret|api_key)\s*=\s*[''"][^''"]{4,}[''"]'
message = "Possible hardcoded credential"
severity = "error"
suggestion = "Use environment variables or secret manager"

# FastAPI specific
[[workiz_rules.python.patterns]]
name = "fastapi_sync_endpoint"
pattern = '@(app|router)\.(get|post|put|patch|delete)\([^)]*\)\s*\ndef\s+'
message = "Synchronous FastAPI endpoint may block event loop"
severity = "warning"
suggestion = "Use async def for FastAPI endpoints"

[[workiz_rules.python.patterns]]
name = "fastapi_missing_response_model"
pattern = '@(app|router)\.(get|post|put|patch|delete)\([^)]*(?!response_model)'
message = "FastAPI endpoint without response_model"
severity = "info"
suggestion = "Add response_model for OpenAPI documentation and validation"

# PostgreSQL / SQLAlchemy
[[workiz_rules.python.patterns]]
name = "pg_raw_sql"
pattern = 'execute\s*\(\s*[''"](?:SELECT|INSERT|UPDATE|DELETE)'
message = "Raw SQL query - consider using SQLAlchemy ORM"
severity = "info"
suggestion = "Use SQLAlchemy ORM methods or Core for type safety"

[[workiz_rules.python.patterns]]
name = "pg_sql_injection"
pattern = 'execute\s*\(\s*f[''"]|execute\s*\(\s*[''"].*%s.*[''"].*%'
message = "Possible SQL injection - string formatting in query"
severity = "error"
suggestion = "Use parameterized queries: execute(query, (param,))"

[[workiz_rules.python.patterns]]
name = "pg_missing_index_hint"
pattern = '\.filter\([^)]+\)\.all\(\)'
message = "Query without pagination or limit"
severity = "info"
suggestion = "Consider adding .limit() to prevent large result sets"

[[workiz_rules.python.patterns]]
name = "pg_n_plus_one"
pattern = 'for\s+\w+\s+in\s+\w+:\s*\n[^#]*\.(query|filter)\('
message = "Possible N+1 query in loop"
severity = "warning"
suggestion = "Use eager loading with joinedload() or subqueryload()"

[[workiz_rules.python.patterns]]
name = "pg_no_connection_pool"
pattern = 'create_engine\([^)]*(?!pool_size)'
message = "Database engine without pool configuration"
severity = "info"
suggestion = "Configure pool_size and max_overflow for production"

[[workiz_rules.python.patterns]]
name = "pg_commit_in_loop"
pattern = 'for\s+\w+\s+in\s+\w+:\s*\n[^#]*\.commit\(\)'
message = "Database commit inside loop"
severity = "warning"
suggestion = "Batch commits outside the loop for better performance"

# Async Python
[[workiz_rules.python.patterns]]
name = "asyncio_blocking_call"
pattern = 'async\s+def[^:]+:\s*\n[^#]*(time\.sleep|requests\.(get|post))'
message = "Blocking call in async function"
severity = "error"
suggestion = "Use asyncio.sleep() and httpx/aiohttp for async code"

[[workiz_rules.python.patterns]]
name = "asyncpg_not_used"
pattern = 'import\s+psycopg2'
message = "Using psycopg2 - consider asyncpg for async applications"
severity = "info"
suggestion = "Use asyncpg or databases library for async PostgreSQL"

# =============================================================================
# Functional Programming Style Rules
# =============================================================================

[workiz_rules.functional]

[[workiz_rules.functional.patterns]]
name = "large_function"
lines_threshold = 30
message = "Function exceeds 30 lines"
severity = "warning"
suggestion = "Break into smaller, single-purpose functions"

[[workiz_rules.functional.patterns]]
name = "deep_nesting"
nesting_threshold = 3
message = "Deep nesting detected (>3 levels)"
severity = "warning"
suggestion = "Extract nested logic into separate functions or use early returns"

[[workiz_rules.functional.patterns]]
name = "object_mutation"
pattern = '\w+\.\w+\s*=\s*[^=]'
message = "Object mutation detected"
severity = "info"
suggestion = "Use spread operator: { ...obj, prop: newValue }"

[[workiz_rules.functional.patterns]]
name = "for_loop"
pattern = '\bfor\s*\([^)]+\)\s*\{'
message = "Imperative for loop"
severity = "info"
suggestion = "Consider using map, filter, reduce, or forEach for declarative iteration"

# =============================================================================
# Security Rules (General - Auth handled by Traefik + Auth Service)
# Note: Guards/auth middleware not needed - Traefik's forwardAuth handles authentication
# Focus on: data validation, injection prevention, sensitive data exposure
# =============================================================================

[workiz_rules.security]

# Hardcoded Secrets
[[workiz_rules.security.patterns]]
name = "hardcoded_secret"
pattern = '(password|secret|api_key|apikey|token|private_key|auth_token|bearer)\s*[:=]\s*[''"][^''"]{8,}[''"]'
message = "Possible hardcoded secret detected"
severity = "error"
suggestion = "Use @workiz/config-loader with GCloud Secret Manager"

[[workiz_rules.security.patterns]]
name = "hardcoded_connection_string"
pattern = '(mysql|postgres|mongodb|redis)://[^$]+'
message = "Hardcoded database connection string"
severity = "error"
suggestion = "Use environment variables for connection strings"

# SQL/NoSQL Injection
[[workiz_rules.security.patterns]]
name = "sql_injection"
pattern = '(\$\{|\+\s*\w+\s*\+).*?(SELECT|INSERT|UPDATE|DELETE|WHERE)'
message = "Possible SQL injection vulnerability"
severity = "error"
suggestion = "Use TypeORM query builder or parameterized queries"

[[workiz_rules.security.patterns]]
name = "raw_sql_with_params"
pattern = 'query\s*\(\s*`[^`]*\$\{'
message = "Template literal in raw SQL query"
severity = "error"
suggestion = "Use parameterized queries: query('SELECT * FROM x WHERE id = ?', [id])"

[[workiz_rules.security.patterns]]
name = "mongo_injection"
pattern = '\{\s*\$where\s*:'
message = "MongoDB $where operator is vulnerable to injection"
severity = "error"
suggestion = "Avoid $where - use standard query operators"

# XSS Prevention
[[workiz_rules.security.patterns]]
name = "innerHTML"
pattern = '\.innerHTML\s*=|dangerouslySetInnerHTML'
message = "Direct HTML insertion - XSS risk"
severity = "warning"
suggestion = "Sanitize content or use React's JSX"

[[workiz_rules.security.patterns]]
name = "eval_usage"
pattern = '\beval\s*\('
message = "eval() usage detected - code injection risk"
severity = "error"
suggestion = "Never use eval() - find alternative approaches"

[[workiz_rules.security.patterns]]
name = "function_constructor"
pattern = 'new\s+Function\s*\('
message = "Function constructor is similar to eval()"
severity = "error"
suggestion = "Avoid dynamic code execution"

# Sensitive Data Logging
[[workiz_rules.security.patterns]]
name = "logging_password"
pattern = 'logger\.(log|info|debug|warn|error)\s*\([^)]*password'
message = "Possible password logging"
severity = "error"
suggestion = "Never log passwords or sensitive data - use maskSensitive()"

[[workiz_rules.security.patterns]]
name = "logging_token"
pattern = 'logger\.(log|info|debug|warn|error)\s*\([^)]*(token|apiKey|secret)'
message = "Possible token/secret logging"
severity = "error"
suggestion = "Never log tokens or secrets - use maskSensitive()"

[[workiz_rules.security.patterns]]
name = "console_log_sensitive"
pattern = 'console\.(log|debug)\s*\([^)]*(password|token|secret|apiKey)'
message = "Sensitive data in console.log"
severity = "error"
suggestion = "Remove console statements and never log sensitive data"

# HTTP Security
[[workiz_rules.security.patterns]]
name = "http_without_https"
pattern = '[''"]http://(?!localhost|127\.0\.0\.1|host\.docker\.internal)'
message = "HTTP URL used instead of HTTPS"
severity = "warning"
suggestion = "Use HTTPS for secure communication"

# Path Traversal
[[workiz_rules.security.patterns]]
name = "path_traversal"
pattern = '(readFile|writeFile|unlink|readdir)\s*\([^)]*(\+|concat|\$\{)'
message = "Dynamic file path - possible path traversal"
severity = "warning"
suggestion = "Validate and sanitize file paths"

# Cookie Security
[[workiz_rules.security.patterns]]
name = "insecure_cookie"
pattern = 'cookie\s*\([^)]*(?!.*httpOnly)(?!.*secure)'
message = "Cookie may not have httpOnly or secure flags"
severity = "info"
suggestion = "Set httpOnly: true, secure: true for sensitive cookies"

# Auth Headers - Traefik Integration
[[workiz_rules.security.patterns]]
name = "manipulating_workiz_headers"
pattern = 'set\s*\(\s*[''"]X-WORKIZ'
message = "Manually setting X-WORKIZ headers"
severity = "warning"
suggestion = "X-WORKIZ headers should only be set by auth service via Traefik forwardAuth"

[[workiz_rules.security.patterns]]
name = "trusting_workiz_header_without_traefik"
pattern = 'headers\[[''"]X-WORKIZ[''"]'
message = "Reading X-WORKIZ headers - ensure request comes through Traefik"
severity = "info"
suggestion = "X-WORKIZ headers are only trustworthy when coming through Traefik"

# CORS
[[workiz_rules.security.patterns]]
name = "cors_wildcard"
pattern = 'origin\s*:\s*[''"]\\*[''"]|Access-Control-Allow-Origin.*\\*'
message = "CORS allows all origins"
severity = "warning"
suggestion = "Restrict CORS to specific trusted domains"

# JWT/Session
[[workiz_rules.security.patterns]]
name = "jwt_secret_hardcoded"
pattern = 'jwt\.sign\s*\([^)]*[''"][A-Za-z0-9]{10,}[''"]'
message = "Hardcoded JWT secret"
severity = "error"
suggestion = "Use environment variable for JWT secret"

# Input Validation (NestJS DTOs)
[[workiz_rules.security.patterns]]
name = "missing_dto_validation"
pattern = '@Body\(\)\s+\w+:\s+(?!.*Dto)'
message = "Request body without DTO validation"
severity = "warning"
suggestion = "Use DTOs with class-validator decorators for input validation"

# =============================================================================
# Database Query Rules (MySQL, MongoDB, Elasticsearch)
# =============================================================================

[workiz_rules.database]

# MySQL specific
[[workiz_rules.database.patterns]]
name = "mysql_select_star"
pattern = 'SELECT\s+\*\s+FROM'
message = "SELECT * query - fetches all columns"
severity = "warning"
suggestion = "Specify only needed columns for better performance"

[[workiz_rules.database.patterns]]
name = "mysql_no_limit"
pattern = 'SELECT.*FROM.*WHERE(?!.*LIMIT)'
message = "Query without LIMIT clause"
severity = "info"
suggestion = "Consider adding LIMIT to prevent unbounded result sets"

[[workiz_rules.database.patterns]]
name = "mysql_like_wildcard_start"
pattern = "LIKE\s+['\"]%"
message = "LIKE with leading wildcard cannot use index"
severity = "warning"
suggestion = "Leading wildcards prevent index usage - consider full-text search"

# MongoDB specific
[[workiz_rules.database.patterns]]
name = "mongo_no_index_hint"
pattern = '\.find\(\s*\{[^}]*\}\s*\)(?!\.hint)'
message = "MongoDB find without index hint"
severity = "info"
suggestion = "Consider adding .hint() for complex queries or verify indexes exist"

[[workiz_rules.database.patterns]]
name = "mongo_regex_no_anchor"
pattern = '\$regex.*[''"][^^]'
message = "MongoDB regex without ^ anchor cannot use index"
severity = "warning"
suggestion = "Use anchored regex /^pattern/ when possible"

[[workiz_rules.database.patterns]]
name = "mongo_large_in"
pattern = '\$in\s*:\s*\[[^\]]{500,}\]'
message = "Large $in array may cause performance issues"
severity = "warning"
suggestion = "Batch queries or consider different data model"

# Elasticsearch specific
[[workiz_rules.database.patterns]]
name = "es_wildcard_query"
pattern = 'wildcard.*query'
message = "Elasticsearch wildcard query is slow"
severity = "warning"
suggestion = "Use prefix query or ngrams for better performance"

[[workiz_rules.database.patterns]]
name = "es_deep_pagination"
pattern = '"from"\s*:\s*\d{4,}'
message = "Elasticsearch deep pagination is inefficient"
severity = "warning"
suggestion = "Use search_after for deep pagination instead of from/size"

[[workiz_rules.database.patterns]]
name = "es_script_query"
pattern = '"script"\s*:\s*\{'
message = "Elasticsearch script queries cannot be cached"
severity = "info"
suggestion = "Consider using runtime fields or pre-computed values"
```

---

## Detailed Component Implementation

### New Files to Create

```
pr_agent/
├── db/
│   ├── __init__.py
│   ├── connection.py          # Database connection management
│   ├── models.py              # SQLAlchemy/Pydantic models
│   ├── repositories.py        # Data access layer
│   └── embeddings.py          # Embedding generation/storage
├── integrations/
│   ├── __init__.py
│   └── jira_client.py         # Jira API client
├── tools/
│   ├── repo_indexer.py        # Repository indexing for RAG
│   ├── context_retriever.py   # Cross-repo context retrieval
│   ├── jira_context_provider.py # Jira integration
│   ├── custom_rules_engine.py # Custom code rules
│   ├── sql_analyzer.py        # SQL query analysis
│   ├── security_scanner.py    # Enhanced security checks
│   └── workiz_pr_reviewer.py  # Extended PR reviewer
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py        # Multi-agent orchestration
│   ├── code_quality_agent.py  # Code quality agent
│   ├── security_agent.py      # Security agent
│   └── performance_agent.py   # Performance agent
└── settings/
    └── workiz_prompts.toml    # Workiz-specific prompts
```

### Files to Modify

1. **`pr_agent/agent/pr_agent.py`**
   - Add `workiz_review` command mapping
   - Import WorkizPRReviewer

2. **`pr_agent/servers/github_app.py`**
   - Add custom endpoint `/api/v1/workiz_review`
   - Initialize database connection on startup

3. **`pr_agent/config_loader.py`**
   - Add Workiz configuration files to settings_files list

4. **`pr_agent/settings/configuration.toml`**
   - Add `[workiz]` and `[jira]` sections

5. **`requirements.txt`**
   - Add: `asyncpg`, `jira`, `pgvector`, `sqlalchemy[asyncio]`

---

## Deployment Strategy

### Google Cloud Platform

```yaml
# Cloud Run deployment
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: workiz-pr-agent
spec:
  template:
    spec:
      containers:
        - image: gcr.io/workiz/pr-agent:latest
          ports:
            - containerPort: 3000
          env:
            - name: OPENAI_KEY
              valueFrom:
                secretKeyRef:
                  name: pr-agent-secrets
                  key: openai-key
            - name: WORKIZ_DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: pr-agent-secrets
                  key: database-url
```

### Database (Cloud SQL)

```bash
# Create PostgreSQL instance
gcloud sql instances create pr-agent-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Enable pgvector extension
# Connect and run: CREATE EXTENSION vector;
```

---

## Timeline and Milestones

### Week 1-2: Foundation
- [ ] Set up PostgreSQL database with pgvector
- [ ] Create database models and connection management
- [ ] Set up local development environment
- [ ] Basic configuration structure

### Week 3-4: Cross-Repository Context
- [ ] Implement repository indexer
- [ ] Create embeddings storage
- [ ] Implement context retriever
- [ ] Test with 2-3 sample repositories

### Week 5: Jira Integration
- [ ] Implement Jira client
- [ ] Create Jira context provider
- [ ] Test ticket extraction and comparison

### Week 6: Custom Rules
- [ ] Implement rule engine
- [ ] Create Workiz-specific rules
- [ ] Integrate with review flow

### Week 7: SQL & Security
- [ ] Implement SQL analyzer
- [ ] Implement security scanner
- [ ] Test with sample PRs

### Week 8-9: Integration
- [ ] Create WorkizPRReviewer
- [ ] Create enhanced prompts
- [ ] Integrate all components
- [ ] End-to-end testing

### Week 10: Multi-Agent & Polish
- [ ] Implement agent orchestrator
- [ ] Optimize performance
- [ ] Documentation
- [ ] Deployment preparation

---

## Testing Strategy

### Unit Tests

```python
# tests/test_custom_rules.py
def test_functional_style_rule():
    rule = FunctionalStyleRule()
    content = "let x = 5;"
    violations = rule.check(content, "test.ts")
    assert len(violations) == 1
    assert "const" in violations[0].suggestion
```

### Integration Tests

```python
# tests/test_workiz_reviewer.py
async def test_cross_repo_context():
    reviewer = WorkizPRReviewer(pr_url="...")
    context = await reviewer.context_retriever.find_related_code(...)
    assert len(context) > 0
```

### End-to-End Tests

```python
# tests/e2e/test_full_review.py
async def test_full_review_flow():
    response = await client.post(
        "/api/v1/workiz_review",
        json={"pr_url": "https://github.com/..."}
    )
    assert response.status_code == 200
```

---

## Language and Framework Support

### Supported Stack Overview

| Language/Framework | File Extensions | Key Patterns to Index |
|--------------------|-----------------|----------------------|
| PHP | `.php` | Classes, Functions, Routes (Laravel/Symfony) |
| NodeJS (JavaScript) | `.js`, `.mjs`, `.cjs` | Functions, Express routes, Event handlers |
| NodeJS (TypeScript) | `.ts`, `.tsx` | Classes, Functions, Interfaces, Types |
| NestJS (TypeScript) | `.ts` | Controllers, Services, Modules, Guards, DTOs |
| React (TypeScript) | `.tsx`, `.ts` | Components, Hooks, Context, Redux |

### Language-Specific Analyzers

Create: `pr_agent/tools/language_analyzers/`

```
pr_agent/tools/language_analyzers/
├── __init__.py
├── base_analyzer.py
├── php_analyzer.py
├── javascript_analyzer.py
├── typescript_analyzer.py
├── nestjs_analyzer.py
└── react_analyzer.py
```

#### Base Analyzer

```python
# pr_agent/tools/language_analyzers/base_analyzer.py
from abc import ABC, abstractmethod
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class CodeElement:
    """Represents an extracted code element for indexing."""
    element_type: str  # 'function', 'class', 'endpoint', 'component', 'hook', etc.
    name: str
    file_path: str
    start_line: int
    end_line: int
    content: str
    signature: str  # Function/method signature
    dependencies: List[str]  # Imports, calls
    metadata: Dict  # Language-specific metadata

class BaseLanguageAnalyzer(ABC):
    """Base class for language-specific code analyzers."""
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """File extensions this analyzer handles."""
        pass
    
    @abstractmethod
    def extract_elements(self, content: str, file_path: str) -> List[CodeElement]:
        """Extract indexable code elements from file content."""
        pass
    
    @abstractmethod
    def extract_dependencies(self, content: str) -> List[str]:
        """Extract external dependencies (imports, requires)."""
        pass
    
    @abstractmethod
    def extract_api_calls(self, content: str) -> List[Dict]:
        """Extract HTTP/API calls made from this file."""
        pass
    
    @abstractmethod
    def extract_event_handlers(self, content: str) -> List[Dict]:
        """Extract event handlers (PubSub, EventEmitter, etc.)."""
        pass
    
    @abstractmethod
    def extract_event_publishers(self, content: str) -> List[Dict]:
        """Extract event publishing calls."""
        pass
```

#### PHP Analyzer

```python
# pr_agent/tools/language_analyzers/php_analyzer.py
import re
from typing import List, Dict
from .base_analyzer import BaseLanguageAnalyzer, CodeElement

class PHPAnalyzer(BaseLanguageAnalyzer):
    """Analyzer for PHP code (Laravel, Symfony, plain PHP)."""
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.php']
    
    def extract_elements(self, content: str, file_path: str) -> List[CodeElement]:
        elements = []
        lines = content.split('\n')
        
        # Extract classes
        class_pattern = r'(abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([^{]+))?'
        for match in re.finditer(class_pattern, content):
            class_name = match.group(2)
            start_line = content[:match.start()].count('\n') + 1
            end_line = self._find_block_end(content, match.end())
            
            elements.append(CodeElement(
                element_type='class',
                name=class_name,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                content=content[match.start():self._get_position(content, end_line)],
                signature=match.group(0),
                dependencies=self._extract_class_dependencies(content, class_name),
                metadata={
                    'extends': match.group(3),
                    'implements': match.group(4).split(',') if match.group(4) else [],
                    'is_abstract': bool(match.group(1))
                }
            ))
        
        # Extract functions/methods
        func_pattern = r'(public|private|protected|static|\s)+function\s+(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(func_pattern, content):
            func_name = match.group(2)
            start_line = content[:match.start()].count('\n') + 1
            end_line = self._find_block_end(content, match.end())
            
            elements.append(CodeElement(
                element_type='function',
                name=func_name,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                content=content[match.start():self._get_position(content, end_line)],
                signature=match.group(0),
                dependencies=[],
                metadata={
                    'visibility': match.group(1).strip() if match.group(1) else 'public',
                    'params': match.group(3)
                }
            ))
        
        # Extract Laravel routes
        route_patterns = [
            r"Route::(get|post|put|patch|delete)\s*\(\s*['\"]([^'\"]+)['\"]",
            r"->route\s*\(\s*['\"]([^'\"]+)['\"]"
        ]
        for pattern in route_patterns:
            for match in re.finditer(pattern, content):
                elements.append(CodeElement(
                    element_type='endpoint',
                    name=match.group(2) if len(match.groups()) > 1 else match.group(1),
                    file_path=file_path,
                    start_line=content[:match.start()].count('\n') + 1,
                    end_line=content[:match.end()].count('\n') + 1,
                    content=match.group(0),
                    signature=match.group(0),
                    dependencies=[],
                    metadata={
                        'method': match.group(1).upper() if len(match.groups()) > 1 else 'GET',
                        'framework': 'laravel'
                    }
                ))
        
        return elements
    
    def extract_dependencies(self, content: str) -> List[str]:
        """Extract use statements and require/include."""
        deps = []
        
        # use statements
        use_pattern = r'use\s+([^;]+);'
        deps.extend(re.findall(use_pattern, content))
        
        # require/include
        require_pattern = r"(require|include)(?:_once)?\s*(?:\()?['\"]([^'\"]+)['\"]"
        for match in re.finditer(require_pattern, content):
            deps.append(match.group(2))
        
        return deps
    
    def extract_api_calls(self, content: str) -> List[Dict]:
        """Extract HTTP client calls (Guzzle, curl, etc.)."""
        calls = []
        
        # Guzzle calls
        guzzle_patterns = [
            r"\->(?:get|post|put|patch|delete)\s*\(\s*['\"]([^'\"]+)['\"]",
            r"Http::(get|post|put|patch|delete)\s*\(\s*['\"]([^'\"]+)['\"]",
        ]
        
        for pattern in guzzle_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                calls.append({
                    'type': 'http',
                    'method': match.group(1) if len(match.groups()) > 1 else 'GET',
                    'url': match.group(2) if len(match.groups()) > 1 else match.group(1),
                    'line': content[:match.start()].count('\n') + 1
                })
        
        return calls
    
    def extract_event_handlers(self, content: str) -> List[Dict]:
        """Extract event listeners."""
        handlers = []
        
        # Laravel event listeners
        patterns = [
            r"Event::listen\s*\(\s*['\"]([^'\"]+)['\"]",
            r"protected\s+\$listen\s*=\s*\[([^\]]+)\]",
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                handlers.append({
                    'event': match.group(1),
                    'line': content[:match.start()].count('\n') + 1,
                    'framework': 'laravel'
                })
        
        return handlers
    
    def extract_event_publishers(self, content: str) -> List[Dict]:
        """Extract event dispatching."""
        publishers = []
        
        patterns = [
            r"event\s*\(\s*new\s+(\w+)",
            r"Event::dispatch\s*\(\s*['\"]?([^'\")\s]+)",
            r"broadcast\s*\(\s*new\s+(\w+)",
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                publishers.append({
                    'event': match.group(1),
                    'line': content[:match.start()].count('\n') + 1,
                    'framework': 'laravel'
                })
        
        return publishers
    
    def _find_block_end(self, content: str, start_pos: int) -> int:
        """Find the end line of a code block (matching braces)."""
        brace_count = 0
        started = False
        for i, char in enumerate(content[start_pos:], start_pos):
            if char == '{':
                brace_count += 1
                started = True
            elif char == '}':
                brace_count -= 1
            if started and brace_count == 0:
                return content[:i+1].count('\n') + 1
        return content.count('\n') + 1
    
    def _get_position(self, content: str, line_num: int) -> int:
        """Get character position for a line number."""
        lines = content.split('\n')
        return sum(len(line) + 1 for line in lines[:line_num])
    
    def _extract_class_dependencies(self, content: str, class_name: str) -> List[str]:
        """Extract dependencies injected into class constructor."""
        deps = []
        # Find constructor
        constructor_pattern = rf'function\s+__construct\s*\(([^)]+)\)'
        match = re.search(constructor_pattern, content)
        if match:
            params = match.group(1)
            # Extract type hints
            type_pattern = r'(\w+)\s+\$\w+'
            deps = re.findall(type_pattern, params)
        return deps
```

#### JavaScript/TypeScript Analyzer

```python
# pr_agent/tools/language_analyzers/javascript_analyzer.py
import re
from typing import List, Dict
from .base_analyzer import BaseLanguageAnalyzer, CodeElement

class JavaScriptAnalyzer(BaseLanguageAnalyzer):
    """Analyzer for JavaScript/Node.js code."""
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.js', '.mjs', '.cjs']
    
    def extract_elements(self, content: str, file_path: str) -> List[CodeElement]:
        elements = []
        
        # Extract functions (regular, arrow, async)
        func_patterns = [
            # Regular function
            r'(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)',
            # Arrow function assigned to const/let
            r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>',
            # Method in object
            r'(\w+)\s*:\s*(?:async\s+)?function\s*\(',
            r'(\w+)\s*:\s*(?:async\s+)?\([^)]*\)\s*=>',
        ]
        
        for pattern in func_patterns:
            for match in re.finditer(pattern, content):
                func_name = match.group(1)
                start_line = content[:match.start()].count('\n') + 1
                
                elements.append(CodeElement(
                    element_type='function',
                    name=func_name,
                    file_path=file_path,
                    start_line=start_line,
                    end_line=self._find_function_end(content, match.end()),
                    content=self._extract_function_body(content, match.start()),
                    signature=match.group(0),
                    dependencies=[],
                    metadata={'is_async': 'async' in match.group(0)}
                ))
        
        # Extract Express routes
        route_patterns = [
            r"(?:app|router)\.(get|post|put|patch|delete)\s*\(\s*['\"`]([^'\"`]+)['\"`]",
        ]
        
        for pattern in route_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                elements.append(CodeElement(
                    element_type='endpoint',
                    name=match.group(2),
                    file_path=file_path,
                    start_line=content[:match.start()].count('\n') + 1,
                    end_line=content[:match.end()].count('\n') + 1,
                    content=match.group(0),
                    signature=match.group(0),
                    dependencies=[],
                    metadata={
                        'method': match.group(1).upper(),
                        'framework': 'express'
                    }
                ))
        
        # Extract class definitions
        class_pattern = r'class\s+(\w+)(?:\s+extends\s+(\w+))?'
        for match in re.finditer(class_pattern, content):
            elements.append(CodeElement(
                element_type='class',
                name=match.group(1),
                file_path=file_path,
                start_line=content[:match.start()].count('\n') + 1,
                end_line=self._find_block_end(content, match.end()),
                content=self._extract_block(content, match.start()),
                signature=match.group(0),
                dependencies=[],
                metadata={'extends': match.group(2)}
            ))
        
        return elements
    
    def extract_dependencies(self, content: str) -> List[str]:
        deps = []
        
        # require statements
        require_pattern = r"require\s*\(\s*['\"]([^'\"]+)['\"]"
        deps.extend(re.findall(require_pattern, content))
        
        # import statements
        import_patterns = [
            r"import\s+.*\s+from\s+['\"]([^'\"]+)['\"]",
            r"import\s*['\"]([^'\"]+)['\"]",
        ]
        for pattern in import_patterns:
            deps.extend(re.findall(pattern, content))
        
        return deps
    
    def extract_api_calls(self, content: str) -> List[Dict]:
        calls = []
        
        # axios calls
        axios_patterns = [
            r"axios\.(get|post|put|patch|delete)\s*\(\s*['\"`]([^'\"`]+)['\"`]",
            r"axios\s*\(\s*\{\s*(?:[^}]*url\s*:\s*['\"`]([^'\"`]+)['\"`])?",
        ]
        
        # fetch calls
        fetch_pattern = r"fetch\s*\(\s*['\"`]([^'\"`]+)['\"`]"
        
        for pattern in axios_patterns:
            for match in re.finditer(pattern, content):
                calls.append({
                    'type': 'http',
                    'library': 'axios',
                    'url': match.group(2) if len(match.groups()) > 1 else match.group(1),
                    'line': content[:match.start()].count('\n') + 1
                })
        
        for match in re.finditer(fetch_pattern, content):
            calls.append({
                'type': 'http',
                'library': 'fetch',
                'url': match.group(1),
                'line': content[:match.start()].count('\n') + 1
            })
        
        return calls
    
    def extract_event_handlers(self, content: str) -> List[Dict]:
        handlers = []
        
        patterns = [
            # EventEmitter
            r"\.on\s*\(\s*['\"]([^'\"]+)['\"]",
            r"\.addListener\s*\(\s*['\"]([^'\"]+)['\"]",
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                handlers.append({
                    'event': match.group(1),
                    'line': content[:match.start()].count('\n') + 1
                })
        
        return handlers
    
    def extract_event_publishers(self, content: str) -> List[Dict]:
        publishers = []
        
        patterns = [
            r"\.emit\s*\(\s*['\"]([^'\"]+)['\"]",
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                publishers.append({
                    'event': match.group(1),
                    'line': content[:match.start()].count('\n') + 1
                })
        
        return publishers
    
    def _find_function_end(self, content: str, start_pos: int) -> int:
        return self._find_block_end(content, start_pos)
    
    def _find_block_end(self, content: str, start_pos: int) -> int:
        brace_count = 0
        started = False
        for i, char in enumerate(content[start_pos:], start_pos):
            if char == '{':
                brace_count += 1
                started = True
            elif char == '}':
                brace_count -= 1
            if started and brace_count == 0:
                return content[:i+1].count('\n') + 1
        return content.count('\n') + 1
    
    def _extract_function_body(self, content: str, start_pos: int) -> str:
        end_line = self._find_block_end(content, start_pos)
        lines = content.split('\n')
        start_line = content[:start_pos].count('\n')
        return '\n'.join(lines[start_line:end_line])
    
    def _extract_block(self, content: str, start_pos: int) -> str:
        return self._extract_function_body(content, start_pos)


class TypeScriptAnalyzer(JavaScriptAnalyzer):
    """Analyzer for TypeScript code (extends JavaScript analyzer)."""
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.ts', '.tsx']
    
    def extract_elements(self, content: str, file_path: str) -> List[CodeElement]:
        elements = super().extract_elements(content, file_path)
        
        # Extract interfaces
        interface_pattern = r'(?:export\s+)?interface\s+(\w+)(?:\s+extends\s+([^{]+))?'
        for match in re.finditer(interface_pattern, content):
            elements.append(CodeElement(
                element_type='interface',
                name=match.group(1),
                file_path=file_path,
                start_line=content[:match.start()].count('\n') + 1,
                end_line=self._find_block_end(content, match.end()),
                content=self._extract_block(content, match.start()),
                signature=match.group(0),
                dependencies=[],
                metadata={'extends': match.group(2).split(',') if match.group(2) else []}
            ))
        
        # Extract type aliases
        type_pattern = r'(?:export\s+)?type\s+(\w+)\s*=\s*([^;]+)'
        for match in re.finditer(type_pattern, content):
            elements.append(CodeElement(
                element_type='type',
                name=match.group(1),
                file_path=file_path,
                start_line=content[:match.start()].count('\n') + 1,
                end_line=content[:match.end()].count('\n') + 1,
                content=match.group(0),
                signature=match.group(0),
                dependencies=[],
                metadata={'definition': match.group(2)}
            ))
        
        return elements
```

#### NestJS Analyzer

```python
# pr_agent/tools/language_analyzers/nestjs_analyzer.py
import re
from typing import List, Dict
from .typescript_analyzer import TypeScriptAnalyzer
from .base_analyzer import CodeElement

class NestJSAnalyzer(TypeScriptAnalyzer):
    """Analyzer for NestJS applications."""
    
    def extract_elements(self, content: str, file_path: str) -> List[CodeElement]:
        elements = super().extract_elements(content, file_path)
        
        # Extract Controllers with routes
        controller_match = re.search(r"@Controller\s*\(\s*['\"]?([^'\")]*)['\"]?\s*\)", content)
        controller_prefix = controller_match.group(1) if controller_match else ''
        
        # Extract HTTP endpoints
        http_methods = ['Get', 'Post', 'Put', 'Patch', 'Delete']
        for method in http_methods:
            pattern = rf"@{method}\s*\(\s*['\"]?([^'\")]*)['\"]?\s*\)"
            for match in re.finditer(pattern, content):
                route = f"/{controller_prefix}/{match.group(1)}".replace('//', '/')
                # Find the method name after the decorator
                method_match = re.search(r'(?:async\s+)?(\w+)\s*\(', content[match.end():match.end()+200])
                method_name = method_match.group(1) if method_match else 'unknown'
                
                elements.append(CodeElement(
                    element_type='endpoint',
                    name=route,
                    file_path=file_path,
                    start_line=content[:match.start()].count('\n') + 1,
                    end_line=content[:match.end()].count('\n') + 1,
                    content=match.group(0),
                    signature=f"{method.upper()} {route}",
                    dependencies=[],
                    metadata={
                        'method': method.upper(),
                        'route': route,
                        'handler': method_name,
                        'framework': 'nestjs'
                    }
                ))
        
        # Extract Injectable services
        if '@Injectable' in content:
            service_pattern = r'@Injectable\s*\(\s*\)\s*(?:export\s+)?class\s+(\w+)'
            for match in re.finditer(service_pattern, content):
                elements.append(CodeElement(
                    element_type='service',
                    name=match.group(1),
                    file_path=file_path,
                    start_line=content[:match.start()].count('\n') + 1,
                    end_line=self._find_block_end(content, match.end()),
                    content=self._extract_block(content, match.start()),
                    signature=match.group(0),
                    dependencies=self._extract_di_dependencies(content),
                    metadata={'framework': 'nestjs'}
                ))
        
        # Extract DTOs
        dto_patterns = [
            r'(?:export\s+)?class\s+(\w+Dto)\b',
            r'(?:export\s+)?class\s+(\w+DTO)\b',
        ]
        for pattern in dto_patterns:
            for match in re.finditer(pattern, content):
                elements.append(CodeElement(
                    element_type='dto',
                    name=match.group(1),
                    file_path=file_path,
                    start_line=content[:match.start()].count('\n') + 1,
                    end_line=self._find_block_end(content, match.end()),
                    content=self._extract_block(content, match.start()),
                    signature=match.group(0),
                    dependencies=[],
                    metadata={'framework': 'nestjs'}
                ))
        
        return elements
    
    def extract_event_handlers(self, content: str) -> List[Dict]:
        handlers = super().extract_event_handlers(content)
        
        # PubSub handlers (Google Cloud PubSub)
        pubsub_patterns = [
            r"@PubSubTopic\s*\(\s*['\"]([^'\"]+)['\"]",
            r"@PubSubEvent\s*\(\s*['\"]([^'\"]+)['\"]",
            r"@EventPattern\s*\(\s*['\"]([^'\"]+)['\"]",
            r"@MessagePattern\s*\(\s*['\"]([^'\"]+)['\"]",
            r"@OnEvent\s*\(\s*['\"]([^'\"]+)['\"]",
        ]
        
        for pattern in pubsub_patterns:
            for match in re.finditer(pattern, content):
                handlers.append({
                    'event': match.group(1),
                    'type': 'pubsub' if 'PubSub' in pattern else 'event',
                    'line': content[:match.start()].count('\n') + 1,
                    'framework': 'nestjs'
                })
        
        return handlers
    
    def extract_event_publishers(self, content: str) -> List[Dict]:
        publishers = super().extract_event_publishers(content)
        
        # PubSub publishing patterns
        pubsub_patterns = [
            r"\.publish\s*\(\s*['\"]([^'\"]+)['\"]",
            r"eventEmitter\.emit\s*\(\s*['\"]([^'\"]+)['\"]",
            r"this\.client\.emit\s*\(\s*['\"]([^'\"]+)['\"]",
        ]
        
        for pattern in pubsub_patterns:
            for match in re.finditer(pattern, content):
                publishers.append({
                    'event': match.group(1),
                    'type': 'pubsub',
                    'line': content[:match.start()].count('\n') + 1,
                    'framework': 'nestjs'
                })
        
        return publishers
    
    def _extract_di_dependencies(self, content: str) -> List[str]:
        """Extract dependency injection from constructor."""
        deps = []
        constructor_pattern = r'constructor\s*\(([^)]+)\)'
        match = re.search(constructor_pattern, content)
        if match:
            params = match.group(1)
            # Extract type annotations
            type_pattern = r'(?:private|public|readonly)\s+\w+\s*:\s*(\w+)'
            deps = re.findall(type_pattern, params)
        return deps
```

#### React Analyzer

```python
# pr_agent/tools/language_analyzers/react_analyzer.py
import re
from typing import List, Dict
from .typescript_analyzer import TypeScriptAnalyzer
from .base_analyzer import CodeElement

class ReactAnalyzer(TypeScriptAnalyzer):
    """Analyzer for React/TypeScript applications."""
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.tsx', '.jsx']
    
    def extract_elements(self, content: str, file_path: str) -> List[CodeElement]:
        elements = super().extract_elements(content, file_path)
        
        # Extract React functional components
        component_patterns = [
            # const Component = () => { ... }
            r'(?:export\s+)?(?:const|function)\s+([A-Z]\w+)\s*(?::\s*React\.FC[^=]*)?=?\s*(?:\([^)]*\)\s*(?::\s*[^=]+)?)?=>',
            # function Component() { ... }
            r'(?:export\s+)?function\s+([A-Z]\w+)\s*\([^)]*\)',
        ]
        
        for pattern in component_patterns:
            for match in re.finditer(pattern, content):
                comp_name = match.group(1)
                # Skip if already captured as a regular function
                if not any(e.name == comp_name and e.element_type == 'component' for e in elements):
                    elements.append(CodeElement(
                        element_type='component',
                        name=comp_name,
                        file_path=file_path,
                        start_line=content[:match.start()].count('\n') + 1,
                        end_line=self._find_block_end(content, match.end()),
                        content=self._extract_block(content, match.start()),
                        signature=match.group(0),
                        dependencies=self._extract_component_deps(content, comp_name),
                        metadata={
                            'framework': 'react',
                            'type': 'functional'
                        }
                    ))
        
        # Extract custom hooks
        hook_pattern = r'(?:export\s+)?(?:const|function)\s+(use[A-Z]\w+)\s*'
        for match in re.finditer(hook_pattern, content):
            elements.append(CodeElement(
                element_type='hook',
                name=match.group(1),
                file_path=file_path,
                start_line=content[:match.start()].count('\n') + 1,
                end_line=self._find_block_end(content, match.end()),
                content=self._extract_block(content, match.start()),
                signature=match.group(0),
                dependencies=[],
                metadata={'framework': 'react'}
            ))
        
        # Extract Redux actions/reducers
        if 'createSlice' in content or 'createAction' in content:
            slice_pattern = r'createSlice\s*\(\s*\{\s*name\s*:\s*[\'"]([^\'"]+)[\'"]'
            for match in re.finditer(slice_pattern, content):
                elements.append(CodeElement(
                    element_type='redux_slice',
                    name=match.group(1),
                    file_path=file_path,
                    start_line=content[:match.start()].count('\n') + 1,
                    end_line=self._find_block_end(content, match.end()),
                    content=self._extract_block(content, match.start()),
                    signature=match.group(0),
                    dependencies=[],
                    metadata={'framework': 'redux'}
                ))
        
        # Extract Context providers
        context_pattern = r'(?:export\s+)?const\s+(\w+Context)\s*=\s*(?:React\.)?createContext'
        for match in re.finditer(context_pattern, content):
            elements.append(CodeElement(
                element_type='context',
                name=match.group(1),
                file_path=file_path,
                start_line=content[:match.start()].count('\n') + 1,
                end_line=content[:match.end()].count('\n') + 1,
                content=match.group(0),
                signature=match.group(0),
                dependencies=[],
                metadata={'framework': 'react'}
            ))
        
        return elements
    
    def extract_api_calls(self, content: str) -> List[Dict]:
        calls = super().extract_api_calls(content)
        
        # React Query / TanStack Query
        query_patterns = [
            r"useQuery\s*\(\s*\[[^\]]*\]\s*,\s*\(\s*\)\s*=>\s*(?:fetch|axios)[^)]*\(['\"`]([^'\"`]+)['\"`]",
            r"useMutation\s*\(\s*\(\s*\)\s*=>\s*(?:fetch|axios)[^)]*\(['\"`]([^'\"`]+)['\"`]",
        ]
        
        for pattern in query_patterns:
            for match in re.finditer(pattern, content):
                calls.append({
                    'type': 'http',
                    'library': 'react-query',
                    'url': match.group(1),
                    'line': content[:match.start()].count('\n') + 1
                })
        
        return calls
    
    def _extract_component_deps(self, content: str, comp_name: str) -> List[str]:
        """Extract component dependencies (props, hooks used)."""
        deps = []
        
        # Find hooks used in component
        hook_pattern = r'\buse[A-Z]\w+\b'
        deps.extend(set(re.findall(hook_pattern, content)))
        
        return deps
```

#### Python Analyzer

```python
# pr_agent/tools/language_analyzers/python_analyzer.py
import re
from typing import List, Dict
from .base_analyzer import BaseLanguageAnalyzer, CodeElement

class PythonAnalyzer(BaseLanguageAnalyzer):
    """Analyzer for Python code (FastAPI, Django, Flask, plain Python)."""
    
    @property
    def supported_extensions(self) -> List[str]:
        return ['.py']
    
    def extract_elements(self, content: str, file_path: str) -> List[CodeElement]:
        elements = []
        lines = content.split('\n')
        
        # Extract classes
        class_pattern = r'^class\s+(\w+)(?:\(([^)]*)\))?:'
        for match in re.finditer(class_pattern, content, re.MULTILINE):
            class_name = match.group(1)
            start_line = content[:match.start()].count('\n') + 1
            end_line = self._find_block_end_python(lines, start_line)
            
            elements.append(CodeElement(
                element_type='class',
                name=class_name,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                content='\n'.join(lines[start_line-1:end_line]),
                signature=match.group(0),
                dependencies=self._extract_class_dependencies(match.group(2) or ''),
                metadata={
                    'bases': [b.strip() for b in (match.group(2) or '').split(',') if b.strip()]
                }
            ))
        
        # Extract functions/methods
        func_pattern = r'^(\s*)(?:async\s+)?def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?:'
        for match in re.finditer(func_pattern, content, re.MULTILINE):
            indent = len(match.group(1))
            func_name = match.group(2)
            start_line = content[:match.start()].count('\n') + 1
            end_line = self._find_function_end_python(lines, start_line, indent)
            
            elements.append(CodeElement(
                element_type='function' if indent == 0 else 'method',
                name=func_name,
                file_path=file_path,
                start_line=start_line,
                end_line=end_line,
                content='\n'.join(lines[start_line-1:end_line]),
                signature=match.group(0).strip(),
                dependencies=[],
                metadata={
                    'is_async': 'async' in match.group(0),
                    'params': match.group(3),
                    'return_type': match.group(4).strip() if match.group(4) else None
                }
            ))
        
        # Extract FastAPI endpoints
        fastapi_patterns = [
            r'@app\.(get|post|put|patch|delete)\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'@router\.(get|post|put|patch|delete)\s*\(\s*[\'"]([^\'"]+)[\'"]',
        ]
        for pattern in fastapi_patterns:
            for match in re.finditer(pattern, content):
                elements.append(CodeElement(
                    element_type='endpoint',
                    name=match.group(2),
                    file_path=file_path,
                    start_line=content[:match.start()].count('\n') + 1,
                    end_line=content[:match.end()].count('\n') + 1,
                    content=match.group(0),
                    signature=f"{match.group(1).upper()} {match.group(2)}",
                    dependencies=[],
                    metadata={
                        'method': match.group(1).upper(),
                        'framework': 'fastapi'
                    }
                ))
        
        # Extract Django views
        django_patterns = [
            r'path\s*\(\s*[\'"]([^\'"]+)[\'"]',
            r'@api_view\s*\(\s*\[([^\]]+)\]\s*\)',
        ]
        for pattern in django_patterns:
            for match in re.finditer(pattern, content):
                elements.append(CodeElement(
                    element_type='endpoint',
                    name=match.group(1),
                    file_path=file_path,
                    start_line=content[:match.start()].count('\n') + 1,
                    end_line=content[:match.end()].count('\n') + 1,
                    content=match.group(0),
                    signature=match.group(0),
                    dependencies=[],
                    metadata={'framework': 'django'}
                ))
        
        return elements
    
    def extract_dependencies(self, content: str) -> List[str]:
        """Extract import statements."""
        deps = []
        
        # import statements
        import_pattern = r'^import\s+(\S+)'
        deps.extend(re.findall(import_pattern, content, re.MULTILINE))
        
        # from ... import statements
        from_pattern = r'^from\s+(\S+)\s+import'
        deps.extend(re.findall(from_pattern, content, re.MULTILINE))
        
        return deps
    
    def extract_api_calls(self, content: str) -> List[Dict]:
        """Extract HTTP client calls (requests, httpx, aiohttp)."""
        calls = []
        
        # requests/httpx calls
        patterns = [
            r"requests\.(get|post|put|patch|delete)\s*\(\s*['\"`]([^'\"`]+)['\"`]",
            r"httpx\.(get|post|put|patch|delete)\s*\(\s*['\"`]([^'\"`]+)['\"`]",
            r"await\s+client\.(get|post|put|patch|delete)\s*\(\s*['\"`]([^'\"`]+)['\"`]",
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                calls.append({
                    'type': 'http',
                    'method': match.group(1).upper(),
                    'url': match.group(2),
                    'line': content[:match.start()].count('\n') + 1
                })
        
        return calls
    
    def extract_event_handlers(self, content: str) -> List[Dict]:
        """Extract event handlers (Celery tasks, etc.)."""
        handlers = []
        
        patterns = [
            r"@celery\.task",
            r"@app\.task",
            r"@shared_task",
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                handlers.append({
                    'type': 'celery_task',
                    'line': content[:match.start()].count('\n') + 1
                })
        
        return handlers
    
    def extract_event_publishers(self, content: str) -> List[Dict]:
        """Extract event publishing (Celery task calls, etc.)."""
        publishers = []
        
        patterns = [
            r"\.delay\s*\(",
            r"\.apply_async\s*\(",
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                publishers.append({
                    'type': 'celery_task_call',
                    'line': content[:match.start()].count('\n') + 1
                })
        
        return publishers
    
    def _find_block_end_python(self, lines: List[str], start_line: int) -> int:
        """Find end of Python block by indentation."""
        if start_line >= len(lines):
            return start_line
        
        start_indent = len(lines[start_line - 1]) - len(lines[start_line - 1].lstrip())
        
        for i in range(start_line, len(lines)):
            line = lines[i]
            if line.strip() and not line.strip().startswith('#'):
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= start_indent and i > start_line:
                    return i
        
        return len(lines)
    
    def _find_function_end_python(self, lines: List[str], start_line: int, func_indent: int) -> int:
        """Find end of Python function by indentation."""
        for i in range(start_line, len(lines)):
            line = lines[i]
            if line.strip() and not line.strip().startswith('#'):
                current_indent = len(line) - len(line.lstrip())
                if current_indent <= func_indent and i > start_line:
                    return i
        return len(lines)
    
    def _extract_class_dependencies(self, bases_str: str) -> List[str]:
        """Extract base classes as dependencies."""
        if not bases_str:
            return []
        return [b.strip() for b in bases_str.split(',') if b.strip()]
```

#### Analyzer Factory

```python
# pr_agent/tools/language_analyzers/__init__.py
from typing import Optional
from .base_analyzer import BaseLanguageAnalyzer, CodeElement
from .php_analyzer import PHPAnalyzer
from .javascript_analyzer import JavaScriptAnalyzer, TypeScriptAnalyzer
from .nestjs_analyzer import NestJSAnalyzer
from .react_analyzer import ReactAnalyzer
from .python_analyzer import PythonAnalyzer

class AnalyzerFactory:
    """Factory to get appropriate analyzer for a file."""
    
    _analyzers = {
        '.php': PHPAnalyzer,
        '.js': JavaScriptAnalyzer,
        '.mjs': JavaScriptAnalyzer,
        '.cjs': JavaScriptAnalyzer,
        '.ts': TypeScriptAnalyzer,
        '.tsx': ReactAnalyzer,
        '.jsx': ReactAnalyzer,
        '.py': PythonAnalyzer,
    }
    
    @classmethod
    def get_analyzer(cls, file_path: str) -> Optional[BaseLanguageAnalyzer]:
        """Get appropriate analyzer based on file extension."""
        import os
        ext = os.path.splitext(file_path)[1].lower()
        
        # Special case: detect NestJS by file naming convention
        if ext in ['.ts'] and any(pattern in file_path for pattern in [
            '.controller.', '.service.', '.module.', '.guard.', '.dto.'
        ]):
            return NestJSAnalyzer()
        
        analyzer_class = cls._analyzers.get(ext)
        return analyzer_class() if analyzer_class else None
    
    @classmethod
    def analyze_file(cls, content: str, file_path: str) -> list[CodeElement]:
        """Analyze a file and return code elements."""
        analyzer = cls.get_analyzer(file_path)
        if analyzer:
            return analyzer.extract_elements(content, file_path)
        return []
```

---

## Database Queries Support (MySQL, MongoDB, Elasticsearch)

### Enhanced SQL Analyzer with MySQL Specifics

Update: `pr_agent/tools/sql_analyzer.py`

```python
# Add to sql_analyzer.py

class MySQLAnalyzer(SQLAnalyzer):
    """MySQL-specific query analyzer."""
    
    def _check_mysql_specifics(self, query: str, line: int) -> List[SQLIssue]:
        issues = []
        query_upper = query.upper()
        
        # Check for MySQL-specific issues
        
        # Using LIMIT without ORDER BY
        if 'LIMIT' in query_upper and 'ORDER BY' not in query_upper:
            issues.append(SQLIssue(
                query=query,
                issue_type='mysql_specific',
                message="LIMIT without ORDER BY may return inconsistent results",
                severity='warning',
                line_number=line,
                suggestion="Add ORDER BY clause for deterministic results"
            ))
        
        # Check for inefficient GROUP BY
        if 'GROUP BY' in query_upper and 'ONLY_FULL_GROUP_BY' not in query_upper:
            # Check if selecting columns not in GROUP BY
            pass
        
        # Check for missing indexes on JOIN conditions
        if 'JOIN' in query_upper and 'ON' in query_upper:
            issues.append(SQLIssue(
                query=query,
                issue_type='mysql_performance',
                message="Verify indexes exist on JOIN columns",
                severity='info',
                line_number=line,
                suggestion="Run EXPLAIN to verify query execution plan"
            ))
        
        # Check for deprecated MySQL syntax
        deprecated = [
            ('SQL_CALC_FOUND_ROWS', 'Use COUNT(*) in a separate query'),
            ('FOUND_ROWS()', 'Use COUNT(*) in a separate query'),
        ]
        for deprecated_syntax, suggestion in deprecated:
            if deprecated_syntax in query_upper:
                issues.append(SQLIssue(
                    query=query,
                    issue_type='deprecated',
                    message=f"{deprecated_syntax} is deprecated in MySQL 8.0",
                    severity='warning',
                    line_number=line,
                    suggestion=suggestion
                ))
        
        return issues


class MongoDBAnalyzer:
    """Analyzer for MongoDB queries."""
    
    def analyze_file(self, content: str, file_path: str) -> List[Dict]:
        """Extract and analyze MongoDB operations."""
        issues = []
        
        # Extract MongoDB operations
        mongo_patterns = [
            # Find operations
            (r'\.find\s*\(\s*(\{[^}]*\})', 'find'),
            (r'\.findOne\s*\(\s*(\{[^}]*\})', 'findOne'),
            # Aggregation
            (r'\.aggregate\s*\(\s*(\[[^\]]*\])', 'aggregate'),
            # Updates
            (r'\.updateOne\s*\(\s*(\{[^}]*\})\s*,\s*(\{[^}]*\})', 'updateOne'),
            (r'\.updateMany\s*\(\s*(\{[^}]*\})\s*,\s*(\{[^}]*\})', 'updateMany'),
            # Inserts
            (r'\.insertOne\s*\(\s*(\{[^}]*\})', 'insertOne'),
            (r'\.insertMany\s*\(\s*(\[[^\]]*\])', 'insertMany'),
        ]
        
        for pattern, operation in mongo_patterns:
            for match in re.finditer(pattern, content, re.DOTALL):
                query = match.group(1)
                line = content[:match.start()].count('\n') + 1
                issues.extend(self._analyze_mongo_query(query, operation, line))
        
        return issues
    
    def _analyze_mongo_query(self, query: str, operation: str, line: int) -> List[Dict]:
        issues = []
        
        # Check for queries without indexes (no _id, no indexed fields)
        if operation in ['find', 'findOne'] and '_id' not in query:
            issues.append({
                'type': 'mongodb_performance',
                'message': f'Query may not use index efficiently',
                'severity': 'info',
                'line': line,
                'suggestion': 'Ensure query fields are indexed'
            })
        
        # Check for $regex without anchors (performance issue)
        if '$regex' in query and '^' not in query:
            issues.append({
                'type': 'mongodb_performance',
                'message': '$regex without ^ anchor cannot use indexes',
                'severity': 'warning',
                'line': line,
                'suggestion': 'Use anchored regex when possible: /^pattern/'
            })
        
        # Check for large $in arrays
        if '$in' in query:
            issues.append({
                'type': 'mongodb_performance',
                'message': 'Large $in arrays can cause performance issues',
                'severity': 'info',
                'line': line,
                'suggestion': 'Consider batching if array is large'
            })
        
        # Check for updates without $set
        if operation in ['updateOne', 'updateMany'] and '$set' not in query and '$' in query:
            pass  # Ok, using another update operator
        elif operation in ['updateOne', 'updateMany'] and '$' not in query:
            issues.append({
                'type': 'mongodb_warning',
                'message': 'Update without operators will replace entire document',
                'severity': 'warning',
                'line': line,
                'suggestion': 'Use $set or other update operators'
            })
        
        return issues


class ElasticsearchAnalyzer:
    """Analyzer for Elasticsearch queries."""
    
    def analyze_file(self, content: str, file_path: str) -> List[Dict]:
        issues = []
        
        # Extract Elasticsearch operations
        es_patterns = [
            (r'\.search\s*\(\s*(\{[^}]*\})', 'search'),
            (r'\.index\s*\(\s*(\{[^}]*\})', 'index'),
            (r'\.update\s*\(\s*(\{[^}]*\})', 'update'),
            (r'\.bulk\s*\(\s*(\[[^\]]*\])', 'bulk'),
        ]
        
        for pattern, operation in es_patterns:
            for match in re.finditer(pattern, content, re.DOTALL):
                query = match.group(1)
                line = content[:match.start()].count('\n') + 1
                issues.extend(self._analyze_es_query(query, operation, line))
        
        return issues
    
    def _analyze_es_query(self, query: str, operation: str, line: int) -> List[Dict]:
        issues = []
        
        # Check for wildcard queries
        if 'wildcard' in query.lower():
            issues.append({
                'type': 'elasticsearch_performance',
                'message': 'Wildcard queries can be slow',
                'severity': 'warning',
                'line': line,
                'suggestion': 'Consider using prefix queries or ngrams'
            })
        
        # Check for script queries
        if 'script' in query.lower():
            issues.append({
                'type': 'elasticsearch_performance',
                'message': 'Script queries cannot be cached and may be slow',
                'severity': 'warning',
                'line': line,
                'suggestion': 'Consider using runtime fields or pre-computed values'
            })
        
        # Check for deep pagination
        if '"from"' in query and '"size"' in query:
            issues.append({
                'type': 'elasticsearch_performance',
                'message': 'Deep pagination (from + size > 10000) is inefficient',
                'severity': 'info',
                'line': line,
                'suggestion': 'Use search_after for deep pagination'
            })
        
        return issues
```

---

## PubSub Events System

### Google Cloud PubSub Analyzer

Create: `pr_agent/tools/pubsub_analyzer.py`

```python
import re
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class PubSubEvent:
    topic: str
    event_type: str  # 'publish' or 'subscribe'
    file_path: str
    line_number: int
    handler_name: str
    message_schema: str  # DTO class if detected

class PubSubAnalyzer:
    """Analyzer for Google Cloud PubSub patterns."""
    
    def extract_pubsub_topology(self, content: str, file_path: str) -> List[PubSubEvent]:
        """Extract PubSub publishers and subscribers from code."""
        events = []
        
        # NestJS PubSub decorators
        subscriber_patterns = [
            # @PubSubTopic('TOPIC_ENV_VAR', METADATA)
            (r"@PubSubTopic\s*\(\s*['\"]([^'\"]+)['\"]", 'subscribe'),
            # @PubSubEvent('EVENT_ENV_VAR', METADATA)
            (r"@PubSubEvent\s*\(\s*['\"]([^'\"]+)['\"]", 'subscribe'),
            # @EventPattern('topic')
            (r"@EventPattern\s*\(\s*['\"]([^'\"]+)['\"]", 'subscribe'),
        ]
        
        publisher_patterns = [
            # pubsub.publish('topic', message)
            (r"\.publish\s*\(\s*['\"]([^'\"]+)['\"]", 'publish'),
            # client.emit('topic', message)
            (r"\.emit\s*\(\s*['\"]([^'\"]+)['\"]", 'publish'),
            # pubSubClient.topic('topic').publish()
            (r"\.topic\s*\(\s*['\"]([^'\"]+)['\"]", 'publish'),
        ]
        
        for pattern, event_type in subscriber_patterns + publisher_patterns:
            for match in re.finditer(pattern, content):
                line_num = content[:match.start()].count('\n') + 1
                handler_name = self._find_handler_name(content, match.end())
                message_schema = self._find_message_schema(content, match.end())
                
                events.append(PubSubEvent(
                    topic=match.group(1),
                    event_type=event_type,
                    file_path=file_path,
                    line_number=line_num,
                    handler_name=handler_name,
                    message_schema=message_schema
                ))
        
        return events
    
    def _find_handler_name(self, content: str, position: int) -> str:
        """Find the function/method name handling the event."""
        # Look for function definition after the decorator
        search_area = content[position:position+500]
        func_match = re.search(r'(?:async\s+)?(\w+)\s*\(', search_area)
        return func_match.group(1) if func_match else 'unknown'
    
    def _find_message_schema(self, content: str, position: int) -> str:
        """Find the DTO/schema used for the message."""
        search_area = content[position:position+500]
        # Look for type annotation or decorator parameter
        dto_patterns = [
            r'@PubSubPayload\s*\(\s*(\w+)\s*\)',
            r'message\s*:\s*(\w+Dto)',
            r'data\s*:\s*(\w+)',
        ]
        for pattern in dto_patterns:
            match = re.search(pattern, search_area)
            if match:
                return match.group(1)
        return ''
    
    def analyze_pubsub_consistency(
        self, 
        publishers: List[PubSubEvent],
        subscribers: List[PubSubEvent]
    ) -> List[Dict]:
        """Analyze PubSub topology for issues."""
        issues = []
        
        publisher_topics = {p.topic for p in publishers}
        subscriber_topics = {s.topic for s in subscribers}
        
        # Topics with no subscribers
        orphan_publishers = publisher_topics - subscriber_topics
        for topic in orphan_publishers:
            issues.append({
                'type': 'pubsub_topology',
                'severity': 'warning',
                'message': f"Topic '{topic}' has publishers but no subscribers found",
                'suggestion': 'Verify subscriber exists or remove unused publisher'
            })
        
        # Subscribers without publishers
        orphan_subscribers = subscriber_topics - publisher_topics
        for topic in orphan_subscribers:
            issues.append({
                'type': 'pubsub_topology',
                'severity': 'info',
                'message': f"Topic '{topic}' has subscribers but no publishers found in indexed repos",
                'suggestion': 'Publisher may be external or in unindexed repo'
            })
        
        return issues
```

---

## Initial Data Population and Continuous Updates

### Repository Indexing Service

Create: `pr_agent/services/indexing_service.py`

```python
import asyncio
import os
import tempfile
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass
import git

from pr_agent.tools.language_analyzers import AnalyzerFactory
from pr_agent.tools.pubsub_analyzer import PubSubAnalyzer
from pr_agent.db.connection import DatabaseManager
from pr_agent.log import get_logger

@dataclass
class IndexingJob:
    repository_url: str
    branch: str
    job_type: str  # 'full' or 'incremental'
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = 'pending'
    error: Optional[str] = None
    stats: Dict = None

class RepositoryIndexingService:
    """Service for initial and incremental repository indexing."""
    
    def __init__(self, db: DatabaseManager, github_token: str, embedding_handler):
        self.db = db
        self.github_token = github_token
        self.embedder = embedding_handler
        self.pubsub_analyzer = PubSubAnalyzer()
    
    async def index_all_repositories(self, repo_urls: List[str]) -> List[IndexingJob]:
        """Initial full indexing of all repositories."""
        jobs = []
        
        for repo_url in repo_urls:
            job = await self.index_repository(repo_url, job_type='full')
            jobs.append(job)
        
        return jobs
    
    async def index_repository(
        self, 
        repo_url: str, 
        branch: str = 'main',
        job_type: str = 'full'
    ) -> IndexingJob:
        """Index a single repository."""
        job = IndexingJob(
            repository_url=repo_url,
            branch=branch,
            job_type=job_type,
            started_at=datetime.now()
        )
        
        try:
            get_logger().info(f"Starting {job_type} indexing for {repo_url}")
            
            # Clone repository to temp directory
            with tempfile.TemporaryDirectory() as temp_dir:
                repo = await self._clone_repository(repo_url, temp_dir, branch)
                
                # Get or create repository record
                repo_id = await self._get_or_create_repo(repo_url)
                
                # Get last indexed commit for incremental
                last_commit = None
                if job_type == 'incremental':
                    last_commit = await self._get_last_indexed_commit(repo_id)
                
                # Process all files
                stats = await self._process_repository_files(
                    repo, 
                    temp_dir, 
                    repo_id,
                    last_commit
                )
                
                # Update repository metadata
                await self._update_repository_metadata(repo_id, repo.head.commit.hexsha)
                
                job.completed_at = datetime.now()
                job.status = 'completed'
                job.stats = stats
                
                get_logger().info(f"Completed indexing {repo_url}: {stats}")
        
        except Exception as e:
            job.status = 'failed'
            job.error = str(e)
            get_logger().error(f"Failed to index {repo_url}: {e}")
        
        return job
    
    async def _clone_repository(
        self, 
        repo_url: str, 
        target_dir: str,
        branch: str
    ) -> git.Repo:
        """Clone repository with authentication."""
        # Parse URL and add token
        if 'github.com' in repo_url:
            auth_url = repo_url.replace(
                'https://github.com',
                f'https://{self.github_token}@github.com'
            )
        else:
            auth_url = repo_url
        
        # Clone with shallow history for speed
        repo = git.Repo.clone_from(
            auth_url,
            target_dir,
            branch=branch,
            depth=1  # Shallow clone for indexing
        )
        
        return repo
    
    async def _process_repository_files(
        self,
        repo: git.Repo,
        repo_path: str,
        repo_id: int,
        since_commit: Optional[str] = None
    ) -> Dict:
        """Process all files in repository."""
        stats = {
            'files_processed': 0,
            'elements_indexed': 0,
            'pubsub_events': 0,
            'api_calls': 0,
            'errors': 0
        }
        
        # Determine files to process
        if since_commit:
            # Get changed files since last index
            files_to_process = self._get_changed_files(repo, since_commit)
        else:
            # Get all files
            files_to_process = self._get_all_files(repo_path)
        
        # Process in batches for embeddings
        batch_size = 50
        elements_batch = []
        
        for file_path in files_to_process:
            try:
                full_path = os.path.join(repo_path, file_path)
                if not os.path.exists(full_path):
                    continue
                
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Extract code elements
                elements = AnalyzerFactory.analyze_file(content, file_path)
                
                # Extract PubSub events
                pubsub_events = self.pubsub_analyzer.extract_pubsub_topology(content, file_path)
                
                # Extract API calls
                analyzer = AnalyzerFactory.get_analyzer(file_path)
                api_calls = analyzer.extract_api_calls(content) if analyzer else []
                
                # Prepare for batch embedding
                for element in elements:
                    elements_batch.append({
                        'repo_id': repo_id,
                        'element': element,
                        'content_for_embedding': f"{element.element_type}: {element.name}\n{element.content[:2000]}"
                    })
                
                stats['files_processed'] += 1
                stats['elements_indexed'] += len(elements)
                stats['pubsub_events'] += len(pubsub_events)
                stats['api_calls'] += len(api_calls)
                
                # Process batch
                if len(elements_batch) >= batch_size:
                    await self._store_elements_batch(elements_batch)
                    elements_batch = []
            
            except Exception as e:
                stats['errors'] += 1
                get_logger().warning(f"Error processing {file_path}: {e}")
        
        # Store remaining elements
        if elements_batch:
            await self._store_elements_batch(elements_batch)
        
        # Extract and store cursor rules
        await self._process_cursor_rules(repo_path, repo_id)
    
    async def _process_cursor_rules(self, repo_path: str, repo_id: int) -> None:
        """Extract and store cursor rules from repository."""
        from pr_agent.tools.cursor_rules_loader import CursorRulesLoader
        
        loader = CursorRulesLoader()
        rules = await loader.load_rules_from_repo(repo_path)
        
        if not rules:
            return
        
        async with self.db.connection() as conn:
            # Clear existing rules for this repo
            await conn.execute(
                "DELETE FROM cursor_rules WHERE repository_id = $1",
                repo_id
            )
            
            # Insert new rules
            for rule in rules:
                await conn.execute("""
                    INSERT INTO cursor_rules 
                    (repository_id, source_file, category, rule_text, applies_to)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT DO NOTHING
                """, repo_id, rule.source_file, rule.category, 
                    rule.rule_text, rule.applies_to)
        
        return stats
    
    async def _store_elements_batch(self, elements_batch: List[Dict]) -> None:
        """Generate embeddings and store batch of elements."""
        if not elements_batch:
            return
        
        # Generate embeddings in batch
        texts = [e['content_for_embedding'] for e in elements_batch]
        embeddings = await self._generate_embeddings_batch(texts)
        
        # Store in database
        async with self.db.connection() as conn:
            for i, item in enumerate(elements_batch):
                element = item['element']
                embedding = embeddings[i] if i < len(embeddings) else None
                
                await conn.execute("""
                    INSERT INTO code_chunks 
                    (repository_id, file_path, chunk_content, chunk_type, 
                     start_line, end_line, embedding, metadata, commit_sha)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (repository_id, file_path, start_line) 
                    DO UPDATE SET 
                        chunk_content = EXCLUDED.chunk_content,
                        embedding = EXCLUDED.embedding,
                        metadata = EXCLUDED.metadata,
                        last_updated = CURRENT_TIMESTAMP
                """,
                    item['repo_id'],
                    element.file_path,
                    element.content,
                    element.element_type,
                    element.start_line,
                    element.end_line,
                    embedding,
                    element.metadata,
                    None  # commit_sha would come from repo
                )
    
    async def _generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        import openai
        
        # OpenAI batch embedding
        response = await openai.Embedding.acreate(
            input=texts,
            model="text-embedding-ada-002"
        )
        
        return [item['embedding'] for item in response['data']]
    
    def _get_all_files(self, repo_path: str) -> List[str]:
        """Get all supported files in repository."""
        supported_extensions = {'.php', '.js', '.ts', '.tsx', '.jsx', '.mjs'}
        files = []
        
        for root, dirs, filenames in os.walk(repo_path):
            # Skip common non-code directories
            dirs[:] = [d for d in dirs if d not in {
                'node_modules', 'vendor', '.git', 'dist', 'build', 
                '__pycache__', '.next', 'coverage'
            }]
            
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext in supported_extensions:
                    rel_path = os.path.relpath(
                        os.path.join(root, filename), 
                        repo_path
                    )
                    files.append(rel_path)
        
        return files
    
    def _get_changed_files(self, repo: git.Repo, since_commit: str) -> List[str]:
        """Get files changed since a specific commit."""
        try:
            diff = repo.git.diff('--name-only', since_commit, 'HEAD')
            return diff.split('\n') if diff else []
        except git.GitCommandError:
            # If commit not found, return all files
            return self._get_all_files(repo.working_dir)
    
    async def _get_or_create_repo(self, repo_url: str) -> int:
        """Get or create repository record."""
        # Parse org and repo name from URL
        parts = repo_url.rstrip('/').split('/')
        repo_name = parts[-1].replace('.git', '')
        org_name = parts[-2]
        
        async with self.db.connection() as conn:
            row = await conn.fetchrow("""
                INSERT INTO repositories (org_name, repo_name, github_url)
                VALUES ($1, $2, $3)
                ON CONFLICT (org_name, repo_name) 
                DO UPDATE SET github_url = EXCLUDED.github_url
                RETURNING id
            """, org_name, repo_name, repo_url)
            
            return row['id']
    
    async def _get_last_indexed_commit(self, repo_id: int) -> Optional[str]:
        """Get last indexed commit SHA."""
        async with self.db.connection() as conn:
            row = await conn.fetchrow("""
                SELECT commit_sha FROM code_chunks 
                WHERE repository_id = $1 
                ORDER BY last_updated DESC 
                LIMIT 1
            """, repo_id)
            
            return row['commit_sha'] if row else None
    
    async def _update_repository_metadata(self, repo_id: int, commit_sha: str) -> None:
        """Update repository last indexed timestamp."""
        async with self.db.connection() as conn:
            await conn.execute("""
                UPDATE repositories 
                SET last_indexed_at = CURRENT_TIMESTAMP
                WHERE id = $1
            """, repo_id)


class IncrementalUpdateService:
    """Service for handling incremental updates from webhooks."""
    
    def __init__(self, indexing_service: RepositoryIndexingService):
        self.indexing_service = indexing_service
    
    async def handle_push_webhook(self, payload: Dict) -> None:
        """Handle GitHub push webhook for incremental indexing."""
        repo_url = payload['repository']['clone_url']
        branch = payload['ref'].split('/')[-1]
        before_sha = payload['before']
        
        # Only index main/master branches
        if branch not in ['main', 'master', 'develop']:
            return
        
        # Queue incremental indexing job
        await self.indexing_service.index_repository(
            repo_url=repo_url,
            branch=branch,
            job_type='incremental'
        )
    
    async def handle_pr_merged_webhook(self, payload: Dict) -> None:
        """Handle PR merged webhook."""
        if payload['action'] != 'closed' or not payload['pull_request']['merged']:
            return
        
        repo_url = payload['repository']['clone_url']
        target_branch = payload['pull_request']['base']['ref']
        
        await self.indexing_service.index_repository(
            repo_url=repo_url,
            branch=target_branch,
            job_type='incremental'
        )
```

### Jira Synchronization Service

Create: `pr_agent/services/jira_sync_service.py`

```python
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pr_agent.integrations.jira_client import JiraClient
from pr_agent.db.connection import DatabaseManager
from pr_agent.log import get_logger

class JiraSyncService:
    """Service for Jira data synchronization."""
    
    def __init__(
        self, 
        jira_client: JiraClient, 
        db: DatabaseManager,
        embedding_handler
    ):
        self.jira = jira_client
        self.db = db
        self.embedder = embedding_handler
    
    async def full_sync(self, project_keys: List[str]) -> Dict:
        """Full synchronization of Jira tickets."""
        stats = {
            'projects': len(project_keys),
            'tickets_synced': 0,
            'errors': 0
        }
        
        for project_key in project_keys:
            try:
                get_logger().info(f"Syncing Jira project: {project_key}")
                count = await self._sync_project(project_key)
                stats['tickets_synced'] += count
            except Exception as e:
                stats['errors'] += 1
                get_logger().error(f"Error syncing project {project_key}: {e}")
        
        return stats
    
    async def _sync_project(self, project_key: str, since: Optional[datetime] = None) -> int:
        """Sync all tickets from a Jira project."""
        count = 0
        start_at = 0
        max_results = 100
        
        # Build JQL query
        jql = f'project = {project_key}'
        if since:
            since_str = since.strftime('%Y-%m-%d %H:%M')
            jql += f' AND updated >= "{since_str}"'
        
        while True:
            issues = self.jira.jira.search_issues(
                jql,
                startAt=start_at,
                maxResults=max_results,
                expand='changelog'
            )
            
            if not issues:
                break
            
            # Process in batches
            tickets_batch = []
            for issue in issues:
                ticket_data = self._extract_ticket_data(issue)
                tickets_batch.append(ticket_data)
            
            # Generate embeddings and store
            await self._store_tickets_batch(tickets_batch)
            
            count += len(issues)
            start_at += max_results
            
            if len(issues) < max_results:
                break
        
        return count
    
    def _extract_ticket_data(self, issue) -> Dict:
        """Extract relevant data from Jira issue."""
        return {
            'ticket_key': issue.key,
            'title': issue.fields.summary,
            'description': issue.fields.description or '',
            'status': issue.fields.status.name,
            'ticket_type': issue.fields.issuetype.name,
            'labels': [label for label in issue.fields.labels],
            'acceptance_criteria': self._get_acceptance_criteria(issue),
            'created': issue.fields.created,
            'updated': issue.fields.updated,
            'assignee': issue.fields.assignee.displayName if issue.fields.assignee else None,
            'reporter': issue.fields.reporter.displayName if issue.fields.reporter else None,
            'resolution': issue.fields.resolution.name if issue.fields.resolution else None,
        }
    
    def _get_acceptance_criteria(self, issue) -> str:
        """Extract acceptance criteria from custom fields."""
        custom_field_names = ['customfield_10001', 'customfield_10002', 'acceptance_criteria']
        for field_name in custom_field_names:
            if hasattr(issue.fields, field_name):
                value = getattr(issue.fields, field_name)
                if value:
                    return value
        return ''
    
    async def _store_tickets_batch(self, tickets: List[Dict]) -> None:
        """Generate embeddings and store tickets."""
        # Create embedding text for each ticket
        texts = [
            f"{t['ticket_key']}: {t['title']}\n{t['description'][:2000]}"
            for t in tickets
        ]
        
        # Generate embeddings
        embeddings = await self._generate_embeddings_batch(texts)
        
        # Store in database
        async with self.db.connection() as conn:
            for i, ticket in enumerate(tickets):
                embedding = embeddings[i] if i < len(embeddings) else None
                
                await conn.execute("""
                    INSERT INTO jira_tickets 
                    (ticket_key, title, description, status, ticket_type,
                     acceptance_criteria, labels, embedding, raw_data, last_synced)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, CURRENT_TIMESTAMP)
                    ON CONFLICT (ticket_key) 
                    DO UPDATE SET 
                        title = EXCLUDED.title,
                        description = EXCLUDED.description,
                        status = EXCLUDED.status,
                        ticket_type = EXCLUDED.ticket_type,
                        acceptance_criteria = EXCLUDED.acceptance_criteria,
                        labels = EXCLUDED.labels,
                        embedding = EXCLUDED.embedding,
                        raw_data = EXCLUDED.raw_data,
                        last_synced = CURRENT_TIMESTAMP
                """,
                    ticket['ticket_key'],
                    ticket['title'],
                    ticket['description'],
                    ticket['status'],
                    ticket['ticket_type'],
                    ticket['acceptance_criteria'],
                    ticket['labels'],
                    embedding,
                    ticket
                )
    
    async def _generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for batch of texts."""
        import openai
        
        response = await openai.Embedding.acreate(
            input=texts,
            model="text-embedding-ada-002"
        )
        
        return [item['embedding'] for item in response['data']]
    
    async def incremental_sync(self, project_keys: List[str]) -> Dict:
        """Incremental sync of recently updated tickets."""
        since = datetime.now() - timedelta(hours=24)
        stats = {'tickets_synced': 0, 'errors': 0}
        
        for project_key in project_keys:
            try:
                count = await self._sync_project(project_key, since=since)
                stats['tickets_synced'] += count
            except Exception as e:
                stats['errors'] += 1
                get_logger().error(f"Error in incremental sync for {project_key}: {e}")
        
        return stats


class SyncScheduler:
    """Scheduler for periodic sync jobs."""
    
    def __init__(
        self,
        indexing_service: RepositoryIndexingService,
        jira_sync_service: JiraSyncService
    ):
        self.indexing_service = indexing_service
        self.jira_sync_service = jira_sync_service
        self._running = False
    
    async def start(self, repo_urls: List[str], jira_projects: List[str]) -> None:
        """Start the sync scheduler."""
        self._running = True
        
        # Initial full sync
        get_logger().info("Starting initial full sync...")
        await self.indexing_service.index_all_repositories(repo_urls)
        await self.jira_sync_service.full_sync(jira_projects)
        
        # Periodic incremental sync
        while self._running:
            await asyncio.sleep(3600)  # Every hour
            
            get_logger().info("Running incremental sync...")
            for repo_url in repo_urls:
                await self.indexing_service.index_repository(
                    repo_url, 
                    job_type='incremental'
                )
            
            await self.jira_sync_service.incremental_sync(jira_projects)
    
    def stop(self) -> None:
        """Stop the scheduler."""
        self._running = False
```

### CLI Commands for Data Management

Create: `pr_agent/cli_admin.py`

```python
#!/usr/bin/env python3
"""
Admin CLI for managing PR Agent data.

Usage:
    python -m pr_agent.cli_admin index-repos --config repos.yaml
    python -m pr_agent.cli_admin sync-jira --projects WORK,DEVOPS
    python -m pr_agent.cli_admin status
"""

import argparse
import asyncio
import yaml
from pr_agent.services.indexing_service import RepositoryIndexingService
from pr_agent.services.jira_sync_service import JiraSyncService, SyncScheduler
from pr_agent.db.connection import DatabaseManager
from pr_agent.config_loader import get_settings
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler

async def cmd_index_repos(args):
    """Index repositories command."""
    # Load repo config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    repo_urls = config.get('repositories', [])
    
    # Initialize services
    db = DatabaseManager(get_settings().workiz.database_url)
    await db.initialize()
    
    ai_handler = LiteLLMAIHandler()
    indexing_service = RepositoryIndexingService(
        db=db,
        github_token=get_settings().github.user_token,
        embedding_handler=ai_handler
    )
    
    print(f"Indexing {len(repo_urls)} repositories...")
    jobs = await indexing_service.index_all_repositories(repo_urls)
    
    for job in jobs:
        status = "✓" if job.status == 'completed' else "✗"
        print(f"{status} {job.repository_url}: {job.stats}")
    
    await db.close()

async def cmd_sync_jira(args):
    """Sync Jira tickets command."""
    projects = args.projects.split(',')
    
    db = DatabaseManager(get_settings().workiz.database_url)
    await db.initialize()
    
    from pr_agent.integrations.jira_client import JiraClient
    jira_client = JiraClient(
        base_url=get_settings().jira.base_url,
        email=get_settings().jira.email,
        api_token=get_settings().jira.api_token
    )
    
    ai_handler = LiteLLMAIHandler()
    jira_sync = JiraSyncService(jira_client, db, ai_handler)
    
    print(f"Syncing Jira projects: {projects}")
    
    if args.full:
        stats = await jira_sync.full_sync(projects)
    else:
        stats = await jira_sync.incremental_sync(projects)
    
    print(f"Sync complete: {stats}")
    await db.close()

async def cmd_status(args):
    """Show indexing status."""
    db = DatabaseManager(get_settings().workiz.database_url)
    await db.initialize()
    
    async with db.connection() as conn:
        # Repository stats
        repos = await conn.fetch("""
            SELECT r.org_name, r.repo_name, r.last_indexed_at,
                   COUNT(cc.id) as chunk_count
            FROM repositories r
            LEFT JOIN code_chunks cc ON r.id = cc.repository_id
            GROUP BY r.id
            ORDER BY r.last_indexed_at DESC
        """)
        
        print("\n=== Indexed Repositories ===")
        for repo in repos:
            print(f"  {repo['org_name']}/{repo['repo_name']}: "
                  f"{repo['chunk_count']} chunks, "
                  f"last indexed: {repo['last_indexed_at']}")
        
        # Jira stats
        jira_stats = await conn.fetchrow("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN status = 'Done' THEN 1 END) as done
            FROM jira_tickets
        """)
        
        print(f"\n=== Jira Tickets ===")
        print(f"  Total: {jira_stats['total']}, Resolved: {jira_stats['done']}")
    
    await db.close()

def main():
    parser = argparse.ArgumentParser(description='PR Agent Admin CLI')
    subparsers = parser.add_subparsers(dest='command')
    
    # index-repos command
    index_parser = subparsers.add_parser('index-repos', help='Index repositories')
    index_parser.add_argument('--config', required=True, help='YAML config file with repo URLs')
    
    # sync-jira command
    jira_parser = subparsers.add_parser('sync-jira', help='Sync Jira tickets')
    jira_parser.add_argument('--projects', required=True, help='Comma-separated project keys')
    jira_parser.add_argument('--full', action='store_true', help='Full sync instead of incremental')
    
    # status command
    subparsers.add_parser('status', help='Show indexing status')
    
    args = parser.parse_args()
    
    if args.command == 'index-repos':
        asyncio.run(cmd_index_repos(args))
    elif args.command == 'sync-jira':
        asyncio.run(cmd_sync_jira(args))
    elif args.command == 'status':
        asyncio.run(cmd_status(args))
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
```

### Repository Configuration Example

Create: `repos.yaml` (example config)

```yaml
# Repository configuration for indexing
repositories:
  # PHP Services
  - https://github.com/workiz/legacy-api.git
  - https://github.com/workiz/billing-service.git
  
  # NodeJS Services
  - https://github.com/workiz/notification-service.git
  - https://github.com/workiz/scheduling-service.git
  
  # NestJS Services
  - https://github.com/workiz/user-service.git
  - https://github.com/workiz/job-service.git
  - https://github.com/workiz/messaging-service.git
  
  # React Frontend
  - https://github.com/workiz/web-app.git
  - https://github.com/workiz/mobile-web.git

# Indexing settings
settings:
  branch: main
  exclude_paths:
    - node_modules/
    - vendor/
    - dist/
    - build/
    - __tests__/
    - test/
  
  # File patterns to index
  include_patterns:
    - "*.php"
    - "*.js"
    - "*.ts"
    - "*.tsx"
```

---

## Auto-Discovery of Repositories and Jira Projects

### GitHub Organization Repository Discovery

Create: `pr_agent/services/discovery_service.py`

```python
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Set
from dataclasses import dataclass
import aiohttp
from pr_agent.db.connection import DatabaseManager
from pr_agent.log import get_logger
from pr_agent.config_loader import get_settings

@dataclass
class DiscoveredRepo:
    org: str
    name: str
    url: str
    default_branch: str
    language: str
    updated_at: datetime
    is_archived: bool

class GitHubDiscoveryService:
    """Auto-discover repositories in GitHub organization."""
    
    def __init__(self, db: DatabaseManager, github_token: str):
        self.db = db
        self.github_token = github_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    async def discover_org_repos(self, org_name: str) -> List[DiscoveredRepo]:
        """Discover all repositories in an organization."""
        repos = []
        page = 1
        per_page = 100
        
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.base_url}/orgs/{org_name}/repos"
                params = {
                    "page": page,
                    "per_page": per_page,
                    "type": "all",
                    "sort": "updated"
                }
                
                async with session.get(url, headers=self.headers, params=params) as response:
                    if response.status != 200:
                        get_logger().error(f"Failed to fetch repos: {response.status}")
                        break
                    
                    data = await response.json()
                    if not data:
                        break
                    
                    for repo in data:
                        repos.append(DiscoveredRepo(
                            org=org_name,
                            name=repo['name'],
                            url=repo['clone_url'],
                            default_branch=repo['default_branch'],
                            language=repo.get('language', 'unknown'),
                            updated_at=datetime.fromisoformat(repo['updated_at'].replace('Z', '+00:00')),
                            is_archived=repo['archived']
                        ))
                    
                    page += 1
        
        return repos
    
    async def sync_repos_to_database(self, org_name: str) -> Dict:
        """Sync discovered repos to database and identify new ones."""
        discovered = await self.discover_org_repos(org_name)
        
        # Filter out archived repos
        active_repos = [r for r in discovered if not r.is_archived]
        
        # Get existing repos from database
        async with self.db.connection() as conn:
            existing = await conn.fetch("""
                SELECT org_name, repo_name FROM repositories 
                WHERE org_name = $1
            """, org_name)
            existing_names = {(r['org_name'], r['repo_name']) for r in existing}
        
        # Identify new repos
        new_repos = []
        for repo in active_repos:
            if (repo.org, repo.name) not in existing_names:
                new_repos.append(repo)
                
                # Add to database
                async with self.db.connection() as conn:
                    await conn.execute("""
                        INSERT INTO repositories 
                        (org_name, repo_name, github_url, default_branch, primary_language)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (org_name, repo_name) DO UPDATE SET
                            github_url = EXCLUDED.github_url,
                            default_branch = EXCLUDED.default_branch
                    """, repo.org, repo.name, repo.url, repo.default_branch, repo.language)
        
        return {
            'total_discovered': len(active_repos),
            'new_repos': len(new_repos),
            'new_repo_names': [r.name for r in new_repos]
        }
    
    async def get_repos_needing_indexing(self) -> List[Dict]:
        """Get repos that need indexing (new or updated)."""
        async with self.db.connection() as conn:
            # Repos never indexed or updated since last index
            repos = await conn.fetch("""
                SELECT id, org_name, repo_name, github_url, default_branch
                FROM repositories
                WHERE last_indexed_at IS NULL
                   OR last_indexed_at < NOW() - INTERVAL '24 hours'
                ORDER BY last_indexed_at NULLS FIRST
            """)
        return [dict(r) for r in repos]


class JiraProjectDiscoveryService:
    """Auto-discover Jira projects."""
    
    def __init__(self, db: DatabaseManager, jira_client):
        self.db = db
        self.jira = jira_client
    
    async def discover_projects(self) -> List[Dict]:
        """Discover all accessible Jira projects."""
        projects = self.jira.jira.projects()
        
        discovered = []
        for project in projects:
            discovered.append({
                'key': project.key,
                'name': project.name,
                'project_type': getattr(project, 'projectTypeKey', 'software'),
                'lead': getattr(project.lead, 'displayName', None) if hasattr(project, 'lead') else None
            })
        
        return discovered
    
    async def sync_projects_to_database(self) -> Dict:
        """Sync discovered Jira projects to database."""
        discovered = await self.discover_projects()
        
        # Get existing projects
        async with self.db.connection() as conn:
            existing = await conn.fetch("SELECT project_key FROM jira_projects")
            existing_keys = {r['project_key'] for r in existing}
        
        new_projects = []
        for project in discovered:
            if project['key'] not in existing_keys:
                new_projects.append(project)
                
                async with self.db.connection() as conn:
                    await conn.execute("""
                        INSERT INTO jira_projects 
                        (project_key, project_name, project_type, sync_enabled)
                        VALUES ($1, $2, $3, TRUE)
                        ON CONFLICT (project_key) DO UPDATE SET
                            project_name = EXCLUDED.project_name
                    """, project['key'], project['name'], project['project_type'])
        
        return {
            'total_discovered': len(discovered),
            'new_projects': len(new_projects),
            'new_project_keys': [p['key'] for p in new_projects]
        }
    
    async def get_projects_for_sync(self) -> List[str]:
        """Get project keys that are enabled for sync."""
        async with self.db.connection() as conn:
            projects = await conn.fetch("""
                SELECT project_key FROM jira_projects 
                WHERE sync_enabled = TRUE
            """)
        return [p['project_key'] for p in projects]


class AutoDiscoveryScheduler:
    """Scheduler for automatic discovery and indexing."""
    
    def __init__(
        self,
        github_discovery: GitHubDiscoveryService,
        jira_discovery: JiraProjectDiscoveryService,
        indexing_service,  # RepositoryIndexingService
        jira_sync_service  # JiraSyncService
    ):
        self.github_discovery = github_discovery
        self.jira_discovery = jira_discovery
        self.indexing_service = indexing_service
        self.jira_sync = jira_sync_service
        self._running = False
    
    async def run_discovery_cycle(self, org_names: List[str]) -> Dict:
        """Run a full discovery and sync cycle."""
        results = {
            'github': {},
            'jira': {},
            'indexing': {}
        }
        
        # Discover GitHub repos
        for org in org_names:
            get_logger().info(f"Discovering repos for org: {org}")
            results['github'][org] = await self.github_discovery.sync_repos_to_database(org)
        
        # Discover Jira projects
        get_logger().info("Discovering Jira projects")
        results['jira'] = await self.jira_discovery.sync_projects_to_database()
        
        # Index new repositories
        repos_to_index = await self.github_discovery.get_repos_needing_indexing()
        get_logger().info(f"Found {len(repos_to_index)} repos needing indexing")
        
        for repo in repos_to_index:
            job = await self.indexing_service.index_repository(
                repo['github_url'],
                repo['default_branch'],
                'full'
            )
            results['indexing'][repo['repo_name']] = job.status
        
        # Sync new Jira projects
        projects_to_sync = await self.jira_discovery.get_projects_for_sync()
        await self.jira_sync.incremental_sync(projects_to_sync)
        
        return results
    
    async def start_scheduler(self, org_names: List[str], interval_hours: int = 6):
        """Start the auto-discovery scheduler."""
        self._running = True
        
        while self._running:
            try:
                get_logger().info("Running auto-discovery cycle")
                results = await self.run_discovery_cycle(org_names)
                get_logger().info(f"Discovery cycle complete: {results}")
            except Exception as e:
                get_logger().error(f"Discovery cycle failed: {e}")
            
            await asyncio.sleep(interval_hours * 3600)
    
    def stop(self):
        """Stop the scheduler."""
        self._running = False
```

### Database Schema for Auto-Discovery

```sql
-- Add to database schema

-- Jira projects table
CREATE TABLE jira_projects (
    id SERIAL PRIMARY KEY,
    project_key VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(255),
    project_type VARCHAR(100),
    sync_enabled BOOLEAN DEFAULT TRUE,
    last_synced_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add primary language to repositories
ALTER TABLE repositories ADD COLUMN IF NOT EXISTS primary_language VARCHAR(50);

-- Discovery logs
CREATE TABLE discovery_logs (
    id SERIAL PRIMARY KEY,
    discovery_type VARCHAR(50), -- 'github' or 'jira'
    org_or_source VARCHAR(255),
    items_discovered INT,
    new_items INT,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## NPM Package Management and Version Tracking

### Internal Package Analyzer

Create: `pr_agent/tools/npm_package_analyzer.py`

```python
import re
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
from packaging import version
import aiohttp
from pr_agent.db.connection import DatabaseManager
from pr_agent.log import get_logger

@dataclass
class PackageInfo:
    name: str
    current_version: str
    latest_version: Optional[str]
    is_internal: bool
    is_outdated: bool
    breaking_changes: bool
    changelog_url: Optional[str]

@dataclass
class PackageDependencyIssue:
    package_name: str
    issue_type: str  # 'outdated', 'version_mismatch', 'breaking_change', 'deprecated'
    message: str
    severity: str
    current_version: str
    recommended_version: Optional[str]
    affected_file: str

class NPMPackageAnalyzer:
    """Analyze NPM package dependencies in PRs."""
    
    def __init__(self, db: DatabaseManager, internal_packages: List[str] = None):
        self.db = db
        self.internal_packages = internal_packages or []
        self.npm_registry = "https://registry.npmjs.org"
        self._package_cache: Dict[str, Dict] = {}
    
    def set_internal_packages(self, packages: List[str]):
        """Set list of internal package names/prefixes."""
        self.internal_packages = packages
    
    def is_internal_package(self, package_name: str) -> bool:
        """Check if package is internal (Workiz package)."""
        for prefix in self.internal_packages:
            if package_name.startswith(prefix):
                return True
        return False
    
    async def analyze_package_json_changes(
        self, 
        old_content: str, 
        new_content: str,
        file_path: str
    ) -> List[PackageDependencyIssue]:
        """Analyze changes to package.json."""
        issues = []
        
        try:
            old_pkg = json.loads(old_content) if old_content else {}
            new_pkg = json.loads(new_content)
        except json.JSONDecodeError:
            return issues
        
        # Get dependencies from both versions
        old_deps = {
            **old_pkg.get('dependencies', {}),
            **old_pkg.get('devDependencies', {})
        }
        new_deps = {
            **new_pkg.get('dependencies', {}),
            **new_pkg.get('devDependencies', {})
        }
        
        # Check for added/changed packages
        for pkg_name, new_version in new_deps.items():
            old_version = old_deps.get(pkg_name)
            
            # New package added
            if old_version is None:
                if self.is_internal_package(pkg_name):
                    # Check internal package version
                    issue = await self._check_internal_package(pkg_name, new_version, file_path)
                    if issue:
                        issues.append(issue)
                else:
                    # Check external package
                    issue = await self._check_external_package(pkg_name, new_version, file_path)
                    if issue:
                        issues.append(issue)
            
            # Version changed
            elif old_version != new_version:
                issues.extend(await self._check_version_change(
                    pkg_name, old_version, new_version, file_path
                ))
        
        # Check for removed packages
        for pkg_name in old_deps:
            if pkg_name not in new_deps:
                if self.is_internal_package(pkg_name):
                    issues.append(PackageDependencyIssue(
                        package_name=pkg_name,
                        issue_type='removed_internal',
                        message=f"Internal package '{pkg_name}' removed - verify this doesn't break other services",
                        severity='warning',
                        current_version=old_deps[pkg_name],
                        recommended_version=None,
                        affected_file=file_path
                    ))
        
        return issues
    
    async def _check_internal_package(
        self, 
        pkg_name: str, 
        version_spec: str,
        file_path: str
    ) -> Optional[PackageDependencyIssue]:
        """Check internal package for issues."""
        # Get latest version from internal registry or database
        latest = await self._get_internal_package_latest(pkg_name)
        
        if not latest:
            return None
        
        current = self._parse_version(version_spec)
        
        # Check if using outdated version
        if current and latest and version.parse(current) < version.parse(latest):
            return PackageDependencyIssue(
                package_name=pkg_name,
                issue_type='outdated_internal',
                message=f"Internal package '{pkg_name}' has newer version available: {latest}",
                severity='info',
                current_version=version_spec,
                recommended_version=f"^{latest}",
                affected_file=file_path
            )
        
        return None
    
    async def _check_external_package(
        self, 
        pkg_name: str, 
        version_spec: str,
        file_path: str
    ) -> Optional[PackageDependencyIssue]:
        """Check external package for issues."""
        pkg_info = await self._get_npm_package_info(pkg_name)
        
        if not pkg_info:
            return None
        
        # Check if package is deprecated
        if pkg_info.get('deprecated'):
            return PackageDependencyIssue(
                package_name=pkg_name,
                issue_type='deprecated',
                message=f"Package '{pkg_name}' is deprecated: {pkg_info.get('deprecated')}",
                severity='warning',
                current_version=version_spec,
                recommended_version=None,
                affected_file=file_path
            )
        
        return None
    
    async def _check_version_change(
        self, 
        pkg_name: str, 
        old_version: str, 
        new_version: str,
        file_path: str
    ) -> List[PackageDependencyIssue]:
        """Check if version change introduces issues."""
        issues = []
        
        old_v = self._parse_version(old_version)
        new_v = self._parse_version(new_version)
        
        if not old_v or not new_v:
            return issues
        
        old_parsed = version.parse(old_v)
        new_parsed = version.parse(new_v)
        
        # Check for major version bump (potential breaking changes)
        if hasattr(old_parsed, 'major') and hasattr(new_parsed, 'major'):
            if new_parsed.major > old_parsed.major:
                severity = 'warning' if self.is_internal_package(pkg_name) else 'info'
                issues.append(PackageDependencyIssue(
                    package_name=pkg_name,
                    issue_type='breaking_change',
                    message=f"Major version bump for '{pkg_name}': {old_version} -> {new_version}. Review changelog for breaking changes.",
                    severity=severity,
                    current_version=old_version,
                    recommended_version=new_version,
                    affected_file=file_path
                ))
        
        # Check for downgrade
        if new_parsed < old_parsed:
            issues.append(PackageDependencyIssue(
                package_name=pkg_name,
                issue_type='downgrade',
                message=f"Package '{pkg_name}' downgraded: {old_version} -> {new_version}. Verify this is intentional.",
                severity='warning',
                current_version=old_version,
                recommended_version=old_version,
                affected_file=file_path
            ))
        
        return issues
    
    async def check_version_consistency(self, repo_name: str, pkg_name: str, version_spec: str) -> List[PackageDependencyIssue]:
        """Check if package version is consistent with other repos."""
        issues = []
        
        if not self.is_internal_package(pkg_name):
            return issues
        
        # Get versions used in other repos
        async with self.db.connection() as conn:
            other_versions = await conn.fetch("""
                SELECT r.repo_name, pd.version_spec
                FROM package_dependencies pd
                JOIN repositories r ON pd.repository_id = r.id
                WHERE pd.package_name = $1
                  AND r.repo_name != $2
            """, pkg_name, repo_name)
        
        if other_versions:
            versions_set = {v['version_spec'] for v in other_versions}
            if len(versions_set) > 1 or (versions_set and version_spec not in versions_set):
                issues.append(PackageDependencyIssue(
                    package_name=pkg_name,
                    issue_type='version_mismatch',
                    message=f"Version inconsistency for '{pkg_name}': this PR uses {version_spec}, other repos use: {', '.join(versions_set)}",
                    severity='warning',
                    current_version=version_spec,
                    recommended_version=list(versions_set)[0] if versions_set else None,
                    affected_file='package.json'
                ))
        
        return issues
    
    async def _get_npm_package_info(self, pkg_name: str) -> Optional[Dict]:
        """Get package info from NPM registry."""
        if pkg_name in self._package_cache:
            return self._package_cache[pkg_name]
        
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.npm_registry}/{pkg_name}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._package_cache[pkg_name] = data
                        return data
        except Exception as e:
            get_logger().warning(f"Failed to fetch NPM info for {pkg_name}: {e}")
        
        return None
    
    async def _get_internal_package_latest(self, pkg_name: str) -> Optional[str]:
        """Get latest version of internal package."""
        # Check database first
        async with self.db.connection() as conn:
            row = await conn.fetchrow("""
                SELECT latest_version FROM internal_packages
                WHERE package_name = $1
            """, pkg_name)
            if row:
                return row['latest_version']
        
        # Could also check private NPM registry here
        return None
    
    def _parse_version(self, version_spec: str) -> Optional[str]:
        """Parse version from spec (remove ^, ~, etc.)."""
        if not version_spec:
            return None
        # Remove common prefixes
        clean = re.sub(r'^[\^~>=<]+', '', version_spec)
        # Remove any remaining non-version chars
        clean = re.sub(r'[^0-9.].*$', '', clean)
        return clean if clean else None


class PackageVersionTracker:
    """Track package versions across all repositories."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def update_repo_dependencies(
        self, 
        repo_id: int, 
        package_json_content: str
    ) -> None:
        """Update tracked dependencies for a repository."""
        try:
            pkg = json.loads(package_json_content)
        except json.JSONDecodeError:
            return
        
        deps = {
            **pkg.get('dependencies', {}),
            **pkg.get('devDependencies', {})
        }
        
        async with self.db.connection() as conn:
            # Clear existing dependencies for this repo
            await conn.execute(
                "DELETE FROM package_dependencies WHERE repository_id = $1",
                repo_id
            )
            
            # Insert new dependencies
            for pkg_name, version_spec in deps.items():
                await conn.execute("""
                    INSERT INTO package_dependencies 
                    (repository_id, package_name, version_spec, dep_type)
                    VALUES ($1, $2, $3, $4)
                """, repo_id, pkg_name, version_spec, 
                    'dev' if pkg_name in pkg.get('devDependencies', {}) else 'prod')
    
    async def get_package_usage_report(self, pkg_name: str) -> List[Dict]:
        """Get report of where a package is used and at what versions."""
        async with self.db.connection() as conn:
            rows = await conn.fetch("""
                SELECT r.org_name, r.repo_name, pd.version_spec, pd.dep_type
                FROM package_dependencies pd
                JOIN repositories r ON pd.repository_id = r.id
                WHERE pd.package_name = $1
                ORDER BY r.org_name, r.repo_name
            """, pkg_name)
        
        return [dict(r) for r in rows]
    
    async def find_version_inconsistencies(self) -> List[Dict]:
        """Find packages with inconsistent versions across repos."""
        async with self.db.connection() as conn:
            rows = await conn.fetch("""
                SELECT package_name, 
                       COUNT(DISTINCT version_spec) as version_count,
                       array_agg(DISTINCT version_spec) as versions,
                       array_agg(DISTINCT r.repo_name) as repos
                FROM package_dependencies pd
                JOIN repositories r ON pd.repository_id = r.id
                GROUP BY package_name
                HAVING COUNT(DISTINCT version_spec) > 1
                ORDER BY version_count DESC
            """)
        
        return [dict(r) for r in rows]


class InternalPackageRegistry:
    """Manage registry of internal Workiz packages."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def register_package(
        self, 
        name: str, 
        latest_version: str,
        repo_url: str,
        changelog_url: Optional[str] = None
    ) -> None:
        """Register or update an internal package."""
        async with self.db.connection() as conn:
            await conn.execute("""
                INSERT INTO internal_packages 
                (package_name, latest_version, repo_url, changelog_url)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (package_name) DO UPDATE SET
                    latest_version = EXCLUDED.latest_version,
                    updated_at = CURRENT_TIMESTAMP
            """, name, latest_version, repo_url, changelog_url)
    
    async def get_all_internal_packages(self) -> List[Dict]:
        """Get list of all internal packages."""
        async with self.db.connection() as conn:
            rows = await conn.fetch("""
                SELECT package_name, latest_version, repo_url, changelog_url, updated_at
                FROM internal_packages
                ORDER BY package_name
            """)
        return [dict(r) for r in rows]
    
    async def sync_from_npm_org(self, npm_org: str) -> Dict:
        """Sync internal packages from NPM organization."""
        # Query NPM for packages under organization
        async with aiohttp.ClientSession() as session:
            url = f"https://registry.npmjs.org/-/v1/search?text=scope:{npm_org}&size=250"
            async with session.get(url) as response:
                if response.status != 200:
                    return {'error': f"Failed to fetch from NPM: {response.status}"}
                
                data = await response.json()
                packages = data.get('objects', [])
                
                synced = 0
                for pkg in packages:
                    pkg_info = pkg.get('package', {})
                    name = pkg_info.get('name')
                    version = pkg_info.get('version')
                    
                    if name and version:
                        await self.register_package(
                            name=name,
                            latest_version=version,
                            repo_url=pkg_info.get('links', {}).get('repository', ''),
                            changelog_url=pkg_info.get('links', {}).get('homepage', '')
                        )
                        synced += 1
                
                return {'synced': synced, 'total_found': len(packages)}
```

### Database Schema for NPM Packages

```sql
-- Package dependencies tracking
CREATE TABLE package_dependencies (
    id SERIAL PRIMARY KEY,
    repository_id INT REFERENCES repositories(id),
    package_name VARCHAR(255) NOT NULL,
    version_spec VARCHAR(100),
    dep_type VARCHAR(20), -- 'prod' or 'dev'
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
    deprecation_message TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Package update history
CREATE TABLE package_updates (
    id SERIAL PRIMARY KEY,
    package_name VARCHAR(255) NOT NULL,
    old_version VARCHAR(100),
    new_version VARCHAR(100),
    update_type VARCHAR(50), -- 'major', 'minor', 'patch'
    breaking_changes TEXT[],
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cursor rules extracted from repositories
CREATE TABLE cursor_rules (
    id SERIAL PRIMARY KEY,
    repository_id INT REFERENCES repositories(id),
    source_file VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    rule_text TEXT NOT NULL,
    applies_to TEXT[],  -- glob patterns
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(repository_id, source_file, rule_text)
);

-- Create indexes
CREATE INDEX idx_package_deps_pkg ON package_dependencies(package_name);
CREATE INDEX idx_package_deps_repo ON package_dependencies(repository_id);
CREATE INDEX idx_internal_packages_name ON internal_packages(package_name);
CREATE INDEX idx_cursor_rules_repo ON cursor_rules(repository_id);
```

### Integration with PR Review

Update: `pr_agent/tools/pr_reviewer.py`

```python
# Add to PRReviewer class

async def _check_package_dependencies(self) -> List[Dict]:
    """Check package.json changes in PR."""
    issues = []
    
    npm_analyzer = NPMPackageAnalyzer(
        db=self.db,
        internal_packages=['@workiz/', 'workiz-']
    )
    
    for file in self.git_provider.get_diff_files():
        if file.filename.endswith('package.json'):
            # Get old and new content
            old_content = file.base_file or ''
            new_content = file.head_file or ''
            
            file_issues = await npm_analyzer.analyze_package_json_changes(
                old_content, 
                new_content,
                file.filename
            )
            issues.extend(file_issues)
            
            # Check version consistency across repos
            if new_content:
                try:
                    pkg = json.loads(new_content)
                    all_deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                    
                    for pkg_name, version_spec in all_deps.items():
                        if npm_analyzer.is_internal_package(pkg_name):
                            consistency_issues = await npm_analyzer.check_version_consistency(
                                self.git_provider.repo,
                                pkg_name,
                                version_spec
                            )
                            issues.extend(consistency_issues)
                except json.JSONDecodeError:
                    pass
    
    return issues
```

---

## Deployment Guide

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Google Cloud Platform                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │  Cloud Run  │    │  Cloud SQL  │    │  Secret Manager     │ │
│  │  PR Agent   │◄──►│  PostgreSQL │    │  API Keys/Tokens    │ │
│  │  Container  │    │  + pgvector │    └─────────────────────┘ │
│  └──────┬──────┘    └─────────────┘                            │
│         │                                                        │
│         ▼                                                        │
│  ┌─────────────┐    ┌─────────────┐                            │
│  │   Pub/Sub   │    │   GCS       │                            │
│  │   Events    │    │   (Logs)    │                            │
│  └─────────────┘    └─────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                       External Services                          │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌──────────────┐ │
│  │  GitHub   │  │   Jira    │  │  OpenAI   │  │ NPM Registry │ │
│  │  API      │  │   API     │  │   API     │  │   (Private)  │ │
│  └───────────┘  └───────────┘  └───────────┘  └──────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

### Local Development Setup (Step-by-Step)

#### Step 1: Prerequisites

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

#### Step 2: Clone and Setup Project

```bash
# Clone repository
cd ~/Documents/Github
git clone https://github.com/workiz/workiz-pr-agent.git
cd workiz-pr-agent

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install additional Workiz dependencies
pip install asyncpg jira pgvector aiohttp gitpython pyyaml packaging
```

#### Step 3: Start Local Database

```bash
# Create docker-compose.local.yml (if not exists)
cat > docker-compose.local.yml << 'EOF'
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
EOF

# Create database init directory
mkdir -p db/init

# Copy schema file
# (Use the 01_schema.sql from this document)

# Start database
docker-compose -f docker-compose.local.yml up -d

# Verify database is running
docker logs pr-agent-db
```

#### Step 4: Configure Secrets for Local Development

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
# For GitHub App (optional for local dev)
# private_key = """-----BEGIN RSA PRIVATE KEY-----
# ...
# -----END RSA PRIVATE KEY-----"""
# app_id = "123456"
# webhook_secret = "your-webhook-secret"

[jira]
api_token = "your-jira-api-token"
email = "your-email@workiz.com"

[workiz]
database_url = "postgresql://pr_agent:pr_agent_dev@localhost:5432/pr_agent"

# Internal packages (Workiz NPM organization)
npm_org = "@workiz"
internal_package_prefixes = ["@workiz/", "workiz-"]
```

#### Step 5: Configure Main Settings

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

# RAG settings
rag_similarity_threshold = 0.75
rag_max_chunks = 10

# Review settings
max_review_comments = 15

# Auto-discovery
auto_discovery_enabled = true
github_orgs = ["workiz"]

[jira]
base_url = "https://workiz.atlassian.net"

[pr_reviewer]
num_max_findings = 15
require_security_review = true
```

#### Step 6: Initialize Database and Index Data

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

# Run auto-discovery (will find all repos and projects)
python -m pr_agent.cli_admin discover --orgs workiz

# Or manually index specific repos
python -m pr_agent.cli_admin index-repos --config repos.yaml

# Sync Jira
python -m pr_agent.cli_admin sync-jira --full

# Check status
python -m pr_agent.cli_admin status
```

#### Step 7: Start Local Server

```bash
# Terminal 1: Start the server
source venv/bin/activate
python -m uvicorn pr_agent.servers.github_app:app --host 0.0.0.0 --port 3000 --reload

# Terminal 2: Start ngrok tunnel
ngrok http 3000

# Note the ngrok URL (e.g., https://abc123.ngrok.io)
```

#### Step 8: Configure GitHub Webhook (for testing)

1. Go to your test repository Settings → Webhooks
2. Add webhook:
   - **Payload URL**: `https://your-ngrok-url.ngrok.io/api/v1/github_webhooks`
   - **Content type**: `application/json`
   - **Secret**: (generate and save to `.secrets.toml`)
   - **Events**: Select:
     - Pull requests
     - Pull request reviews
     - Issue comments
     - Push

#### Step 9: Test PR Review

```bash
# Create a test PR in your repository
# Or use CLI to test directly:
python pr_agent/cli.py --pr_url="https://github.com/workiz/test-repo/pull/1" review
```

---

### Production Deployment (Google Cloud)

#### Step 1: GCloud Project Setup

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

#### Step 2: Create Cloud SQL Instance

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

#### Step 3: Configure Secrets in Google Secret Manager

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

# Database password (use the one from Step 2)
echo -n "database-password" | gcloud secrets create db-password --data-file=-

# List secrets to verify
gcloud secrets list
```

#### Step 4: Create Service Account

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

#### Step 5: Update Code for GCloud Secrets Manager

Create: `pr_agent/secret_providers/gcloud_secret_manager.py`

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
        """Get secret from Secret Manager."""
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
        """Get all required secrets."""
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

Update: `pr_agent/config_loader.py`

```python
# Add to config_loader.py

import os

def load_secrets_from_gcloud():
    """Load secrets from GCloud Secret Manager if in production."""
    if os.environ.get('GCLOUD_PROJECT'):
        from pr_agent.secret_providers.gcloud_secret_manager import GCloudSecretManagerProvider
        
        provider = GCloudSecretManagerProvider(os.environ['GCLOUD_PROJECT'])
        secrets = provider.get_all_secrets()
        
        # Set as environment variables
        os.environ['OPENAI_KEY'] = secrets['openai_key']
        os.environ['GITHUB_USER_TOKEN'] = secrets['github_token']
        os.environ['GITHUB_APP_PRIVATE_KEY'] = secrets['github_app_private_key']
        os.environ['GITHUB_APP_ID'] = secrets['github_app_id']
        os.environ['GITHUB_WEBHOOK_SECRET'] = secrets['github_webhook_secret']
        os.environ['JIRA_API_TOKEN'] = secrets['jira_api_token']
        os.environ['JIRA_EMAIL'] = secrets['jira_email']
        
        # Build database URL
        db_password = secrets['db_password']
        db_instance = os.environ.get('CLOUD_SQL_INSTANCE', '')
        os.environ['WORKIZ_DATABASE_URL'] = f"postgresql://pr_agent:{db_password}@/{db_instance}?host=/cloudsql/{db_instance}"

# Call at startup
if os.environ.get('GCLOUD_PROJECT'):
    load_secrets_from_gcloud()
```

#### Step 6: Create Dockerfile for Production

```dockerfile
# Dockerfile.production
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

#### Step 7: Deploy to Cloud Run

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
    --set-env-vars "GITHUB_ORGS=workiz" \
    --add-cloudsql-instances $PROJECT_ID:$REGION:pr-agent-db \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --allow-unauthenticated

# Get the deployed URL
gcloud run services describe pr-agent --region $REGION --format='value(status.url)'
```

#### Step 8: Configure GitHub App (Production)

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

#### Step 9: Configure Jira Webhook (Production)

1. Go to Jira Settings → System → Webhooks
2. Create webhook:
   - **URL**: `https://your-cloud-run-url/api/v1/webhooks/jira`
   - **Events**:
     - Issue: created, updated, deleted

#### Step 10: Initialize Production Database

```bash
# Connect to Cloud SQL
gcloud sql connect pr-agent-db --user=pr_agent

# In psql, run the schema
\i 01_schema.sql

# Enable pgvector
CREATE EXTENSION IF NOT EXISTS vector;

# Exit
\q
```

#### Step 11: Run Initial Indexing (Production)

```bash
# Option 1: Use Cloud Run Jobs
gcloud run jobs create pr-agent-indexing \
    --image gcr.io/$PROJECT_ID/pr-agent:latest \
    --region $REGION \
    --service-account pr-agent-sa@$PROJECT_ID.iam.gserviceaccount.com \
    --set-env-vars "GCLOUD_PROJECT=$PROJECT_ID" \
    --add-cloudsql-instances $PROJECT_ID:$REGION:pr-agent-db \
    --command "python" \
    --args="-m,pr_agent.cli_admin,discover,--orgs,workiz"

# Execute the job
gcloud run jobs execute pr-agent-indexing --region $REGION

# Option 2: Use Admin API
curl -X POST "https://your-cloud-run-url/api/v1/admin/discovery" \
    -H "Content-Type: application/json" \
    -d '{"org_names": ["workiz"]}'
```

#### Step 12: Set Up Scheduled Jobs

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

### Monitoring and Logging

#### Cloud Logging Setup

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

#### Cloud Monitoring Alerts

```bash
# Create alert policy for high error rate
gcloud alpha monitoring policies create \
    --display-name="PR Agent High Error Rate" \
    --condition-display-name="Error rate > 5%" \
    --condition-filter='metric.type="logging.googleapis.com/user/pr-agent-errors" AND resource.type="cloud_run_revision"' \
    --condition-threshold-value=0.05 \
    --condition-threshold-duration=300s \
    --notification-channels=your-channel-id
```

---

## Updated Database Schema

Add to the database schema in the main plan:

```sql
-- Additional tables for multi-database support

-- Track database queries found in code
CREATE TABLE database_queries (
    id SERIAL PRIMARY KEY,
    repository_id INT REFERENCES repositories(id),
    file_path TEXT NOT NULL,
    line_number INT,
    query_type VARCHAR(50), -- 'mysql', 'mongodb', 'elasticsearch'
    operation VARCHAR(50), -- 'select', 'insert', 'update', 'delete', 'find', 'aggregate'
    query_content TEXT,
    tables_collections TEXT[], -- Tables or collections involved
    potential_issues JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- PubSub topology tracking
CREATE TABLE pubsub_events (
    id SERIAL PRIMARY KEY,
    repository_id INT REFERENCES repositories(id),
    file_path TEXT NOT NULL,
    line_number INT,
    topic VARCHAR(255) NOT NULL,
    event_type VARCHAR(50), -- 'publish' or 'subscribe'
    handler_name VARCHAR(255),
    message_schema VARCHAR(255), -- DTO class name
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexing jobs history
CREATE TABLE indexing_jobs (
    id SERIAL PRIMARY KEY,
    repository_id INT REFERENCES repositories(id),
    job_type VARCHAR(50), -- 'full', 'incremental'
    status VARCHAR(50), -- 'pending', 'running', 'completed', 'failed'
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    stats JSONB,
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_database_queries_repo ON database_queries(repository_id);
CREATE INDEX idx_pubsub_events_topic ON pubsub_events(topic);
CREATE INDEX idx_pubsub_events_type ON pubsub_events(event_type);
CREATE INDEX idx_indexing_jobs_status ON indexing_jobs(status);
```

---

## Appendix: Key Existing Code References

### Command Routing (`pr_agent/agent/pr_agent.py`)

```python:24:44:pr_agent/agent/pr_agent.py
command2class = {
    "auto_review": PRReviewer,
    "answer": PRReviewer,
    "review": PRReviewer,
    ...
}
```

### AI Handler Interface (`pr_agent/algo/ai_handlers/base_ai_handler.py`)

```python:1:28:pr_agent/algo/ai_handlers/base_ai_handler.py
class BaseAiHandler(ABC):
    @abstractmethod
    async def chat_completion(self, model: str, system: str, user: str, temperature: float = 0.2, img_path: str = None):
        pass
```

### Review Prompt Structure (`pr_agent/settings/pr_reviewer_prompts.toml`)

```toml:1:50:pr_agent/settings/pr_reviewer_prompts.toml
[pr_review_prompt]
system="""You are PR-Reviewer...
{%- if extra_instructions %}
Extra instructions:
{{ extra_instructions }}
{%- endif %}
"""
```

### Existing RAG Implementation (`pr_agent/tools/pr_similar_issue.py`)

```python:35:75:pr_agent/tools/pr_similar_issue.py
# Demonstrates vector DB integration with Pinecone, LanceDB, Qdrant
```

---

## Summary: Addressing All Requirements

### ✅ Languages and Frameworks Covered

| Stack | Analyzer | Rules | Notes |
|-------|----------|-------|-------|
| **PHP** | `PHPAnalyzer` | php_avoid_raw_sql, php_no_dd, eloquent_n_plus_one, mass_assignment, env_in_code | Main backend, MySQL, MongoDB, Elasticsearch |
| **NodeJS (JS)** | `JavaScriptAnalyzer` | js_no_console, callback_hell, no_var, mutation_in_reduce | Express routes, EventEmitter patterns |
| **NodeJS (TS)** | `TypeScriptAnalyzer` | ts_no_any, ts_no_ignore, prefer_readonly | Extends JS analyzer, adds interfaces/types |
| **NestJS (TS)** | `NestJSAnalyzer` | 20+ rules from Cursor Rules (structured logging, DI, PubSub, functional style, etc.) | Auth, CRM, Core, Reporting services |
| **React (TS)** | `ReactAnalyzer` | react_inline_styles, react_missing_key, react_index_as_key, react_useeffect_no_deps, react_class_component | Web app, Mobile web |
| **Python** | `PythonAnalyzer` | py_no_print, pg_sql_injection, pg_n_plus_one, asyncio_blocking_call, fastapi_sync_endpoint | FastAPI + PostgreSQL |

### ✅ Cursor Team Rules Integrated (From `.cursor/rules.mdc`)

| Category | Rules Added | Source File |
|----------|-------------|-------------|
| **Structured Logging** | no_logger_context, logger_string_concat, maskSensitive required | `rules.mdc` |
| **Functional Style** | let_usage, var_usage, array_mutation, object_mutation, imperative_loop | Workspace Rules |
| **PubSub Patterns** | pubsub_no_ack, pubsub_sync_handler, pubsub_metadata, pubsub_registration | `pubsub-pattern.mdc` |
| **Exception Handling** | catch_without_rethrow, try_catch_in_service, use @workiz/all-exceptions-filter | Workspace Rules |
| **TypeORM Migrations** | typeorm_table_builder (use raw SQL only) | Workspace Rules |
| **Controller Standards** | singular_route, controller_complex_logic, no business logic in controllers | Workspace Rules |
| **No Inline Comments** | inline_comment detection | `rules.mdc` |
| **Test Execution** | Use `npm run test`, grep for "fail" and "error" | `rules.mdc` |
| **Code Verification** | Always check actual implementation, don't assume | `rules.mdc` |
| **DI Pattern** | Use NestJS IoC, no manual instantiation | Workspace Rules |

### ✅ PubSub Pattern Requirements (From `pubsub-pattern.mdc`)

| Requirement | Rule Check |
|-------------|------------|
| Metadata constants in `src/constants/pubsub-metadata.ts` | `pubsub_metadata_location` |
| Decorators: @PubSubTopic, @PubSubEvent, @PubSubAsyncAcknowledge | `pubsub_missing_decorators` |
| Method signature with EmittedMessage and typed DTO | `pubsub_method_signature` |
| Register in main.ts with ReflectDecoratorService | `pubsub_registration_missing` |
| Use maskSensitive() for logging payloads | `pubsub_sensitive_logging` |
| No business logic in controller handlers | `pubsub_controller_logic` |
| Handler naming: onResourceAction format | `pubsub_handler_naming` |

### ✅ Databases Covered

| Database | Analyzer | Key Checks | Used By |
|----------|----------|------------|---------|
| **MySQL** | `MySQLAnalyzer` | SELECT *, LIMIT without ORDER BY, N+1 queries, SQL injection | PHP backend, NestJS services |
| **PostgreSQL** | `PostgreSQLAnalyzer` | pg_sql_injection, pg_n_plus_one, pg_commit_in_loop, asyncpg patterns | Python service |
| **MongoDB** | `MongoDBAnalyzer` | Queries without indexes, $regex without anchor, large $in arrays | PHP backend |
| **Elasticsearch** | `ElasticsearchAnalyzer` | Wildcard queries, script queries, deep pagination | PHP backend, Reporting service |

### ✅ Security Review (Traefik-Aware)

| Focus Area | What We Check | What We Don't Check |
|------------|---------------|---------------------|
| **Input Validation** | DTOs with class-validator, missing validation | Auth guards (Traefik handles) |
| **Injection** | SQL, NoSQL, command injection | Session validation |
| **Data Exposure** | Sensitive data in logs, passwords logged | JWT validation |
| **Headers** | Manipulating X-WORKIZ headers incorrectly | Role-based access |
| **CORS/Cookies** | Wildcard CORS, insecure cookies | - |

### ✅ Workiz Internal NPM Packages

| Package | Purpose | Track Updates |
|---------|---------|---------------|
| `@workiz/all-exceptions-filter` | Global exception handling | ✅ |
| `@workiz/config-loader` | Configuration with GCloud Secrets | ✅ |
| `@workiz/node-logger` | Structured logging (Winston) | ✅ |
| `@workiz/pubsub-decorator-reflector` | PubSub decorators | ✅ |
| `@workiz/pubsub-publish-client` | PubSub publishing | ✅ |
| `@workiz/redis-nestjs` | Redis integration | ✅ |
| `@workiz/jwt-headers-generator` | JWT header utilities | ✅ |
| `@workiz/socket-io-updater` | Socket.io updates | ✅ |

### ✅ NPM Package Management

| Feature | Implementation | Description |
|---------|----------------|-------------|
| **Version tracking** | `PackageVersionTracker` | Tracks all package versions across repos |
| **Internal packages** | `InternalPackageRegistry` | Registry of @workiz/* packages with latest versions |
| **Outdated detection** | `NPMPackageAnalyzer` | Flags outdated internal packages in PRs |
| **Version consistency** | `check_version_consistency()` | Alerts when same package has different versions across repos |
| **Breaking changes** | Major version detection | Warns on major version bumps |
| **Deprecation check** | NPM registry query | Warns if using deprecated packages |

### ✅ Auto-Discovery

| Component | Service | Automation |
|-----------|---------|------------|
| **GitHub Repos** | `GitHubDiscoveryService` | Auto-discovers all repos in organization |
| **Jira Projects** | `JiraProjectDiscoveryService` | Auto-discovers all accessible Jira projects |
| **New repo indexing** | `AutoDiscoveryScheduler` | Automatically indexes newly discovered repos |
| **Scheduled discovery** | Cloud Scheduler | Runs every 6 hours to find new repos/projects |

### ✅ PubSub Events System

- **`PubSubAnalyzer`**: Extracts publishers and subscribers from code
- **Topology tracking**: Database table `pubsub_events` stores all event relationships
- **Cross-repo analysis**: Identifies orphan publishers/subscribers across repositories
- **NestJS patterns**: Detects `@PubSubTopic`, `@PubSubEvent`, `@EventPattern`, `@OnEvent`
- **Message schema detection**: Links events to DTOs

### ✅ Initial Data Population

| Command | Purpose |
|---------|---------|
| `python -m pr_agent.cli_admin index-repos --config repos.yaml` | Full repository indexing |
| `python -m pr_agent.cli_admin sync-jira --projects WORK,DEVOPS --full` | Full Jira sync |
| `python -m pr_agent.cli_admin status` | Check indexing status |
| Docker Compose + `db/init/01_schema.sql` | Database schema creation |

### ✅ Continuous Updates

| Method | Trigger | Action |
|--------|---------|--------|
| **GitHub Webhook** | Push to main/develop | Incremental repo indexing |
| **GitHub Webhook** | PR merged | Incremental repo indexing |
| **Jira Webhook** | Issue created/updated | Single ticket sync |
| **Cron Job** | Scheduled (hourly) | Incremental sync all repos + Jira |
| **Admin API** | Manual trigger | On-demand indexing via `/api/v1/admin/*` |

### Files to Create (Summary)

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
│   ├── cursor_rules_loader.py           # Load .cursor/rules.mdc files
│   ├── sql_analyzer.py                  # MySQL/MongoDB/ES analyzer
│   ├── pubsub_analyzer.py               # PubSub topology analyzer
│   ├── security_analyzer.py             # Deep security checks
│   ├── npm_package_analyzer.py          # NPM package version management
│   └── language_analyzers/
│       ├── __init__.py
│       ├── base_analyzer.py
│       ├── php_analyzer.py
│       ├── javascript_analyzer.py
│       ├── typescript_analyzer.py
│       ├── nestjs_analyzer.py
│       ├── react_analyzer.py
│       └── python_analyzer.py           # Python/FastAPI/Django support
├── settings/
│   └── workiz_rules.toml                # Custom rules configuration
├── cli_admin.py                         # Admin CLI for data management
db/
└── init/
    └── 01_schema.sql                    # PostgreSQL schema
docker-compose.local.yml                  # Local DB setup
Dockerfile.production                     # Production Docker image
repos.yaml                                # Repository configuration
```

### Quick Start Checklist (Local Development)

1. [ ] Clone the repository
2. [ ] Set up Python 3.12 virtual environment
3. [ ] Install dependencies: `pip install -r requirements.txt asyncpg jira pgvector gitpython aiohttp packaging`
4. [ ] Start PostgreSQL: `docker-compose -f docker-compose.local.yml up -d`
5. [ ] Create `.secrets.toml` with credentials (GitHub, OpenAI, Jira)
6. [ ] Run auto-discovery: `python -m pr_agent.cli_admin discover --orgs workiz`
7. [ ] Run Jira sync: `python -m pr_agent.cli_admin sync-jira --full`
8. [ ] Sync internal NPM packages: `python -m pr_agent.cli_admin sync-npm --org @workiz`
9. [ ] Start server: `python -m uvicorn pr_agent.servers.github_app:app --port 3000`
10. [ ] Start ngrok: `ngrok http 3000`
11. [ ] Configure GitHub webhook with ngrok URL
12. [ ] Test with a PR review: `/review`

### Production Deployment Checklist (GCloud)

1. [ ] **GCloud Setup**
   - [ ] Set project: `gcloud config set project workiz-pr-agent`
   - [ ] Enable APIs: Cloud Run, Secret Manager, Cloud SQL, Cloud Build
   
2. [ ] **Database**
   - [ ] Create Cloud SQL PostgreSQL instance
   - [ ] Enable pgvector extension
   - [ ] Run schema migration

3. [ ] **Secrets (GCloud Secret Manager)**
   - [ ] `openai-key` - OpenAI API key
   - [ ] `github-token` - GitHub personal access token
   - [ ] `github-app-private-key` - GitHub App private key
   - [ ] `github-app-id` - GitHub App ID
   - [ ] `github-webhook-secret` - Webhook secret
   - [ ] `jira-api-token` - Jira API token
   - [ ] `jira-email` - Jira email
   - [ ] `db-password` - Database password

4. [ ] **Service Account**
   - [ ] Create service account: `pr-agent-sa`
   - [ ] Grant Secret Manager access
   - [ ] Grant Cloud SQL Client access

5. [ ] **Deploy**
   - [ ] Build container: `gcloud builds submit`
   - [ ] Deploy to Cloud Run
   - [ ] Note the service URL

6. [ ] **GitHub App Configuration**
   - [ ] Create GitHub App in organization
   - [ ] Set webhook URL to Cloud Run service
   - [ ] Configure permissions (Contents, Issues, PRs, Commit statuses)
   - [ ] Install App to organization

7. [ ] **Jira Webhook**
   - [ ] Create webhook in Jira settings
   - [ ] Point to `{service-url}/api/v1/webhooks/jira`

8. [ ] **Scheduled Jobs**
   - [ ] Create Cloud Scheduler for discovery (every 6 hours)
   - [ ] Create Cloud Scheduler for Jira sync (every 2 hours)

9. [ ] **Monitoring**
   - [ ] Set up Cloud Logging
   - [ ] Create error rate alerts
   - [ ] Set up uptime checks

10. [ ] **Initial Data**
    - [ ] Run discovery job
    - [ ] Verify repos are indexed
    - [ ] Verify Jira projects synced

---

## Next Steps

1. **Review this document** with the team
2. **Set up local development environment** following the guide above
3. **Create the database schema** in a local PostgreSQL instance
4. **Configure repos.yaml** with your actual repository URLs
5. **Start Phase 1** implementation (database setup + global context)

For questions or clarifications, refer to the original qodo-ai/pr-agent documentation at https://qodo-merge-docs.qodo.ai/


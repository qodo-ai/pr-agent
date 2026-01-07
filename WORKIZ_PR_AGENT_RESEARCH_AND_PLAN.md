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

## Local Development Setup

### Prerequisites

```bash
# Python 3.12+
python3 --version

# PostgreSQL 15+ with pgvector
psql --version

# Install pgvector extension
CREATE EXTENSION vector;
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
pip install asyncpg jira pgvector

# 5. Copy secrets template
cp pr_agent/settings/.secrets_template.toml pr_agent/settings/.secrets.toml

# 6. Edit secrets file with your credentials
# See Configuration Guide below
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

## Next Steps

1. **Review this document** with the team
2. **Set up local development environment** following the guide above
3. **Create the database schema** in a local PostgreSQL instance
4. **Start Phase 1** implementation

For questions or clarifications, refer to the original qodo-ai/pr-agent documentation at https://qodo-merge-docs.qodo.ai/


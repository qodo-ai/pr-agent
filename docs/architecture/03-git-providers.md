# Git Providers Architecture

**Generated:** 2025-10-07

## Git Provider Hierarchy

This diagram shows the class hierarchy and relationships between different git platform providers.

```mermaid
classDiagram
    class GitProvider {
        <<abstract>>
        +is_supported(capability) bool
        +get_diff_files() List[FilePatchInfo]
        +get_files() list
        +get_pr_description_full() str
        +get_pr_description() str
        +get_user_description() str
        +publish_description(title, body)
        +publish_code_suggestions(suggestions) bool
        +publish_comment(comment, temporary)
        +publish_inline_comment(body, file, line)
        +publish_inline_comments(comments)
        +get_issue_comments()
        +edit_comment(comment, body)
        +remove_comment(comment)
        +publish_labels(labels)
        +get_pr_labels() list
        +get_commit_messages() list
        +get_languages() dict
        +get_pr_branch() str
        +get_user_id() str
        +get_repo_settings() dict
        +clone(repo_url, dest) ScopedClonedRepo
        +get_git_repo_url(url) str
        +get_canonical_url_parts(repo, branch) Tuple
    }

    class GithubProvider {
        -github_client
        -repo
        -pr
        +is_supported(capability) bool
        +get_diff_files() List[FilePatchInfo]
        +publish_description(title, body)
        +publish_code_suggestions(suggestions) bool
        +publish_persistent_comment_full()
        +publish_inline_comments(comments)
        +create_inline_comment()
        +get_issue_comments()
        +publish_labels(labels)
        +remove_reaction()
        +add_eyes_reaction()
        +auto_approve() bool
        -_prepare_clone_url_with_token()
    }

    class GitlabProvider {
        -gitlab_client
        -project
        -mr
        +is_supported(capability) bool
        +get_diff_files() List[FilePatchInfo]
        +publish_description(title, body)
        +publish_code_suggestions(suggestions) bool
        +publish_inline_comments(comments)
        +get_issue_comments()
        +publish_labels(labels)
        -_prepare_clone_url_with_token()
    }

    class BitbucketProvider {
        -bitbucket_client
        -workspace
        -repo
        -pr
        +is_supported(capability) bool
        +get_diff_files() List[FilePatchInfo]
        +publish_description(title, body)
        +publish_code_suggestions(suggestions) bool
        +publish_inline_comments(comments)
        +get_issue_comments()
        -_prepare_clone_url_with_token()
    }

    class BitbucketServerProvider {
        -bitbucket_client
        -project
        -repo
        -pr
        +is_supported(capability) bool
        +get_diff_files() List[FilePatchInfo]
        +publish_description(title, body)
        +publish_inline_comments(comments)
        -_prepare_clone_url_with_token()
    }

    class AzureDevOpsProvider {
        -azure_client
        -project
        -repo
        -pr_id
        +is_supported(capability) bool
        +get_diff_files() List[FilePatchInfo]
        +publish_description(title, body)
        +publish_comment(comment)
        +get_issue_comments()
        +publish_labels(labels)
        -_prepare_clone_url_with_token()
    }

    class GiteaProvider {
        -gitea_client
        -repo
        -pr
        +is_supported(capability) bool
        +get_diff_files() List[FilePatchInfo]
        +publish_description(title, body)
        +publish_comment(comment)
        +get_issue_comments()
        +publish_labels(labels)
        -_prepare_clone_url_with_token()
    }

    class GerritProvider {
        -gerrit_client
        -change
        +is_supported(capability) bool
        +get_diff_files() List[FilePatchInfo]
        +publish_comment(comment)
        +publish_inline_comments(comments)
        -_prepare_clone_url_with_token()
    }

    class CodeCommitProvider {
        -codecommit_client
        -repo
        -pr_id
        +is_supported(capability) bool
        +get_diff_files() List[FilePatchInfo]
        +publish_comment(comment)
        +get_issue_comments()
        -_prepare_clone_url_with_token()
    }

    class LocalGitProvider {
        -repo_path
        -git_repo
        +is_supported(capability) bool
        +get_diff_files() List[FilePatchInfo]
        +get_commit_messages()
    }

    GitProvider <|-- GithubProvider
    GitProvider <|-- GitlabProvider
    GitProvider <|-- BitbucketProvider
    GitProvider <|-- BitbucketServerProvider
    GitProvider <|-- AzureDevOpsProvider
    GitProvider <|-- GiteaProvider
    GitProvider <|-- GerritProvider
    GitProvider <|-- CodeCommitProvider
    GitProvider <|-- LocalGitProvider

    class FilePatchInfo {
        +base_file str
        +head_file str
        +patch str
        +filename str
        +tokens int
        +edit_type EDIT_TYPE
        +old_filename str
        +num_plus_lines int
        +num_minus_lines int
        +language str
        +ai_file_summary str
    }

    GitProvider ..> FilePatchInfo : returns
```

## Platform Feature Support Matrix

```mermaid
graph TD
    subgraph "GitHub"
        GH_Review[Review Comments]
        GH_Inline[Inline Comments]
        GH_Suggestions[Code Suggestions]
        GH_Labels[Labels]
        GH_Reactions[Reactions]
        GH_AutoApprove[Auto-Approve]
        GH_PersistentComments[Persistent Comments]
    end

    subgraph "GitLab"
        GL_Review[Review Comments]
        GL_Inline[Inline Comments]
        GL_Suggestions[Code Suggestions]
        GL_Labels[Labels]
        GL_PersistentComments[Persistent Comments]
    end

    subgraph "Bitbucket"
        BB_Review[Review Comments]
        BB_Inline[Inline Comments]
        BB_Suggestions[Code Suggestions]
    end

    subgraph "Azure DevOps"
        AZ_Review[Review Comments]
        AZ_Inline[Inline Comments]
        AZ_Labels[Labels]
    end

    subgraph "Gitea"
        GT_Review[Review Comments]
        GT_Inline[Inline Comments]
        GT_Labels[Labels]
    end

    subgraph "Gerrit"
        GR_Review[Review Comments]
        GR_Inline[Inline Comments]
    end

    subgraph "CodeCommit"
        CC_Review[Review Comments]
    end

    style GH_AutoApprove fill:#90EE90
    style GH_Reactions fill:#90EE90
    style GH_PersistentComments fill:#90EE90
    style GL_PersistentComments fill:#90EE90
```

## Git Provider Factory Pattern

```mermaid
flowchart TB
    Start([PR URL]) --> Parse[Parse URL]
    Parse --> DetectPlatform{Detect Platform}

    DetectPlatform -->|github.com| CreateGH[Create GithubProvider]
    DetectPlatform -->|gitlab.com| CreateGL[Create GitlabProvider]
    DetectPlatform -->|bitbucket.org| CreateBB[Create BitbucketProvider]
    DetectPlatform -->|dev.azure.com| CreateAZ[Create AzureDevOpsProvider]
    DetectPlatform -->|gitea| CreateGT[Create GiteaProvider]
    DetectPlatform -->|gerrit| CreateGR[Create GerritProvider]
    DetectPlatform -->|codecommit| CreateCC[Create CodeCommitProvider]
    DetectPlatform -->|local| CreateLocal[Create LocalGitProvider]
    DetectPlatform -->|Unknown| Error[Raise Error]

    CreateGH --> Initialize[Initialize Provider]
    CreateGL --> Initialize
    CreateBB --> Initialize
    CreateAZ --> Initialize
    CreateGT --> Initialize
    CreateGR --> Initialize
    CreateCC --> Initialize
    CreateLocal --> Initialize

    Initialize --> Auth[Authenticate]
    Auth --> LoadPR[Load PR/MR Data]
    LoadPR --> Ready([Provider Ready])

    style DetectPlatform fill:#FFD700
    style Initialize fill:#87CEEB
    style Ready fill:#90EE90
```

## Provider Communication Flow

```mermaid
sequenceDiagram
    participant Tool as PR Tool
    participant Provider as Git Provider
    participant Cache as Local Cache
    participant API as Platform API
    participant Repo as Git Repository

    Tool->>Provider: get_diff_files()

    Provider->>Cache: Check cache
    alt Cache hit
        Cache-->>Provider: Cached diff files
    else Cache miss
        Provider->>API: Fetch PR diff
        API-->>Provider: Diff data
        Provider->>Provider: Parse diff
        Provider->>Cache: Store in cache
    end

    Provider->>API: Get file contents
    API->>Repo: Fetch base files
    Repo-->>API: Base file content
    API->>Repo: Fetch head files
    Repo-->>API: Head file content
    API-->>Provider: File contents

    Provider->>Provider: Build FilePatchInfo objects
    Provider-->>Tool: List[FilePatchInfo]

    Tool->>Tool: Process files

    Tool->>Provider: publish_comment(review)
    Provider->>API: Create comment
    API-->>Provider: Comment created
    Provider-->>Tool: Success

    Tool->>Provider: publish_inline_comments(suggestions)
    Provider->>API: Create inline comments
    API-->>Provider: Comments created
    Provider-->>Tool: Success
```

## Clone Operations

```mermaid
flowchart LR
    Start([Clone Request]) --> PrepareURL[Prepare Clone URL<br/>with Auth Token]
    PrepareURL --> CreateTemp[Create Temp Directory]
    CreateTemp --> ShallowClone[Shallow Clone<br/>--depth=1<br/>--filter=blob:none]

    ShallowClone --> CheckTimeout{Timeout<br/>20 seconds?}
    CheckTimeout -->|No| CloneSuccess[Clone Successful]
    CheckTimeout -->|Yes| CloneError[Clone Failed]

    CloneSuccess --> CreateScope[Create ScopedClonedRepo]
    CreateScope --> ReturnPath[Return repo path]
    ReturnPath --> Used([Use repo])

    Used --> Cleanup{Out of<br/>Scope?}
    Cleanup -->|Yes| DeleteRepo[Delete temp repo]
    DeleteRepo --> End([Complete])

    CloneError --> LogError[Log Error]
    LogError --> ReturnNone[Return None]
    ReturnNone --> End

    style ShallowClone fill:#87CEEB
    style CloneSuccess fill:#90EE90
    style CloneError fill:#FFB6C1
    style DeleteRepo fill:#FFD700
```

## Provider-Specific Data Models

```mermaid
erDiagram
    FilePatchInfo ||--|| EDIT_TYPE : has
    FilePatchInfo {
        string base_file
        string head_file
        string patch
        string filename
        int tokens
        EDIT_TYPE edit_type
        string old_filename
        int num_plus_lines
        int num_minus_lines
        string language
        string ai_file_summary
    }

    EDIT_TYPE {
        enum ADDED
        enum DELETED
        enum MODIFIED
        enum RENAMED
        enum UNKNOWN
    }

    IncrementalPR {
        bool is_incremental
        string commits_range
        object first_new_commit
        object last_seen_commit
        string first_new_commit_sha
        string last_seen_commit_sha
    }

    ScopedClonedRepo {
        string path
    }
```

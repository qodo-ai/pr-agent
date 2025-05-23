# RAG Context Enrichment 💎

`Supported Git Platforms: GitHub, Bitbucket Data Center`

!!! info "Prerequisites"
    - RAG is available only for Qodo enterprise plan users, with single tenant or on-premises setup.
    - Database setup and codebase indexing must be completed before proceeding. [Contact support](https://www.qodo.ai/contact/) for more information.

## Overview

### What is RAG Context Enrichment?

A feature that enhances AI analysis by retrieving and referencing relevant code patterns from your project, enabling context-aware insights during code reviews.

### How does RAG Context Enrichment work?

Using Retrieval-Augmented Generation (RAG), it searches your configured repositories for contextually relevant code segments, enriching pull request (PR) insights and accelerating review accuracy.

## Getting started

### Configuration options

In order to enable the RAG feature, add the following lines to your configuration file:

```toml
[rag_arguments]
enable_rag=true
```

!!! example "RAG Arguments Options"

    <table>
      <tr>
        <td><b>enable_rag</b></td>
        <td>If set to true, repository enrichment using RAG will be enabled. Default is false.</td>
      </tr>
      <tr>
        <td><b>rag_repo_list</b></td>
        <td>A list of repositories that will be used by the semantic search for RAG. Use `['all']` to consider the entire codebase or a select list of repositories, for example: ['my-org/my-repo', ...]. Default: the repository from which the PR was opened.</td>
      </tr>
    </table>

### Applications

RAG capability is exclusively available in the following tools:

=== "`/review`"
    The [`/review`](https://qodo-merge-docs.qodo.ai/tools/review/) tool offers the _Focus area from RAG data_ which contains feedback based on the RAG references analysis.
    The complete list of references found relevant to the PR will be shown in the _References_ section, helping developers understand the broader context by exploring the provided references.

    ![RAGed review tool](https://codium.ai/images/pr_agent/rag_review.png){width=640}

=== "`/implement`"
    The [`/implement`](https://qodo-merge-docs.qodo.ai/tools/implement/) tool utilizes the RAG feature to provide comprehensive context of the repository codebase, allowing it to generate more refined code output.
    The _References_ section contains links to the content used to support the code generation.

    ![RAGed implement tool](https://codium.ai/images/pr_agent/rag_implement.png){width=640}

=== "`/ask`"
    The [`/ask`](https://qodo-merge-docs.qodo.ai/tools/ask/) tool can access broader repository context through the RAG feature when answering questions that go beyond the PR scope alone.
    The _References_ section displays the additional repository content consulted to formulate the answer.

    ![RAGed ask tool](https://codium.ai/images/pr_agent/rag_ask.png){width=640}

## Limitations

### Querying the codebase presents significant challenges

- **Search Method**: RAG uses natural language queries to find semantically relevant code sections
- **Result Quality**: No guarantee that RAG results will be useful for all queries
- **Scope Recommendation**: To reduce noise, focus on the PR repository rather than searching across multiple repositories

### This feature has several requirements and restrictions

- **Codebase**: Must be properly indexed for search functionality
- **Security**: Requires secure and private indexed codebase implementation
- **Deployment**: Only available for Qodo Merge Enterprise plan using single tenant or on-premises setup

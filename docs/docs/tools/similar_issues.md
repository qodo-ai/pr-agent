## Overview

The similar issue tool retrieves the most similar issues to the current issue or MR context.
It can be invoked manually by commenting on any PR/MR:

```
/similar_issue
```

## Example usage

![similar_issue_original_issue](https://codium.ai/images/pr_agent/similar_issue_original_issue.png){width=768}

![similar_issue_comment](https://codium.ai/images/pr_agent/similar_issue_comment.png){width=768}

![similar_issue](https://codium.ai/images/pr_agent/similar_issue.png){width=768}

### GitLab example (MR comment)

Comment on an MR:

```
/similar_issue
```

Example output posted to the MR:

```
### Similar Issues
___

1. **[Add retry logic for HTTP client](https://gitlab.example.com/org/repo/-/issues/1)** (score=0.91)
2. **[Cache embeddings for faster review](https://gitlab.example.com/org/repo/-/issues/3)** (score=0.89)
```

Note that to perform retrieval, the `similar_issue` tool indexes all the repo previous issues (once).

## Indexing lifecycle and scope

### What is indexed
- Issues and (optionally) issue comments only. MRs are not indexed.
- Each vector includes `repo`, `username`, `created_at`, and `level` (issue or comment).

### When indexing happens
- On demand, the first time `/similar_issue` is called for a repo.
- A per-repo marker record is stored to avoid re-indexing the same repo.
- On later runs, only new issues are appended (based on issue IDs).

### Query scope
- One shared collection is used, but queries always filter to the current repo.
- GitLab: the query text comes from MR title + description. If the MR text includes `#<issue>`, that GitLab issue is used as the query source, but the output still posts on the MR.

```mermaid
flowchart TD
    A[Comment /similar_issue on MR] --> B{Repo indexed?}
    B -- No --> C[Fetch repo issues + comments]
    C --> D[Embed + upsert vectors to vector DB]
    B -- Yes --> E[Check for new issues]
    E --> F{New issues?}
    F -- Yes --> D
    F -- No --> G[Build query]
    D --> G[Build query]
    G --> H[Query vector DB (filter by repo)]
    H --> I[Post Similar Issues on MR]
```

## Embedding configuration

The tool uses an OpenAI-compatible embeddings endpoint. Configure it in `configuration.toml` (or via env vars):

```
[pr_similar_issue]
embedding_base_url = "https://your-embeddings-host/v1/embeddings"
embedding_model = "intfloat/multilingual-e5-large"
embedding_dim = 1024
embedding_max_tokens = 10000
```

If the embedding endpoint requires auth, set `PR_SIMILAR_ISSUE__EMBEDDING_API_KEY` as an environment variable.

### Selecting a Vector Database

Configure your preferred database by changing the `pr_similar_issue` parameter in `configuration.toml` file.

#### Available Options

Choose from the following Vector Databases:

1. LanceDB
2. Pinecone
3. Qdrant

#### Pinecone Configuration

To use Pinecone with the `similar issue` tool, add these credentials to `.secrets.toml` (or set as environment variables):

```
[pinecone]
api_key = "..."
environment = "..."
```

These parameters can be obtained by registering to [Pinecone](https://app.pinecone.io/?sessionType=signup/).

#### Qdrant Configuration

To use Qdrant with the `similar issue` tool, add these credentials to `.secrets.toml` (or set as environment variables):

```
[qdrant]
url = "https://YOUR-QDRANT-URL" # e.g., https://xxxxxxxx-xxxxxxxx.eu-central-1-0.aws.cloud.qdrant.io
api_key = "..."
```

Then select Qdrant in `configuration.toml`:

```
[pr_similar_issue]
vectordb = "qdrant"
```

You can get a free managed Qdrant instance from [Qdrant Cloud](https://cloud.qdrant.io/).
Ensure the Qdrant collection dimension matches `embedding_dim`. If you change models, set
`pr_similar_issue.force_update_dataset=true` to rebuild the collection.

## How to use

- To invoke the 'similar issue' tool from **CLI**, run:
`python3 cli.py --issue_url=... similar_issue`

- To invoke the 'similar issue' tool via online usage, [comment](https://github.com/Codium-ai/pr-agent/issues/178#issuecomment-1716934893) on a PR/MR:
`/similar_issue`

- GitLab: if run from an MR comment, the query uses the MR title + description. If the MR text includes an issue reference (e.g., `#123`), that issue is used as the query source, but the output is still posted on the MR. If run from CLI with `--issue_url`, the query uses that issue.
- Jira: set `issue_provider="jira"` and configure `[jira]` with either `issue_projects` (or `issue_project_map`) or `issue_jql`. When enabled, `/similar_issue` indexes Jira issues instead of GitLab/GitHub issues. If the MR text includes Jira keys (e.g., `ABC-123`), those tickets are used as the query source; otherwise it uses the MR title + description.

- You can also enable the 'similar issue' tool to run automatically when a new issue is opened, by adding it to the [pr_commands list in the github_app section](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml#L66)

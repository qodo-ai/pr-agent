## Overview

The `help_docs` tool answers a question based on a given relative path of documentation (which defaults to docs/), either from the repository of this merge request or from a given one.
It can be invoked manually by commenting on any PR or Issue:
```
/help_docs "..."
```

## Example usage
#### Asking a question about this repository:
![help_docs on the documentation of this repository](https://codium.ai/images/pr_agent/help_docs_comment.png){width=512}

#### Asking a question about another repository under branch: main:
![help_docs on the documentation of another repository](https://codium.ai/images/pr_agent/help_docs_comment_explicit_git.png){width=512}

#### Response for the first question: 
![help_docs response](https://codium.ai/images/pr_agent/help_docs_response.png){width=512}

## Configuration options

Under the section `pr_help_docs`, the [configuration file](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml#L50) contains options to customize the 'help docs' tool:

- `repo_url`: If not overwritten, will use the repo from where the context came from (issue or PR), otherwise - use the given repo as context.
- `repo_default_branch`: The branch to use in case repo_url overwritten, otherwise - has no effect.
- `docs_path`: Relative path from root of repository (either the one this PR has been issued for, or above repo url).
- `exclude_root_readme`:  Whether or not to exclude the root README file for querying the model.
- `supported_doc_exts` : Which file extensions should be included for the purpose of querying the model.

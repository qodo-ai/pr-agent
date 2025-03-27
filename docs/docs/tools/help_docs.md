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

---
## Run as a GitHub Action

You can use our pre-built Github Action Docker image to run help_docs on any newly created issue, as a Github Action. Here's how:

1) Follow the steps depicted under [Run as a Github Action](https://qodo-merge-docs.qodo.ai/installation/github/#run-as-a-github-action) to create a new workflow, such as:`.github/workflows/help_docs.yml`:

2) Edit your yaml file to the following:

```yaml
name: Run pr agent on every opened issue, respond to user comments on an issue

#When the action is triggered
on:
  issues:
    types: [opened] #New issue

# Read env. variables
env:
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  GITHUB_API_URL: ${{ github.api_url }}
  GIT_REPO_URL: ${{ github.event.repository.clone_url }}
  ISSUE_URL: ${{ github.event.issue.html_url || github.event.comment.html_url }}
  ISSUE_BODY: ${{ github.event.issue.body || github.event.comment.body }}
  OPENAI_KEY: ${{ secrets.OPENAI_KEY }}

# The actual set of actions
jobs:
  issue_agent:
    runs-on: ubuntu-latest
    if: ${{ github.event.sender.type != 'Bot' }} #Do not respond to bots

    # Set required permissions
    permissions:
      contents: read    # For reading repository contents
      issues: write     # For commenting on issues

    steps:
      - name: Run PR Agent on Issues
        if: ${{ env.ISSUE_URL != '' }}
        uses: docker://codiumai/pr-agent:latest
        with:
          entrypoint: /bin/bash #Replace invoking cli.py directly with a shell
          args: |
            -c "cd /app && \
            echo 'Running Issue Agent action step on ISSUE_URL=$ISSUE_URL' && \
            export config__git_provider='github' && \
            export github__user_token=$GITHUB_TOKEN && \            
            export github__base_url=$GITHUB_API_URL && \
            export openai__key=$OPENAI_KEY && \
            export config__verbosity_level=2 && \
            python -m pr_agent.cli --issue_url=$ISSUE_URL help_docs \"$ISSUE_BODY\""
```

3) Following completion of the remaining steps (such as adding secrets and any env. variables), merge this change to your main branch.
When a new issue is opened, you should see a comment from `github-actions` bot with an auto response, assuming the question is a relevant one.
---

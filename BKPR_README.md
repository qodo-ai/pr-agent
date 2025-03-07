# Beekeeper Readme


## Running Beekeeper tests

### Unit Tests

```bash
# from project root
export PYTHONPATH=`pwd`
pytest tests/beekeeper/unittest/guidelines/test_beekeeper_style_guidelines_checker.py  -v
```

## Docker & Build

Image is published to `quay.io/beekeeper/beekeeper-pr-agent:latest`

## Usage for Pull Request Review

Add this Github Action workflow file to your repository in `.github/workflows/pr_agent.yml`:

```yaml
name: PR Agent

on:
  pull_request:
    types: [opened, reopened, ready_for_review]
  issue_comment:

jobs:
  pr_agent_job:
    if: ${{ github.event.sender.type != 'Bot' }}
    runs-on: ubuntu-24.04
    permissions:
      issues: write
      pull-requests: write
      contents: write
    name: Run pr agent on every pull request, respond to user comments
    steps:
      - name: PR Agent action step
        id: pragent
        uses: beekpr/beekeeper-pr-agent@master
        env:
          OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```
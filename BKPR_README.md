# Beekeeper Readme

### Enable PR Best Practices Check in Github Actions

```shell
# add this to the env section of your workflow
GITHUB_ACTION_CONFIG.BEEKEEPER_PR_BEST_PRACTICES: true
```

## Running Beekeeper tests

### Unit Tests

```bash
# from project root
export PYTHONPATH=`pwd`
pytest tests/beekeeper/unittest/  -v

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


### Test Scripts

```shell
# from project root
export GITHUB_TOKEN={YOUR_GITHUB_TOKEN}
export ANTHROPIC_API_KEY={YOUR_ANTHROPIC_API_KEY}

pip install -e .
python3 scripts/beekeeper_run_best_practices_check.py https://github.com/beekpr/beekeeper-analytics/pull/546


```
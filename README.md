<img width="697" height="176" alt="image" src="https://github.com/user-attachments/assets/81c96bcc-4ec3-45b2-a69e-d116bb75b22b" />

<a href="https://github.com/Codium-ai/pr-agent/commits/main">
<img alt="GitHub" src="https://img.shields.io/github/last-commit/Codium-ai/pr-agent/main?style=for-the-badge" height="20">
</a>

<br />

# 🚀 The first AI Code Reviewer

PR-Agent is an open-source, AI-powered code review agent. It is a legacy project of Qodo that is now maintained by the community.

> NOTE: It is not related to the main product offering of Qodo's code review product.

Qodo now offers a [free tier for AI code review](https://www.qodo.ai/get-started/) to easily integrate with GitHub, GitLab, Bitbucket, and Azure DevOps, with feature-rich capabilities for high-quality context-aware code reviews.

## Table of Contents

- [Getting Started](#getting-started)
- [Why Use PR-Agent?](#why-use-pr-agent)
- [Features](#features)
- [See It in Action](#see-it-in-action)
- [Try It Now](#try-it-now)
- [How It Works](#how-it-works)
- [Data Privacy](#data-privacy)
- [Contributing](#contributing)

## Getting Started

### 🚀 Quick Start for PR-Agent

#### 1. Try it Instantly (No Setup)
Test PR-Agent on any public GitHub repository by commenting `@CodiumAI-Agent /improve`

#### 2. GitHub Action (Recommended)
Add automated PR reviews to your repository with a simple workflow file:
```yaml
# .github/workflows/pr-agent.yml
name: PR Agent
on:
  pull_request:
    types: [opened, synchronize]
jobs:
  pr_agent_job:
    runs-on: ubuntu-latest
    steps:
    - name: PR Agent action step
      uses: Codium-ai/pr-agent@main
      env:
        OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```
[Full GitHub Action setup guide](https://qodo-merge-docs.qodo.ai/installation/github/#run-as-a-github-action)

#### 3. CLI Usage (Local Development)
Run PR-Agent locally on your repository:
```bash
pip install pr-agent
export OPENAI_KEY=your_key_here
pr-agent --pr_url https://github.com/owner/repo/pull/123 review
```
[Complete CLI setup guide](https://qodo-merge-docs.qodo.ai/usage-guide/automations_and_usage/#local-repo-cli)

#### 4. Other Platforms
- [GitLab webhook setup](https://qodo-merge-docs.qodo.ai/installation/gitlab/)
- [BitBucket app installation](https://qodo-merge-docs.qodo.ai/installation/bitbucket/)
- [Azure DevOps setup](https://qodo-merge-docs.qodo.ai/installation/azure/)

[//]: # (## News and Updates)

[//]: # ()
[//]: # (## Aug 8, 2025)

[//]: # ()
[//]: # (Added full support for GPT-5 models. View the [benchmark results]&#40;https://qodo-merge-docs.qodo.ai/pr_benchmark/#pr-benchmark-results&#41; for details on the performance of GPT-5 models in PR-Agent.)

[//]: # ()
[//]: # ()
[//]: # (## Jul 17, 2025)

[//]: # ()
[//]: # (Introducing `/compliance`, a new Qodo Merge 💎 tool that runs comprehensive checks for security, ticket requirements, codebase duplication, and custom organizational rules. )

[//]: # ()
[//]: # (<img width="384" alt="compliance-image" src="https://codium.ai/images/pr_agent/compliance_partial.png"/>)

[//]: # ()
[//]: # (Read more about it [here]&#40;https://qodo-merge-docs.qodo.ai/tools/compliance/&#41;)

[//]: # ()
[//]: # ()
[//]: # (## Jul 1, 2025)

[//]: # (You can now receive automatic feedback from Qodo Merge in your local IDE after each commit. Read more about it [here]&#40;https://github.com/qodo-ai/agents/tree/main/agents/qodo-merge-post-commit&#41;.)

[//]: # ()
[//]: # ()
[//]: # (## Jun 21, 2025)

[//]: # ()
[//]: # (v0.30 was [released]&#40;https://github.com/qodo-ai/pr-agent/releases&#41;)

[//]: # ()
[//]: # ()
[//]: # (## Jun 3, 2025)

[//]: # ()
[//]: # (Qodo Merge now offers a simplified free tier 💎.)

[//]: # (Organizations can use Qodo Merge at no cost, with a [monthly limit]&#40;https://qodo-merge-docs.qodo.ai/installation/qodo_merge/#cloud-users&#41; of 75 PR reviews per organization.)

[//]: # ()
[//]: # ()
[//]: # (## Apr 30, 2025)

[//]: # ()
[//]: # (A new feature is now available in the `/improve` tool for Qodo Merge 💎 - Chat on code suggestions.)

[//]: # ()
[//]: # (<img width="512" alt="image" src="https://codium.ai/images/pr_agent/improve_chat_on_code_suggestions_ask.png" />)

[//]: # ()
[//]: # (Read more about it [here]&#40;https://qodo-merge-docs.qodo.ai/tools/improve/#chat-on-code-suggestions&#41;.)

[//]: # ()
[//]: # ()
[//]: # (## Apr 16, 2025)

[//]: # ()
[//]: # (New tool for Qodo Merge 💎 - `/scan_repo_discussions`.)

[//]: # ()
[//]: # (<img width="635" alt="image" src="https://codium.ai/images/pr_agent/scan_repo_discussions_2.png" />)

[//]: # ()
[//]: # (Read more about it [here]&#40;https://qodo-merge-docs.qodo.ai/tools/scan_repo_discussions/&#41;.)

## Why Use PR-Agent?

### 🎯 Built for Real Development Teams

**Fast & Affordable**: Each tool (`/review`, `/improve`, `/ask`) uses a single LLM call (~30 seconds, low cost)

**Handles Any PR Size**: Our [PR Compression strategy](https://qodo-merge-docs.qodo.ai/core-abilities/#pr-compression-strategy) effectively processes both small and large PRs

**Highly Customizable**: JSON-based prompting allows easy customization of review categories and behavior via [configuration files](pr_agent/settings/configuration.toml)

**Platform Agnostic**: 
- **Git Providers**: GitHub, GitLab, BitBucket, Azure DevOps, Gitea
- **Deployment**: CLI, GitHub Actions, Docker, self-hosted, webhooks
- **AI Models**: OpenAI GPT, Claude, Deepseek, and more

**Open Source Benefits**:
- Full control over your data and infrastructure
- Customize prompts and behavior for your team's needs
- No vendor lock-in
- Community-driven development

## Features

<div style="text-align:left;">

PR-Agent offers comprehensive pull request functionalities integrated with various git providers:

|                                                         |                                                                                        | GitHub | GitLab | Bitbucket | Azure DevOps | Gitea |
|---------------------------------------------------------|----------------------------------------------------------------------------------------|:------:|:------:|:---------:|:------------:|:-----:|
| [TOOLS](https://qodo-merge-docs.qodo.ai/tools/)         | [Describe](https://qodo-merge-docs.qodo.ai/tools/describe/)                            |   ✅   |   ✅   |    ✅     |      ✅      |  ✅   |
|                                                         | [Review](https://qodo-merge-docs.qodo.ai/tools/review/)                                |   ✅   |   ✅   |    ✅     |      ✅      |  ✅   |
|                                                         | [Improve](https://qodo-merge-docs.qodo.ai/tools/improve/)                              |   ✅   |   ✅   |    ✅     |      ✅      |  ✅   |
|                                                         | [Ask](https://qodo-merge-docs.qodo.ai/tools/ask/)                                      |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | ⮑ [Ask on code lines](https://qodo-merge-docs.qodo.ai/tools/ask/#ask-lines)            |   ✅   |   ✅   |           |              |       |
|                                                         | [Help Docs](https://qodo-merge-docs.qodo.ai/tools/help_docs/?h=auto#auto-approval)     |   ✅   |   ✅   |    ✅     |              |       |
|                                                         | [Update CHANGELOG](https://qodo-merge-docs.qodo.ai/tools/update_changelog/)            |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         |                                                                                                                     |        |        |           |              |       |
| [USAGE](https://qodo-merge-docs.qodo.ai/usage-guide/)   | [CLI](https://qodo-merge-docs.qodo.ai/usage-guide/automations_and_usage/#local-repo-cli)                            |   ✅   |   ✅   |    ✅     |      ✅      |  ✅   |
|                                                         | [App / webhook](https://qodo-merge-docs.qodo.ai/usage-guide/automations_and_usage/#github-app)                      |   ✅   |   ✅   |    ✅     |      ✅      |  ✅   |
|                                                         | [Tagging bot](https://github.com/Codium-ai/pr-agent#try-it-now)                                                     |   ✅   |        |           |              |       |
|                                                         | [Actions](https://qodo-merge-docs.qodo.ai/installation/github/#run-as-a-github-action)                              |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         |                                                                                                                     |        |        |           |              |       |
| [CORE](https://qodo-merge-docs.qodo.ai/core-abilities/) | [Adaptive and token-aware file patch fitting](https://qodo-merge-docs.qodo.ai/core-abilities/compression_strategy/) |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | [Chat on code suggestions](https://qodo-merge-docs.qodo.ai/core-abilities/chat_on_code_suggestions/)                |   ✅   |  ✅   |           |              |       |
|                                                         | [Dynamic context](https://qodo-merge-docs.qodo.ai/core-abilities/dynamic_context/)                                  |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | [Fetching ticket context](https://qodo-merge-docs.qodo.ai/core-abilities/fetching_ticket_context/)                  |   ✅    |  ✅    |     ✅     |              |       |
|                                                         | [Incremental Update](https://qodo-merge-docs.qodo.ai/core-abilities/incremental_update/)                            |   ✅    |       |           |              |       |
|                                                         | [Interactivity](https://qodo-merge-docs.qodo.ai/core-abilities/interactivity/)                                      |   ✅   |  ✅   |           |              |       |
|                                                         | [Local and global metadata](https://qodo-merge-docs.qodo.ai/core-abilities/metadata/)                               |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | [Multiple models support](https://qodo-merge-docs.qodo.ai/usage-guide/changing_a_model/)                            |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | [PR compression](https://qodo-merge-docs.qodo.ai/core-abilities/compression_strategy/)                              |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | [RAG context enrichment](https://qodo-merge-docs.qodo.ai/core-abilities/rag_context_enrichment/)                    |   ✅    |       |    ✅     |              |       |
|                                                         | [Self reflection](https://qodo-merge-docs.qodo.ai/core-abilities/self_reflection/)                                  |   ✅   |   ✅   |    ✅     |      ✅      |       |

[//]: # (- Support for additional git providers is described in [here]&#40;./docs/Full_environments.md&#41;)
___

## See It in Action

</div>
<h4><a href="https://github.com/Codium-ai/pr-agent/pull/530">/describe</a></h4>
<div align="center">
<p float="center">
<img src="https://www.codium.ai/images/pr_agent/describe_new_short_main.png" width="512">
</p>
</div>
<hr>

<h4><a href="https://github.com/Codium-ai/pr-agent/pull/732#issuecomment-1975099151">/review</a></h4>
<div align="center">
<p float="center">
<kbd>
<img src="https://www.codium.ai/images/pr_agent/review_new_short_main.png" width="512">
</kbd>
</p>
</div>
<hr>

<h4><a href="https://github.com/Codium-ai/pr-agent/pull/732#issuecomment-1975099159">/improve</a></h4>
<div align="center">
<p float="center">
<kbd>
<img src="https://www.codium.ai/images/pr_agent/improve_new_short_main.png" width="512">
</kbd>
</p>
</div>

<div align="left">

</div>
<hr>

## Provider-agnostic push outputs and Slack relay

PR-Agent can optionally emit review results to external sinks without calling git provider APIs.
This is disabled by default. To enable and forward to Slack via a lightweight relay:

1) Start the relay (in a separate shell):
   - Set an Incoming Webhook URL for Slack:
     - CMD:  set SLACK_WEBHOOK_URL=https://hooks.slack.com/services/TXXXX/BXXXX/XXXXXXXX
     - PS:   $env:SLACK_WEBHOOK_URL="https://hooks.slack.com/services/TXXXX/BXXXX/XXXXXXXX"
   - Run:
     uvicorn pr_agent.servers.push_outputs_relay:app --host 0.0.0.0 --port 8000

2) In your repository, configure PR-Agent to emit to the relay by creating .pr_agent.toml:

```
[push_outputs]
enable = true
channels = ["webhook"]
webhook_url = "http://localhost:8000/relay"
presentation = "markdown"
```

Notes:
- This mechanism is provider-agnostic and uses minimal API calls.
- You can also use the "file" channel to append JSONL records locally.
- The relay transforms the generic payload into Slack’s Incoming Webhook schema.

## Try It Now

Try the GPT-5 powered PR-Agent instantly on _your public GitHub repository_. Just mention `@CodiumAI-Agent` and add the desired command in any PR comment. The agent will generate a response based on your command.
For example, add a comment to any pull request with the following text:

```
@CodiumAI-Agent /review
```

and the agent will respond with a review of your PR.

Note that this is a promotional bot, suitable only for initial experimentation.
It does not have 'edit' access to your repo, for example, so it cannot update the PR description or add labels (`@CodiumAI-Agent /describe` will publish PR description as a comment). In addition, the bot cannot be used on private repositories, as it does not have access to the files there.


## How It Works

The following diagram illustrates PR-Agent tools and their flow:

![PR-Agent Tools](https://www.qodo.ai/images/pr_agent/diagram-v0.9.png)

## Data Privacy

### Self-hosted PR-Agent

- If you host PR-Agent with your OpenAI API key, it is between you and OpenAI. You can read their API data privacy policy here:
https://openai.com/enterprise-privacy

## Contributing

To contribute to the project, get started by reading our [Contributing Guide](https://github.com/qodo-ai/pr-agent/blob/b09eec265ef7d36c232063f76553efb6b53979ff/CONTRIBUTING.md).


## ❤️ Community

This open-source release remains here as a community contribution from Qodo — the origin of modern AI-powered code collaboration. We’re proud to share it and inspire developers worldwide.

The project now has its first external maintainer, Naor ([@naorpeled](https://github.com/naorpeled)), and is currently in the process of being donated to an open-source foundation.
<div align="center">

<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://www.qodo.ai/wp-content/uploads/2025/02/PR-Agent-Purple-2.png">
  <source media="(prefers-color-scheme: light)" srcset="https://www.qodo.ai/wp-content/uploads/2025/02/PR-Agent-Purple-2.png">
  <img src="https://codium.ai/images/pr_agent/logo-light.png" alt="logo" width="330">

</picture>
<br/>

[Installation Guide](https://qodo-merge-docs.qodo.ai/installation/) |
[Usage Guide](https://qodo-merge-docs.qodo.ai/usage-guide/) |
[Tools Guide](https://qodo-merge-docs.qodo.ai/tools/) |
[Qodo Merge](https://qodo-merge-docs.qodo.ai/overview/pr_agent_pro/) 💎

## Open-Source AI-Powered Code Review Tool

**PR-Agent** is a free, open-source tool that provides AI-powered code review and PR assistance. Run it locally, on your CI/CD, or self-host it.

**[Qodo Merge](https://qodo-merge-docs.qodo.ai/overview/pr_agent_pro/) 💎** is the hosted, enterprise version with additional features, zero-setup, and priority support.

---

### Quick Start Options

| **Option** | **Best For** | **Setup Time** | **Cost** |
|------------|--------------|----------------|----------|
| **[PR-Agent (Open Source)](#-quick-start-for-pr-agent-open-source)** | Developers who want full control, self-hosting, or custom integrations | 5-15 minutes | Free |
| **[Qodo Merge](#-try-qodo-merge-zero-setup)** | Teams wanting zero-setup, enhancing the open-source features, additional enterprise features, and managed hosting | 2 minutes | Free tier available |
</div>

[![Static Badge](https://img.shields.io/badge/Chrome-Extension-violet)](https://chromewebstore.google.com/detail/qodo-merge-ai-powered-cod/ephlnjeghhogofkifjloamocljapahnl)
[![Static Badge](https://img.shields.io/badge/Pro-App-blue)](https://github.com/apps/qodo-merge-pro/)
[![Static Badge](https://img.shields.io/badge/OpenSource-App-red)](https://github.com/apps/qodo-merge-pro-for-open-source/)
[![Discord](https://badgen.net/badge/icon/discord?icon=discord&label&color=purple)](https://discord.com/invite/SgSxuQ65GF)
<a href="https://github.com/Codium-ai/pr-agent/commits/main">
<img alt="GitHub" src="https://img.shields.io/github/last-commit/Codium-ai/pr-agent/main?style=for-the-badge" height="20">
</a>
</div>

## Table of Contents

- [PR-Agent vs Qodo Merge](#pr-agent-vs-qodo-merge)
- [Getting Started](#getting-started)
- [News and Updates](#news-and-updates)
- [Why Use PR-Agent?](#why-use-pr-agent)
- [Features](#features)
- [See It in Action](#see-it-in-action)
- [Try It Now](#try-it-now)
- [Qodo Merge 💎](#qodo-merge-)
- [How It Works](#how-it-works)
- [Data Privacy](#data-privacy)
- [Contributing](#contributing)
- [Links](#links)

## PR-Agent vs Qodo Merge

### PR-Agent (This Repository) - Open Source

✅ **What you get:**
- Complete source code access and customization
- Self-hosted deployment options
- All core AI review tools (`/describe`, `/review`, `/improve`, `/ask`)
- Support for GitHub, GitLab, BitBucket, Azure DevOps
- CLI usage for local development
- Free forever

⚙️ **What you need to manage:**
- Your own API keys (OpenAI, Claude, etc.)
- Infrastructure and hosting
- Updates and maintenance
- Configuration management

### Qodo Merge - Hosted Solution

✅ **What you get (everything above plus):**
- Zero-setup installation (2-minute GitHub app install)
- Managed infrastructure and automatic updates
- Advanced features: CI feedback, code suggestions tracking, custom prompts
- Priority support and feature requests
- Enhanced privacy with zero data retention
- Free tier: 75 PR reviews/month per organization

💰 **Pricing:**
- Free tier available
- Paid plans for unlimited usage
- [View pricing details](https://www.qodo.ai/pricing/)

**👨‍💻 Developer Recommendation:** Start with PR-Agent if you want to experiment, customize heavily, or have specific self-hosting requirements. Choose Qodo Merge if you want to focus on coding rather than tool maintenance.

## Getting Started

### 🚀 Quick Start for PR-Agent (Open Source)

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

### 💎 Try Qodo Merge (Zero Setup)

If you prefer a hosted solution without managing infrastructure:

1. **[Install Qodo Merge GitHub App](https://github.com/marketplace/qodo-merge-pro)** (2 minutes)
2. **[FREE for Open Source](https://github.com/marketplace/qodo-merge-pro-for-open-source)**: Full features, zero cost for public repos
3. **Free Tier**: 75 PR reviews/month for private repos
4. **[View Plans & Pricing](https://www.qodo.ai/pricing/)**

[Complete Qodo Merge setup guide](https://qodo-merge-docs.qodo.ai/installation/qodo_merge/)

### 💻 Local IDE Integration
Receive automatic feedback in your IDE after each commit: [Qodo Merge post-commit agent](https://github.com/qodo-ai/agents/tree/main/agents/qodo-merge-post-commit)


## News and Updates

## Aug 8, 2025

Added full support for GPT-5 models. View the [benchmark results](https://qodo-merge-docs.qodo.ai/pr_benchmark/#pr-benchmark-results) for details on the performance of GPT-5 models in PR-Agent.


## Jul 17, 2025

Introducing `/compliance`, a new Qodo Merge 💎 tool that runs comprehensive checks for security, ticket requirements, codebase duplication, and custom organizational rules. 

<img width="384" alt="compliance-image" src="https://codium.ai/images/pr_agent/compliance_partial.png"/>

Read more about it [here](https://qodo-merge-docs.qodo.ai/tools/compliance/)


## Jul 1, 2025
You can now receive automatic feedback from Qodo Merge in your local IDE after each commit. Read more about it [here](https://github.com/qodo-ai/agents/tree/main/agents/qodo-merge-post-commit).


## Jun 21, 2025

v0.30 was [released](https://github.com/qodo-ai/pr-agent/releases)


## Jun 3, 2025

Qodo Merge now offers a simplified free tier 💎.
Organizations can use Qodo Merge at no cost, with a [monthly limit](https://qodo-merge-docs.qodo.ai/installation/qodo_merge/#cloud-users) of 75 PR reviews per organization.


## Apr 30, 2025

A new feature is now available in the `/improve` tool for Qodo Merge 💎 - Chat on code suggestions.

<img width="512" alt="image" src="https://codium.ai/images/pr_agent/improve_chat_on_code_suggestions_ask.png" />

Read more about it [here](https://qodo-merge-docs.qodo.ai/tools/improve/#chat-on-code-suggestions).


## Apr 16, 2025

New tool for Qodo Merge 💎 - `/scan_repo_discussions`.

<img width="635" alt="image" src="https://codium.ai/images/pr_agent/scan_repo_discussions_2.png" />

Read more about it [here](https://qodo-merge-docs.qodo.ai/tools/scan_repo_discussions/).

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

PR-Agent and Qodo Merge offer comprehensive pull request functionalities integrated with various git providers:

|                                                         |                                                                                        | GitHub | GitLab | Bitbucket | Azure DevOps | Gitea |
|---------------------------------------------------------|----------------------------------------------------------------------------------------|:------:|:------:|:---------:|:------------:|:-----:|
| [TOOLS](https://qodo-merge-docs.qodo.ai/tools/)         | [Describe](https://qodo-merge-docs.qodo.ai/tools/describe/)                            |   ✅   |   ✅   |    ✅     |      ✅      |  ✅   |
|                                                         | [Review](https://qodo-merge-docs.qodo.ai/tools/review/)                                |   ✅   |   ✅   |    ✅     |      ✅      |  ✅   |
|                                                         | [Improve](https://qodo-merge-docs.qodo.ai/tools/improve/)                              |   ✅   |   ✅   |    ✅     |      ✅      |  ✅   |
|                                                         | [Ask](https://qodo-merge-docs.qodo.ai/tools/ask/)                                      |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | ⮑ [Ask on code lines](https://qodo-merge-docs.qodo.ai/tools/ask/#ask-lines)            |   ✅   |   ✅   |           |              |       |
|                                                         | [Help Docs](https://qodo-merge-docs.qodo.ai/tools/help_docs/?h=auto#auto-approval)     |   ✅   |   ✅   |    ✅     |              |       |
|                                                         | [Update CHANGELOG](https://qodo-merge-docs.qodo.ai/tools/update_changelog/)            |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | [Add Documentation](https://qodo-merge-docs.qodo.ai/tools/documentation/) 💎           |   ✅   |   ✅   |           |              |       |
|                                                         | [Analyze](https://qodo-merge-docs.qodo.ai/tools/analyze/) 💎                           |   ✅   |   ✅   |           |              |       |
|                                                         | [Auto-Approve](https://qodo-merge-docs.qodo.ai/tools/improve/?h=auto#auto-approval) 💎 |   ✅   |   ✅   |    ✅     |              |       |
|                                                         | [CI Feedback](https://qodo-merge-docs.qodo.ai/tools/ci_feedback/) 💎                   |   ✅   |        |           |              |       |
|                                                         | [Compliance](https://qodo-merge-docs.qodo.ai/tools/compliance/) 💎                     |   ✅   |    ✅   |    ✅     |              |       |
|                                                         | [Custom Prompt](https://qodo-merge-docs.qodo.ai/tools/custom_prompt/) 💎                                            |   ✅   |   ✅   |    ✅     |              |       |
|                                                         | [Generate Custom Labels](https://qodo-merge-docs.qodo.ai/tools/custom_labels/) 💎                                   |   ✅   |   ✅   |           |              |       |
|                                                         | [Generate Tests](https://qodo-merge-docs.qodo.ai/tools/test/) 💎                                                    |   ✅   |   ✅   |           |              |       |
|                                                         | [Implement](https://qodo-merge-docs.qodo.ai/tools/implement/) 💎                                                    |   ✅   |   ✅   |    ✅     |              |       |
|                                                         | [Scan Repo Discussions](https://qodo-merge-docs.qodo.ai/tools/scan_repo_discussions/) 💎                            |   ✅   |        |           |              |       |
|                                                         | [Similar Code](https://qodo-merge-docs.qodo.ai/tools/similar_code/) 💎                                              |   ✅   |        |           |              |       |
|                                                         | [Utilizing Best Practices](https://qodo-merge-docs.qodo.ai/tools/improve/#best-practices) 💎                        |   ✅   |   ✅   |    ✅     |              |       |
|                                                         | [PR Chat](https://qodo-merge-docs.qodo.ai/chrome-extension/features/#pr-chat) 💎                                    |   ✅   |        |           |              |       |
|                                                         | [PR to Ticket](https://qodo-merge-docs.qodo.ai/tools/pr_to_ticket/) 💎                                              |   ✅   |   ✅   |    ✅     |              |       |
|                                                         | [Suggestion Tracking](https://qodo-merge-docs.qodo.ai/tools/improve/#suggestion-tracking) 💎                        |   ✅   |   ✅   |           |              |       |
|                                                         |                                                                                                                     |        |        |           |              |       |
| [USAGE](https://qodo-merge-docs.qodo.ai/usage-guide/)   | [CLI](https://qodo-merge-docs.qodo.ai/usage-guide/automations_and_usage/#local-repo-cli)                            |   ✅   |   ✅   |    ✅     |      ✅      |  ✅   |
|                                                         | [App / webhook](https://qodo-merge-docs.qodo.ai/usage-guide/automations_and_usage/#github-app)                      |   ✅   |   ✅   |    ✅     |      ✅      |  ✅   |
|                                                         | [Tagging bot](https://github.com/Codium-ai/pr-agent#try-it-now)                                                     |   ✅   |        |           |              |       |
|                                                         | [Actions](https://qodo-merge-docs.qodo.ai/installation/github/#run-as-a-github-action)                              |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         |                                                                                                                     |        |        |           |              |       |
| [CORE](https://qodo-merge-docs.qodo.ai/core-abilities/) | [Adaptive and token-aware file patch fitting](https://qodo-merge-docs.qodo.ai/core-abilities/compression_strategy/) |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | [Auto Best Practices 💎](https://qodo-merge-docs.qodo.ai/core-abilities/auto_best_practices/)                       |   ✅   |      |         |            |   |
|                                                         | [Chat on code suggestions](https://qodo-merge-docs.qodo.ai/core-abilities/chat_on_code_suggestions/)                |   ✅   |  ✅   |           |              |       |
|                                                         | [Code Validation 💎](https://qodo-merge-docs.qodo.ai/core-abilities/code_validation/)                               |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | [Dynamic context](https://qodo-merge-docs.qodo.ai/core-abilities/dynamic_context/)                                  |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | [Fetching ticket context](https://qodo-merge-docs.qodo.ai/core-abilities/fetching_ticket_context/)                  |   ✅    |  ✅    |     ✅     |              |       |
|                                                         | [Global and wiki configurations](https://qodo-merge-docs.qodo.ai/usage-guide/configuration_options/) 💎             |   ✅   |   ✅   |    ✅     |              |       |
|                                                         | [Impact Evaluation](https://qodo-merge-docs.qodo.ai/core-abilities/impact_evaluation/) 💎                           |   ✅   |   ✅   |           |              |       |
|                                                         | [Incremental Update](https://qodo-merge-docs.qodo.ai/core-abilities/incremental_update/)                            |   ✅    |       |           |              |       |
|                                                         | [Interactivity](https://qodo-merge-docs.qodo.ai/core-abilities/interactivity/)                                      |   ✅   |  ✅   |           |              |       |
|                                                         | [Local and global metadata](https://qodo-merge-docs.qodo.ai/core-abilities/metadata/)                               |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | [Multiple models support](https://qodo-merge-docs.qodo.ai/usage-guide/changing_a_model/)                            |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | [PR compression](https://qodo-merge-docs.qodo.ai/core-abilities/compression_strategy/)                              |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | [PR interactive actions](https://www.qodo.ai/images/pr_agent/pr-actions.mp4) 💎                                     |   ✅   |   ✅   |           |              |       |
|                                                         | [RAG context enrichment](https://qodo-merge-docs.qodo.ai/core-abilities/rag_context_enrichment/)                    |   ✅    |       |    ✅     |              |       |
|                                                         | [Self reflection](https://qodo-merge-docs.qodo.ai/core-abilities/self_reflection/)                                  |   ✅   |   ✅   |    ✅     |      ✅      |       |
|                                                         | [Static code analysis](https://qodo-merge-docs.qodo.ai/core-abilities/static_code_analysis/) 💎                     |   ✅   |   ✅   |           |              |       |
- 💎 means this feature is available only in [Qodo Merge](https://www.qodo.ai/pricing/)

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

## Try It Now

Try the GPT-5 powered PR-Agent instantly on _your public GitHub repository_. Just mention `@CodiumAI-Agent` and add the desired command in any PR comment. The agent will generate a response based on your command.
For example, add a comment to any pull request with the following text:

```
@CodiumAI-Agent /review
```

and the agent will respond with a review of your PR.

Note that this is a promotional bot, suitable only for initial experimentation.
It does not have 'edit' access to your repo, for example, so it cannot update the PR description or add labels (`@CodiumAI-Agent /describe` will publish PR description as a comment). In addition, the bot cannot be used on private repositories, as it does not have access to the files there.

---

## Qodo Merge 💎

[Qodo Merge](https://www.qodo.ai/pricing/) is the hosted version of PR-Agent with additional enterprise features.

### Key Differences from Open Source PR-Agent:

**Infrastructure & Management:**
- Fully managed hosting and automatic updates
- Zero-setup installation (GitHub/GitLab/BitBucket app)
- No need to manage API keys or infrastructure

**Enhanced Privacy:**
- Zero data retention policy
- No data used for model training
- Enterprise-grade security

**Additional Features:**
- Advanced code suggestions with tracking
- CI feedback analysis
- Custom prompts and labels
- Static code analysis integration
- Priority support

**Pricing:**
- Free tier: 75 PR reviews/month per organization
- Paid plans for unlimited usage
- Free for open source projects

See [complete feature comparison](https://qodo-merge-docs.qodo.ai/overview/pr_agent_pro/) for detailed differences.

## How It Works

The following diagram illustrates PR-Agent tools and their flow:

![PR-Agent Tools](https://www.qodo.ai/images/pr_agent/diagram-v0.9.png)

Check out the [PR Compression strategy](https://qodo-merge-docs.qodo.ai/core-abilities/#pr-compression-strategy) page for more details on how we convert a code diff to a manageable LLM prompt

## Data Privacy

### Self-hosted PR-Agent

- If you host PR-Agent with your OpenAI API key, it is between you and OpenAI. You can read their API data privacy policy here:
https://openai.com/enterprise-privacy

### Qodo-hosted Qodo Merge 💎

- When using Qodo Merge 💎, hosted by Qodo, we will not store any of your data, nor will we use it for training. You will also benefit from an OpenAI account with zero data retention.

- For certain clients, Qodo-hosted Qodo Merge will use Qodo’s proprietary models — if this is the case, you will be notified.

- No passive collection of Code and Pull Requests’ data — Qodo Merge will be active only when you invoke it, and it will then extract and analyze only data relevant to the executed command and queried pull request.

### Qodo Merge Chrome extension

- The [Qodo Merge Chrome extension](https://chromewebstore.google.com/detail/qodo-merge-ai-powered-cod/ephlnjeghhogofkifjloamocljapahnl) serves solely to modify the visual appearance of a GitHub PR screen. It does not transmit any user's repo or pull request code. Code is only sent for processing when a user submits a GitHub comment that activates a PR-Agent tool, in accordance with the standard privacy policy of Qodo-Merge.

## Contributing

To contribute to the project, get started by reading our [Contributing Guide](https://github.com/qodo-ai/pr-agent/blob/b09eec265ef7d36c232063f76553efb6b53979ff/CONTRIBUTING.md).

## Links

- Discord community: https://discord.com/invite/SgSxuQ65GF
- Qodo site: https://www.qodo.ai/
- Blog: https://www.qodo.ai/blog/
- Troubleshooting: https://www.qodo.ai/blog/technical-faq-and-troubleshooting/
- Support: support@qodo.ai

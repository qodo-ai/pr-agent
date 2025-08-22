# Overview

[PR-Agent](https://github.com/Codium-ai/pr-agent) is an open-source tool to help efficiently review and handle pull requests.
Qodo Merge is a hosted version of PR-Agent, designed for companies and teams that require additional features and capabilities

- See the [Installation Guide](./installation/index.md) for instructions on installing and running the tool on different git platforms.

- See the [Usage Guide](./usage-guide/index.md) for instructions on running commands via different interfaces, including _CLI_, _online usage_, or by _automatically triggering_ them when a new PR is opened.

- See the [Tools Guide](./tools/index.md) for a detailed description of the different tools.

- See the [Video Tutorials](https://www.youtube.com/playlist?list=PLRTpyDOSgbwFMA_VBeKMnPLaaZKwjGBFT) for practical demonstrations on how to use the tools.

## Docs Smart Search

To search the documentation site using natural language:

1) Comment `/help "your question"` in either:

   - A pull request where Qodo Merge is installed
   - A [PR Chat](https://qodo-merge-docs.qodo.ai/chrome-extension/features/#pr-chat)

2) The bot will respond with an [answer](https://github.com/Codium-ai/pr-agent/pull/1241#issuecomment-2365259334) that includes relevant documentation links.

## Features

PR-Agent and Qodo Merge offer comprehensive pull request functionalities integrated with various git providers:

|       |                                                                                                                     | GitHub | GitLab | Bitbucket | Azure DevOps | Gitea |
| ----- |---------------------------------------------------------------------------------------------------------------------|:------:|:------:|:---------:|:------------:|:-----:|
| [TOOLS](https://qodo-merge-docs.qodo.ai/tools/) | [Describe](https://qodo-merge-docs.qodo.ai/tools/describe/)                                                         |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |
|       | [Review](https://qodo-merge-docs.qodo.ai/tools/review/)                                                             |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |
|       | [Improve](https://qodo-merge-docs.qodo.ai/tools/improve/)                                                           |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |
|       | [Ask](https://qodo-merge-docs.qodo.ai/tools/ask/)                                                                   |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       | ⮑ [Ask on code lines](https://qodo-merge-docs.qodo.ai/tools/ask/#ask-lines)                                         |   ✅   |   ✅   |           |              |       |
|       | [Help Docs](https://qodo-merge-docs.qodo.ai/tools/help_docs/?h=auto#auto-approval)                                  |   ✅   |   ✅   |    ✅     |              |       |
|       | [Update CHANGELOG](https://qodo-merge-docs.qodo.ai/tools/update_changelog/)                                         |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       | [Add Documentation](https://qodo-merge-docs.qodo.ai/tools/documentation/) 💎                                        |   ✅   |   ✅   |           |              |       |
|       | [Analyze](https://qodo-merge-docs.qodo.ai/tools/analyze/) 💎                                                        |   ✅   |   ✅   |           |              |       |
|       | [Auto-Approve](https://qodo-merge-docs.qodo.ai/tools/improve/?h=auto#auto-approval) 💎                              |   ✅   |   ✅   |    ✅     |              |       |
|       | [CI Feedback](https://qodo-merge-docs.qodo.ai/tools/ci_feedback/) 💎                                                |   ✅   |        |           |              |       |
|       | [Compliance](https://qodo-merge-docs.qodo.ai/tools/compliance/) 💎                                                  |   ✅   |   ✅   |    ✅     |              |       |
|       | [Custom Prompt](https://qodo-merge-docs.qodo.ai/tools/custom_prompt/) 💎                                            |   ✅   |   ✅   |    ✅     |              |       |
|       | [Generate Custom Labels](https://qodo-merge-docs.qodo.ai/tools/custom_labels/) 💎                                   |   ✅   |   ✅   |           |              |       |
|       | [Generate Tests](https://qodo-merge-docs.qodo.ai/tools/test/) 💎                                                    |   ✅   |   ✅   |           |              |       |
|       | [Implement](https://qodo-merge-docs.qodo.ai/tools/implement/) 💎                                                    |   ✅   |   ✅   |    ✅     |              |       |
|       | [PR Chat](https://qodo-merge-docs.qodo.ai/chrome-extension/features/#pr-chat) 💎                                    |   ✅   |        |           |              |       |
|       | [PR to Ticket](https://qodo-merge-docs.qodo.ai/tools/pr_to_ticket/) 💎                                              |   ✅   |   ✅   |    ✅     |              |       |
|       | [Scan Repo Discussions](https://qodo-merge-docs.qodo.ai/tools/scan_repo_discussions/) 💎                            |   ✅   |        |           |              |       |
|       | [Similar Code](https://qodo-merge-docs.qodo.ai/tools/similar_code/) 💎                                              |   ✅   |        |           |              |       |
|       | [Suggestion Tracking](https://qodo-merge-docs.qodo.ai/tools/improve/#suggestion-tracking) 💎                        |   ✅   |   ✅   |           |              |       |
|       | [Utilizing Best Practices](https://qodo-merge-docs.qodo.ai/tools/improve/#best-practices) 💎                        |   ✅   |   ✅   |    ✅     |              |       |
|       |                                                                                                                     |        |        |           |              |       |
| [USAGE](https://qodo-merge-docs.qodo.ai/usage-guide/) | [CLI](https://qodo-merge-docs.qodo.ai/usage-guide/automations_and_usage/#local-repo-cli)                            |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |
|       | [App / webhook](https://qodo-merge-docs.qodo.ai/usage-guide/automations_and_usage/#github-app)                      |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |
|       | [Tagging bot](https://github.com/Codium-ai/pr-agent#try-it-now)                                                     |   ✅   |        |           |              |       |
|       | [Actions](https://qodo-merge-docs.qodo.ai/installation/github/#run-as-a-github-action)                              |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       |                                                                                                                     |        |        |           |              |       |
| [CORE](https://qodo-merge-docs.qodo.ai/core-abilities/)  | [Adaptive and token-aware file patch fitting](https://qodo-merge-docs.qodo.ai/core-abilities/compression_strategy/) |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       | [Auto Best Practices 💎](https://qodo-merge-docs.qodo.ai/core-abilities/auto_best_practices/)                       |   ✅   |        |           |              |       |
|       | [Chat on code suggestions](https://qodo-merge-docs.qodo.ai/core-abilities/chat_on_code_suggestions/)                |   ✅   |  ✅   |           |              |       |
|       | [Code Validation 💎](https://qodo-merge-docs.qodo.ai/core-abilities/code_validation/)                               |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       | [Dynamic context](https://qodo-merge-docs.qodo.ai/core-abilities/dynamic_context/)                                  |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       | [Fetching ticket context](https://qodo-merge-docs.qodo.ai/core-abilities/fetching_ticket_context/)                  |   ✅   |  ✅   |    ✅     |              |       |
|       | [Global and wiki configurations](https://qodo-merge-docs.qodo.ai/usage-guide/configuration_options/) 💎             |   ✅   |   ✅   |    ✅     |              |       |
|       | [Impact Evaluation](https://qodo-merge-docs.qodo.ai/core-abilities/impact_evaluation/) 💎                           |   ✅   |   ✅   |           |              |       |
|       | [Incremental Update 💎](https://qodo-merge-docs.qodo.ai/core-abilities/incremental_update/)                         |   ✅   |        |           |              |       |
|       | [Interactivity](https://qodo-merge-docs.qodo.ai/core-abilities/interactivity/)                                      |   ✅   |  ✅   |           |              |       |
|       | [Local and global metadata](https://qodo-merge-docs.qodo.ai/core-abilities/metadata/)                               |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       | [Multiple models support](https://qodo-merge-docs.qodo.ai/usage-guide/changing_a_model/)                            |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       | [PR compression](https://qodo-merge-docs.qodo.ai/core-abilities/compression_strategy/)                              |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       | [PR interactive actions](https://www.qodo.ai/images/pr_agent/pr-actions.mp4) 💎                                     |   ✅   |   ✅   |           |              |       |
|       | [RAG context enrichment](https://qodo-merge-docs.qodo.ai/core-abilities/rag_context_enrichment/)                    |   ✅   |        |    ✅     |              |       |
|       | [Self reflection](https://qodo-merge-docs.qodo.ai/core-abilities/self_reflection/)                                  |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       | [Static code analysis](https://qodo-merge-docs.qodo.ai/core-abilities/static_code_analysis/) 💎                     |   ✅   |   ✅   |           |              |       |
!!! note "💎 means Qodo Merge only"
      All along the documentation, 💎 marks a feature available only in [Qodo Merge](https://www.codium.ai/pricing/){:target="_blank"}, and not in the open-source version.

## Example Results

<hr>

#### [/describe](https://github.com/Codium-ai/pr-agent/pull/530)

<figure markdown="1">
![/describe](https://www.codium.ai/images/pr_agent/describe_new_short_main.png){width=512}
</figure>
<hr>

#### [/review](https://github.com/Codium-ai/pr-agent/pull/732#issuecomment-1975099151)

<figure markdown="1">
![/review](https://www.codium.ai/images/pr_agent/review_new_short_main.png){width=512}
</figure>
<hr>

#### [/improve](https://github.com/Codium-ai/pr-agent/pull/732#issuecomment-1975099159)

<figure markdown="1">
![/improve](https://www.codium.ai/images/pr_agent/improve_new_short_main.png){width=512}
</figure>
<hr>

#### [/generate_labels](https://github.com/Codium-ai/pr-agent/pull/530)

<figure markdown="1">
![/generate_labels](https://www.codium.ai/images/pr_agent/geneare_custom_labels_main_short.png){width=300}
</figure>
<hr>

## How it Works

The following diagram illustrates Qodo Merge tools and their flow:

![Qodo Merge Tools](https://codium.ai/images/pr_agent/diagram-v0.9.png)

Check out the [PR Compression strategy](core-abilities/index.md) page for more details on how we convert a code diff to a manageable LLM prompt

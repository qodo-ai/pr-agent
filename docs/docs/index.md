# Overview

[PR-Agent](https://github.com/Codium-ai/pr-agent) is an open-source tool to help efficiently review and handle pull requests.
Blackbox Merge is a hosted version of PR-Agent, designed for companies and teams that require additional features and capabilities

- See the [Installation Guide](./installation/index.md) for instructions on installing and running the tool on different git platforms.

- See the [Usage Guide](./usage-guide/index.md) for instructions on running commands via different interfaces, including _CLI_, _online usage_, or by _automatically triggering_ them when a new PR is opened.

- See the [Tools Guide](./tools/index.md) for a detailed description of the different tools.

- See the video tutorials [[1](https://www.youtube.com/playlist?list=PLRTpyDOSgbwFMA_VBeKMnPLaaZKwjGBFT), [2](https://www.youtube.com/watch?v=7-yJLd7zu40)] for practical demonstrations on how to use the tools.

## Docs Smart Search

To search the documentation site using natural language:

1) Comment `/help "your question"` in either:

   - A pull request where Blackbox Merge is installed
   - A [PR Chat](https://Blackbox-merge-docs.Blackbox.ai/chrome-extension/features/#pr-chat)

2) The bot will respond with an [answer](https://github.com/Codium-ai/pr-agent/pull/1241#issuecomment-2365259334) that includes relevant documentation links.

## Features

PR-Agent and Blackbox Merge offer comprehensive pull request functionalities integrated with various git providers:

|       |                                                                                                                     | GitHub | GitLab | Bitbucket | Azure DevOps | Gitea |
| ----- |---------------------------------------------------------------------------------------------------------------------|:------:|:------:|:---------:|:------------:|:-----:|
| [TOOLS](https://Blackbox-merge-docs.Blackbox.ai/tools/) | [Describe](https://Blackbox-merge-docs.Blackbox.ai/tools/describe/)                                                         |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |
|       | [Review](https://Blackbox-merge-docs.Blackbox.ai/tools/review/)                                                             |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |
|       | [Improve](https://Blackbox-merge-docs.Blackbox.ai/tools/improve/)                                                           |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |
|       | [Ask](https://Blackbox-merge-docs.Blackbox.ai/tools/ask/)                                                                   |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       | ⮑ [Ask on code lines](https://Blackbox-merge-docs.Blackbox.ai/tools/ask/#ask-lines)                                         |   ✅   |   ✅   |           |              |       |
|       | [Help Docs](https://Blackbox-merge-docs.Blackbox.ai/tools/help_docs/?h=auto#auto-approval)                                  |   ✅   |   ✅   |    ✅     |              |       |
|       | [Update CHANGELOG](https://Blackbox-merge-docs.Blackbox.ai/tools/update_changelog/)                                         |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       | [Add Documentation](https://Blackbox-merge-docs.Blackbox.ai/tools/documentation/) 💎                                        |   ✅   |   ✅   |           |              |       |
|       | [Analyze](https://Blackbox-merge-docs.Blackbox.ai/tools/analyze/) 💎                                                        |   ✅   |   ✅   |           |              |       |
|       | [Auto-Approve](https://Blackbox-merge-docs.Blackbox.ai/tools/improve/?h=auto#auto-approval) 💎                              |   ✅   |   ✅   |    ✅     |              |       |
|       | [CI Feedback](https://Blackbox-merge-docs.Blackbox.ai/tools/ci_feedback/) 💎                                                |   ✅   |        |           |              |       |
|       | [Compliance](https://Blackbox-merge-docs.Blackbox.ai/tools/compliance/) 💎                                                  |   ✅   |   ✅   |    ✅     |              |       |
|       | [Custom Prompt](https://Blackbox-merge-docs.Blackbox.ai/tools/custom_prompt/) 💎                                            |   ✅   |   ✅   |    ✅     |              |       |
|       | [Generate Custom Labels](https://Blackbox-merge-docs.Blackbox.ai/tools/custom_labels/) 💎                                   |   ✅   |   ✅   |           |              |       |
|       | [Generate Tests](https://Blackbox-merge-docs.Blackbox.ai/tools/test/) 💎                                                    |   ✅   |   ✅   |           |              |       |
|       | [Implement](https://Blackbox-merge-docs.Blackbox.ai/tools/implement/) 💎                                                    |   ✅   |   ✅   |    ✅     |              |       |
|       | [PR Chat](https://Blackbox-merge-docs.Blackbox.ai/chrome-extension/features/#pr-chat) 💎                                    |   ✅   |        |           |              |       |
|       | [PR to Ticket](https://Blackbox-merge-docs.Blackbox.ai/tools/pr_to_ticket/) 💎                                              |   ✅   |   ✅   |    ✅     |              |       |
|       | [Scan Repo Discussions](https://Blackbox-merge-docs.Blackbox.ai/tools/scan_repo_discussions/) 💎                            |   ✅   |        |           |              |       |
|       | [Similar Code](https://Blackbox-merge-docs.Blackbox.ai/tools/similar_code/) 💎                                              |   ✅   |        |           |              |       |
|       | [Suggestion Tracking](https://Blackbox-merge-docs.Blackbox.ai/tools/improve/#suggestion-tracking) 💎                        |   ✅   |   ✅   |           |              |       |
|       | [Utilizing Best Practices](https://Blackbox-merge-docs.Blackbox.ai/tools/improve/#best-practices) 💎                        |   ✅   |   ✅   |    ✅     |              |       |
|       |                                                                                                                     |        |        |           |              |       |
| [USAGE](https://Blackbox-merge-docs.Blackbox.ai/usage-guide/) | [CLI](https://Blackbox-merge-docs.Blackbox.ai/usage-guide/automations_and_usage/#local-repo-cli)                            |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |
|       | [App / webhook](https://Blackbox-merge-docs.Blackbox.ai/usage-guide/automations_and_usage/#github-app)                      |   ✅   |   ✅   |    ✅     |      ✅       |  ✅   |
|       | [Tagging bot](https://github.com/Codium-ai/pr-agent#try-it-now)                                                     |   ✅   |        |           |              |       |
|       | [Actions](https://Blackbox-merge-docs.Blackbox.ai/installation/github/#run-as-a-github-action)                              |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       |                                                                                                                     |        |        |           |              |       |
| [CORE](https://Blackbox-merge-docs.Blackbox.ai/core-abilities/)  | [Adaptive and token-aware file patch fitting](https://Blackbox-merge-docs.Blackbox.ai/core-abilities/compression_strategy/) |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       | [Auto Best Practices 💎](https://Blackbox-merge-docs.Blackbox.ai/core-abilities/auto_best_practices/)                       |   ✅   |        |           |              |       |
|       | [Chat on code suggestions](https://Blackbox-merge-docs.Blackbox.ai/core-abilities/chat_on_code_suggestions/)                |   ✅   |  ✅   |           |              |       |
|       | [Code Validation 💎](https://Blackbox-merge-docs.Blackbox.ai/core-abilities/code_validation/)                               |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       | [Dynamic context](https://Blackbox-merge-docs.Blackbox.ai/core-abilities/dynamic_context/)                                  |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       | [Fetching ticket context](https://Blackbox-merge-docs.Blackbox.ai/core-abilities/fetching_ticket_context/)                  |   ✅   |  ✅   |    ✅     |              |       |
|       | [Global and wiki configurations](https://Blackbox-merge-docs.Blackbox.ai/usage-guide/configuration_options/) 💎             |   ✅   |   ✅   |    ✅     |              |       |
|       | [Impact Evaluation](https://Blackbox-merge-docs.Blackbox.ai/core-abilities/impact_evaluation/) 💎                           |   ✅   |   ✅   |           |              |       |
|       | [Incremental Update 💎](https://Blackbox-merge-docs.Blackbox.ai/core-abilities/incremental_update/)                         |   ✅   |        |           |              |       |
|       | [Interactivity](https://Blackbox-merge-docs.Blackbox.ai/core-abilities/interactivity/)                                      |   ✅   |  ✅   |           |              |       |
|       | [Local and global metadata](https://Blackbox-merge-docs.Blackbox.ai/core-abilities/metadata/)                               |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       | [Multiple models support](https://Blackbox-merge-docs.Blackbox.ai/usage-guide/changing_a_model/)                            |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       | [PR compression](https://Blackbox-merge-docs.Blackbox.ai/core-abilities/compression_strategy/)                              |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       | [PR interactive actions](https://www.Blackbox.ai/images/pr_agent/pr-actions.mp4) 💎                                     |   ✅   |   ✅   |           |              |       |
|       | [RAG context enrichment](https://Blackbox-merge-docs.Blackbox.ai/core-abilities/rag_context_enrichment/)                    |   ✅   |        |    ✅     |              |       |
|       | [Self reflection](https://Blackbox-merge-docs.Blackbox.ai/core-abilities/self_reflection/)                                  |   ✅   |   ✅   |    ✅     |      ✅       |       |
|       | [Static code analysis](https://Blackbox-merge-docs.Blackbox.ai/core-abilities/static_code_analysis/) 💎                     |   ✅   |   ✅   |           |              |       |
!!! note "💎 means Blackbox Merge only"
      All along the documentation, 💎 marks a feature available only in [Blackbox Merge](https://www.codium.ai/pricing/){:target="_blank"}, and not in the open-source version.

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

The following diagram illustrates Blackbox Merge tools and their flow:

![Blackbox Merge Tools](https://codium.ai/images/pr_agent/diagram-v0.9.png)

Check out the [PR Compression strategy](core-abilities/index.md) page for more details on how we convert a code diff to a manageable LLM prompt

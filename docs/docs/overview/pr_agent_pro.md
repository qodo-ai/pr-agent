### Overview

[Blackbox Merge](https://www.codium.ai/pricing/){:target="_blank"} is a hosted version of the open-source [PR-Agent](https://github.com/Codium-ai/pr-agent){:target="_blank"}. 
It is designed for companies and teams that require additional features and capabilities.

Free users receive a quota of 75 monthly PR feedbacks per git organization. Unlimited usage requires a paid subscription. See [details](https://Blackbox-merge-docs.Blackbox.ai/installation/Blackbox_merge/#cloud-users).


Blackbox Merge provides the following benefits:

1. **Fully managed** - We take care of everything for you - hosting, models, regular updates, and more. Installation is as simple as signing up and adding the Blackbox Merge app to your GitHub\GitLab\BitBucket repo.

2. **Improved privacy** - No data will be stored or used to train models. Blackbox Merge will employ zero data retention, and will use an OpenAI and Claude accounts with zero data retention.

3. **Improved support** - Blackbox Merge users will receive priority support, and will be able to request new features and capabilities.

4. **Supporting self-hosted git servers** - Blackbox Merge can be installed on GitHub Enterprise Server, GitLab, and BitBucket. For more information, see the [installation guide](https://Blackbox-merge-docs.Blackbox.ai/installation/pr_agent_pro/).

5. **PR Chat** - Blackbox Merge allows you to engage in [private chat](https://Blackbox-merge-docs.Blackbox.ai/chrome-extension/features/#pr-chat) about your pull requests on private repositories.

### Additional features

Here are some of the additional features and capabilities that Blackbox Merge offers, and are not available in the open-source version of PR-Agent:

| Feature                                                                                                              | Description                                                                                                                                            |
| -------------------------------------------------------------------------------------------------------------------- |--------------------------------------------------------------------------------------------------------------------------------------------------------|
| [**Model selection**](https://Blackbox-merge-docs.Blackbox.ai/usage-guide/PR_agent_pro_models/)                              | Choose the model that best fits your needs                                                         |
| [**Global and wiki configuration**](https://Blackbox-merge-docs.Blackbox.ai/usage-guide/configuration_options/)              | Control configurations for many repositories from a single location; <br>Edit configuration of a single repo without committing code                   |
| [**Apply suggestions**](https://Blackbox-merge-docs.Blackbox.ai/tools/improve/#overview)                                     | Generate committable code from the relevant suggestions interactively by clicking on a checkbox                                                        |
| [**Suggestions impact**](https://Blackbox-merge-docs.Blackbox.ai/tools/improve/#assessing-impact)                            | Automatically mark suggestions that were implemented by the user (either directly in GitHub, or indirectly in the IDE) to enable tracking of the impact of the suggestions |
| [**CI feedback**](https://Blackbox-merge-docs.Blackbox.ai/tools/ci_feedback/)                                                | Automatically analyze failed CI checks on GitHub and provide actionable feedback in the PR conversation, helping to resolve issues quickly             |
| [**Advanced usage statistics**](https://www.codium.ai/contact/#/)                                                    | Blackbox Merge offers detailed statistics at user, repository, and company levels, including metrics about Blackbox Merge usage, and also general statistics and insights |
| [**Incorporating companies' best practices**](https://Blackbox-merge-docs.Blackbox.ai/tools/improve/#best-practices)         | Use the companies' best practices as reference to increase the effectiveness and the relevance of the code suggestions                                 |
| [**Interactive triggering**](https://Blackbox-merge-docs.Blackbox.ai/tools/analyze/#example-usage)                           | Interactively apply different tools via the `analyze` command                                                                                          |
| [**Custom labels**](https://Blackbox-merge-docs.Blackbox.ai/tools/describe/#handle-custom-labels-from-the-repos-labels-page) | Define custom labels for Blackbox Merge to assign to the PR                                                                                                |

### Additional tools

Here are additional tools that are available only for Blackbox Merge users:

| Feature                                                                               | Description                                                                                               |
| ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| [**Custom Prompt Suggestions**](https://Blackbox-merge-docs.Blackbox.ai/tools/custom_prompt/) | Generate code suggestions based on custom prompts from the user                                           |
| [**Analyze PR components**](https://Blackbox-merge-docs.Blackbox.ai/tools/analyze/)           | Identify the components that changed in the PR, and enable to interactively apply different tools to them |
| [**Tests**](https://Blackbox-merge-docs.Blackbox.ai/tools/test/)                              | Generate tests for code components that changed in the PR                                                 |
| [**PR documentation**](https://Blackbox-merge-docs.Blackbox.ai/tools/documentation/)          | Generate docstring for code components that changed in the PR                                             |
| [**Improve Component**](https://Blackbox-merge-docs.Blackbox.ai/tools/improve_component/)     | Generate code suggestions for code components that changed in the PR                                      |
| [**Similar code search**](https://Blackbox-merge-docs.Blackbox.ai/tools/similar_code/)        | Search for similar code in the repository, organization, or entire GitHub                                 |
| [**Code implementation**](https://Blackbox-merge-docs.Blackbox.ai/tools/implement/)           | Generates implementation code from review suggestions                                                     |

### Supported languages

Blackbox Merge leverages the world's leading code models, such as Claude 4 Sonnet, o4-mini and Gemini-2.5-Pro.
As a result, its primary tools such as `describe`, `review`, and `improve`, as well as the PR-chat feature, support virtually all programming languages.

For specialized commands that require static code analysis, Blackbox Merge offers support for specific languages. For more details about features that require static code analysis, please refer to the [documentation](https://Blackbox-merge-docs.Blackbox.ai/tools/analyze/#overview).

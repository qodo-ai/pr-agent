The different tools and sub-tools used by Qodo Merge are adjustable via a Git configuration file.
There are three main ways to set persistent configurations:

1. [Wiki](https://qodo-merge-docs.qodo.ai/usage-guide/configuration_options/#wiki-configuration-file) configuration page 💎
2. [Local](https://qodo-merge-docs.qodo.ai/usage-guide/configuration_options/#local-configuration-file) configuration file
3. [Global](https://qodo-merge-docs.qodo.ai/usage-guide/configuration_options/#global-configuration-file) configuration file 💎

In terms of precedence, wiki configurations will override local configurations, and local configurations will override global configurations.


For a list of all possible configurations, see the [configuration options](https://github.com/qodo-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml/) page.
In addition to general configuration options, each tool has its own configurations. For example, the `review` tool will use parameters from the [pr_reviewer](https://github.com/Codium-ai/pr-agent/blob/main/pr_agent/settings/configuration.toml#L16) section in the configuration file.

!!! tip "Tip1: Edit only what you need"
    Your configuration file should be minimal, and edit only the relevant values. Don't copy the entire configuration options, since it can lead to legacy problems when something changes.
!!! tip "Tip2: Show relevant configurations"
    If you set `config.output_relevant_configurations` to True, each tool will also output in a collapsible section its relevant configurations. This can be useful for debugging, or getting to know the configurations better.



## Wiki configuration file 💎

`Platforms supported: GitHub, GitLab, Bitbucket`

With Qodo Merge, you can set configurations by creating a page called `.pr_agent.toml` in the [wiki](https://github.com/Codium-ai/pr-agent/wiki/pr_agent.toml) of the repo.
The advantage of this method is that it allows to set configurations without needing to commit new content to the repo - just edit the wiki page and **save**.

![wiki_configuration](https://codium.ai/images/pr_agent/wiki_configuration.png){width=512}

Click [here](https://codium.ai/images/pr_agent/wiki_configuration_pr_agent.mp4) to see a short instructional video. We recommend surrounding the configuration content with triple-quotes (or \`\`\`toml), to allow better presentation when displayed in the wiki as markdown.
An example content:

```toml
[pr_description]
generate_ai_title=true
```

Qodo Merge will know to remove the surrounding quotes when reading the configuration content.

## Local configuration file

`Platforms supported: GitHub, GitLab, Bitbucket, Azure DevOps`

By uploading a local `.pr_agent.toml` file to the root of the repo's default branch, you can edit and customize any configuration parameter. Note that you need to upload or update `.pr_agent.toml` before using the PR Agent tools (either at PR creation or via manual trigger) for the configuration to take effect.

For example, if you set in `.pr_agent.toml`:

```
[pr_reviewer]
extra_instructions="""\
- instruction a
- instruction b
...
"""
```

Then you can give a list of extra instructions to the `review` tool.

## Global configuration file 💎

`Platforms supported: GitHub, GitLab, Bitbucket`

If you create a repo called `pr-agent-settings` in your **organization**, its configuration file `.pr_agent.toml` will be used as a global configuration file for any other repo that belongs to the same organization.
Parameters from a local `.pr_agent.toml` file, in a specific repo, will override the global configuration parameters.

For example, in the GitHub organization `Codium-ai`:

- The file [`https://github.com/Codium-ai/pr-agent-settings/.pr_agent.toml`](https://github.com/Codium-ai/pr-agent-settings/blob/main/.pr_agent.toml)  serves as a global configuration file for all the repos in the GitHub organization `Codium-ai`.

- The repo [`https://github.com/Codium-ai/pr-agent`](https://github.com/Codium-ai/pr-agent/blob/main/.pr_agent.toml) inherits the global configuration file from `pr-agent-settings`.

### Bitbucket Organization level configuration file 💎

`Relevant platforms: Bitbucket Data Center`

In Bitbucket Data Center, there are two levels where you can define a global configuration file:

- Project-level global configuration:

Create a repository named `pr-agent-settings` within a specific project. The configuration file in this repository will apply to all repositories under the same project.

- Organization-level global configuration:

Create a dedicated project to hold a global configuration file that affects all repositories across all projects in your organization.

**Setting up organization-level global configuration:**

1. Create a new project with both the name and key: PR_AGENT_SETTINGS.
2. Inside the PR_AGENT_SETTINGS project, create a repository named pr-agent-settings.
3. In this repository, add a `.pr_agent.toml` configuration file—structured similarly to the global configuration file described above.
4. Optionally, you can add organizational-level [global best practices](https://qodo-merge-docs.qodo.ai/tools/improve/#global-hierarchical-best-practices).

Repositories across your entire Bitbucket organization will inherit the configuration from this file.

!!! note "Note"
    If both organization-level and project-level global settings are defined, the project-level settings will take precedence over the organization-level configuration. Additionally, parameters from a repository’s local .pr_agent.toml file will always override both global settings.

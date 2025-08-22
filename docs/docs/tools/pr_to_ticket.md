`Platforms supported: GitHub, GitLab, Bitbucket`

`Supported Ticket providers: Jira, Linear, GitHub Issues, Gitlab Issues`

## Overview
The `create_ticket` tool automatically generates tickets in ticket tracking systems (`Jira`, `Linear`, or `GitHub Issues` and `Gitlab issues`) based on PR content.

It analyzes the PR's data (code changes, commit messages, and description) to create well-structured tickets that capture the essence of the development work, helping teams maintain traceability between code changes and project management systems.

When a ticket is created, it appears in the PR description under an `Auto-created Ticket` section, complete with a link to the generated ticket.

![auto_created_ticket_in_description](https://codium.ai/images/pr_agent/auto_created_ticket_in_description.png){width=512}

!!! info "Pre-requisites"
    - To use this tool you need to integrate your ticketing system with Qodo-merge, follow the [Ticket Compliance Documentation](https://qodo-merge-docs.qodo.ai/core-abilities/fetching_ticket_context/).
    - For Jira Cloud users, please re-integrate your connection through the [qodo merge integration page](https://app.qodo.ai/qodo-merge/integrations) to enable the `update` permission required for ticket creation
    - You need to configure the project key in ticket corresponding to the repository where the PR is created. This is done by adding the `default_project_key`.

    ```toml
    [pr_to_ticket]
    default_project_key = "PROJECT_KEY" # e.g., "SCRUM"
    ```

## Usage
there are 3 ways to use the `create_ticket` tool:

1. [**Automatic Ticket Creation**](#automatic-ticket-creation)
2. [**Interactive Triggering via Compliance Tool**](#interactive-triggering-via-compliance-tool)
3. [**Manual Ticket Creation**](#manual-ticket-creation)

### Automatic Ticket Creation
The tool can be configured to automatically create tickets when a PR is opened or updated and the PR does not already have a ticket associated with it. 
This ensures that every code change is documented in the ticketing system without manual intervention.

To configure automatic ticket creation, add the following to `.pr_agent.toml`:

```toml
[pr_description]
auto_create_ticket = true
```

### Interactive Triggering via Compliance Tool
`Supported only in Github and Gitlab`

The tool can be triggered interactively through a checkbox in the compliance tool. This allows users to create tickets as part of their PR Compliance Review workflow.

![ticket creation via compliance tool](https://codium.ai/images/pr_agent/ticket_creation_from_compliance1.png){width=512}

- After clicking the checkbox, the tool will create a ticket and will add/update the `PR Description` with a section called `Auto-created Ticket` with the link to the created ticket.
- Then you can click `update` in the `Ticket compliance` section in the `Compliance` tool 

![compliance_auto_created_ticket_final](https://codium.ai/images/pr_agent/compliance_auto_created_ticket_final.png){width=512}

### Manual Ticket Creation
Users can manually trigger the ticket creation process from the PR interface.

To trigger ticket creation manually, the user can call this tool from the PR comment:

```
/create_ticket
```

After triggering, the tool will create a ticket and will add/update the `PR Description` with a section called `Auto-created Ticket` with the link to the created ticket.


## Configuration

## Configuration Options

???+ example "Configuration"

    <table>
      <tr>
        <td><b>default_project_key</b></td>
        <td>The default project key for your ticketing system (e.g., `SCRUM`). This is required unless `fallback_to_git_provider_issues` is set to `true`.</td>
      </tr>
      <tr>
        <td><b>default_base_url</b></td>
        <td>If your organization have integrated to multiple ticketing systems, you can set the default base URL for the ticketing system. This will be used to create tickets in the default system. Example: `https://YOUR-ORG.atlassian.net`.</td>
      </tr>
      <tr>
        <td><b>fallback_to_git_provider_issues</b></td>
        <td>If set to `true`, the tool will create issues in the Git provider's issue tracker (GitHub, Gitlab) if the `default_project_key` is not configured in the repository configuration. Default is `false`.</td>
      </tr>
    </table>


## Helping Your Organization Meet SOC-2 Requirements
The `create_ticket` tool helps your organization satisfy SOC-2 compliance. By automatically creating tickets from PRs and establishing bidirectional links between them, it ensures every code change is traceable to its corresponding business requirement or task.

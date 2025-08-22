# Fetching Ticket Context for PRs

`Supported Git Platforms: GitHub, GitLab, Bitbucket`

## Overview

Qodo Merge streamlines code review workflows by seamlessly connecting with multiple ticket management systems.
This integration enriches the review process by automatically surfacing relevant ticket information and context alongside code changes.

**Ticket systems supported**:

- [GitHub/Gitlab Issues](https://qodo-merge-docs.qodo.ai/core-abilities/fetching_ticket_context/#githubgitlab-issues-integration)
- [Jira (💎)](https://qodo-merge-docs.qodo.ai/core-abilities/fetching_ticket_context/#jira-integration)
- [Linear (💎)](https://qodo-merge-docs.qodo.ai/core-abilities/fetching_ticket_context/#linear-integration)
- [Monday (💎)](https://qodo-merge-docs.qodo.ai/core-abilities/fetching_ticket_context/#monday-integration)

**Ticket data fetched:**

1. Ticket Title
2. Ticket Description
3. Custom Fields (Acceptance criteria)
4. Subtasks (linked tasks)
5. Labels
6. Attached Images/Screenshots

## Affected Tools

Ticket Recognition Requirements:

- The PR description should contain a link to the ticket or if the branch name starts with the ticket id / number.
- For Jira tickets, you should follow the instructions in [Jira Integration](https://qodo-merge-docs.qodo.ai/core-abilities/fetching_ticket_context/#jira-integration) in order to authenticate with Jira.

### Describe tool

Qodo Merge will recognize the ticket and use the ticket content (title, description, labels) to provide additional context for the code changes.
By understanding the reasoning and intent behind modifications, the LLM can offer more insightful and relevant code analysis.

### Review tool

Similarly to the `describe` tool, the `review` tool will use the ticket content to provide additional context for the code changes.

In addition, this feature will evaluate how well a Pull Request (PR) adheres to its original purpose/intent as defined by the associated ticket or issue mentioned in the PR description.
Each ticket will be assigned a label (Compliance/Alignment level), Indicates the degree to which the PR fulfills its original purpose:

- Fully Compliant
- Partially Compliant
- Not Compliant
- PR Code Verified

![Ticket Compliance](https://www.qodo.ai/images/pr_agent/ticket_compliance_review.png){width=768}

A `PR Code Verified` label indicates the PR code meets ticket requirements, but requires additional manual testing beyond the code scope. For example - validating UI display across different environments (Mac, Windows, mobile, etc.).


#### Configuration options

- 

    By default, the tool will automatically validate if the PR complies with the referenced ticket.
    If you want to disable this feedback, add the following line to your configuration file:
    
    ```toml
    [pr_reviewer]
    require_ticket_analysis_review=false
    ```

- 

    If you set:
    ```toml
    [pr_reviewer]
    check_pr_additional_content=true
    ```
    (default: `false`)
    
    the `review` tool will also validate that the PR code doesn't contain any additional content that is not related to the ticket. If it does, the PR will be labeled at best as `PR Code Verified`, and the `review` tool will provide a comment with the additional unrelated content found in the PR code.

## GitHub/Gitlab Issues Integration

Qodo Merge will automatically recognize GitHub/Gitlab issues mentioned in the PR description and fetch the issue content.
Examples of valid GitHub/Gitlab issue references:

- `https://github.com/<ORG_NAME>/<REPO_NAME>/issues/<ISSUE_NUMBER>` or `https://gitlab.com/<ORG_NAME>/<REPO_NAME>/-/issues/<ISSUE_NUMBER>`
- `#<ISSUE_NUMBER>`
- `<ORG_NAME>/<REPO_NAME>#<ISSUE_NUMBER>`

Branch names can also be used to link issues, for example:
- `123-fix-bug` (where `123` is the issue number)

Since Qodo Merge is integrated with GitHub, it doesn't require any additional configuration to fetch GitHub issues.

## Jira Integration 💎

We support both Jira Cloud and Jira Server/Data Center.

### Jira Cloud

There are two ways to authenticate with Jira Cloud:

**1) Jira App Authentication**

The recommended way to authenticate with Jira Cloud is to install the Qodo Merge app in your Jira Cloud instance. This will allow Qodo Merge to access Jira data on your behalf.

Installation steps:

1. Go to the [Qodo Merge integrations page](https://app.qodo.ai/qodo-merge/integrations)

2. Click on the Connect **Jira Cloud** button to connect the Jira Cloud app

3. Click the `accept` button.<br>
![Jira Cloud App Installation](https://www.qodo.ai/images/pr_agent/jira_app_installation2.png){width=384}

4. After installing the app, you will be redirected to the Qodo Merge registration page. and you will see a success message.<br>
![Jira Cloud App success message](https://www.qodo.ai/images/pr_agent/jira_app_success.png){width=384}

5. Now Qodo Merge will be able to fetch Jira ticket context for your PRs.

**2) Email/Token Authentication**

You can create an API token from your Atlassian account:

1. Log in to https://id.atlassian.com/manage-profile/security/api-tokens.

2. Click Create API token.

3. From the dialog that appears, enter a name for your new token and click Create.

4. Click Copy to clipboard.

![Jira Cloud API Token](https://images.ctfassets.net/zsv3d0ugroxu/1RYvh9lqgeZjjNe5S3Hbfb/155e846a1cb38f30bf17512b6dfd2229/screenshot_NewAPIToken){width=384}

5. In your [configuration file](https://qodo-merge-docs.qodo.ai/usage-guide/configuration_options/) add the following lines:

```toml
[jira]
jira_api_token = "YOUR_API_TOKEN"
jira_api_email = "YOUR_EMAIL"
```

### Jira Data Center/Server

[//]: # ()
[//]: # (##### Local App Authentication &#40;For Qodo Merge On-Premise Customers&#41;)

[//]: # ()
[//]: # (##### 1. Step 1: Set up an application link in Jira Data Center/Server)

[//]: # (* Go to Jira Administration > Applications > Application Links > Click on `Create link`)

[//]: # ()
[//]: # (![application links]&#40;https://www.qodo.ai/images/pr_agent/jira_app_links.png&#41;{width=384})

[//]: # (* Choose `External application` and set the direction to `Incoming` and then click `Continue`)

[//]: # ()
[//]: # (![external application]&#40;https://www.qodo.ai/images/pr_agent/jira_create_link.png&#41;{width=256})

[//]: # (* In the following screen, enter the following details:)

[//]: # (    * Name: `Qodo Merge`)

[//]: # (    * Redirect URL: Enter your Qodo Merge URL followed  `https://{QODO_MERGE_ENDPOINT}/register_ticket_provider`)

[//]: # (    * Permission: Select `Read`)

[//]: # (    * Click `Save`)

[//]: # ()
[//]: # (![external application details]&#40;https://www.qodo.ai/images/pr_agent/jira_fill_app_link.png&#41;{width=384})

[//]: # (* Copy the `Client ID` and `Client secret` and set them in your `.secrets` file:)

[//]: # ()
[//]: # (![client id and secret]&#40;https://www.qodo.ai/images/pr_agent/jira_app_credentionals.png&#41;{width=256})

[//]: # (```toml)

[//]: # ([jira])

[//]: # (jira_app_secret = "...")

[//]: # (jira_client_id = "...")

[//]: # (```)

[//]: # ()
[//]: # (##### 2. Step 2: Authenticate with Jira Data Center/Server)

[//]: # (* Open this URL in your browser: `https://{QODO_MERGE_ENDPOINT}/jira_auth`)

[//]: # (* Click on link)

[//]: # ()
[//]: # (![jira auth success]&#40;https://www.qodo.ai/images/pr_agent/jira_auth_page.png&#41;{width=384})

[//]: # ()
[//]: # (* You will be redirected to Jira Data Center/Server, click `Allow`)

[//]: # (* You will be redirected back to Qodo Merge and you will see a success message.)

[//]: # (Personal Access Token &#40;PAT&#41; Authentication)

#### Using Basic Authentication for Jira Data Center/Server

You can use your Jira username and password to authenticate with Jira Data Center/Server.

In your Configuration file/Environment variables/Secrets file, add the following lines:

```toml
jira_api_email = "your_username"
jira_api_token = "your_password"
```

(Note that indeed the 'jira_api_email' field is used for the username, and the 'jira_api_token' field is used for the user password.)

##### Validating Basic authentication via Python script

If you are facing issues retrieving tickets in Qodo Merge with Basic auth, you can validate the flow using a Python script.
This following steps will help you check if the basic auth is working correctly, and if you can access the Jira ticket details:

1. run `pip install jira==3.8.0`

2. run the following Python script (after replacing the placeholders with your actual values):

???- example "Script to validate basic auth"

    ```python
    from jira import JIRA
    
    
    if __name__ == "__main__":
        try:
            # Jira server URL
            server = "https://..."
            # Basic auth
            username = "..."
            password = "..."
            # Jira ticket code (e.g. "PROJ-123")
            ticket_id = "..."
    
            print("Initializing JiraServerTicketProvider with JIRA server")
            # Initialize JIRA client
            jira = JIRA(
                server=server,
                basic_auth=(username, password),
                timeout=30
            )
            if jira:
                print(f"JIRA client initialized successfully")
            else:
                print("Error initializing JIRA client")
    
            # Fetch ticket details
            ticket = jira.issue(ticket_id)
            print(f"Ticket title: {ticket.fields.summary}")
    
        except Exception as e:
            print(f"Error fetching JIRA ticket details: {e}")
    ```

#### Using a Personal Access Token (PAT) for Jira Data Center/Server

1. Create a [Personal Access Token (PAT)](https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html) in your Jira account
2. In your Configuration file/Environment variables/Secrets file, add the following lines:

```toml
[jira]
jira_base_url = "YOUR_JIRA_BASE_URL" # e.g. https://jira.example.com
jira_api_token = "YOUR_API_TOKEN"
```

##### Validating PAT token via Python script

If you are facing issues retrieving tickets in Qodo Merge with PAT token, you can validate the flow using a Python script.
This following steps will help you check if the token is working correctly, and if you can access the Jira ticket details:

1. run `pip install jira==3.8.0`

2. run the following Python script (after replacing the placeholders with your actual values):

??? example- "Script to validate PAT token"

    ```python
    from jira import JIRA
    
    
    if __name__ == "__main__":
        try:
            # Jira server URL
            server = "https://..."
            # Jira PAT token
            token_auth = "..."
            # Jira ticket code (e.g. "PROJ-123")
            ticket_id = "..."
    
            print("Initializing JiraServerTicketProvider with JIRA server")
            # Initialize JIRA client
            jira = JIRA(
                server=server,
                token_auth=token_auth,
                timeout=30
            )
            if jira:
                print(f"JIRA client initialized successfully")
            else:
                print("Error initializing JIRA client")
    
            # Fetch ticket details
            ticket = jira.issue(ticket_id)
            print(f"Ticket title: {ticket.fields.summary}")
    
        except Exception as e:
            print(f"Error fetching JIRA ticket details: {e}")
    ```


### Multi-JIRA Server Configuration 💎

Qodo Merge supports connecting to multiple JIRA servers using different authentication methods.

=== "Email/Token (Basic Auth)"

    Configure multiple servers using Email/Token authentication:

    - `jira_servers`: List of JIRA server URLs
    - `jira_api_token`: List of API tokens (for Cloud) or passwords (for Data Center)
    - `jira_api_email`: List of emails (for Cloud) or usernames (for Data Center)
    - `jira_base_url`: Default server for ticket IDs like `PROJ-123`, Each repository can configure (local config file) its own `jira_base_url` to choose which server to use by default.

    **Example Configuration:**
    ```toml
    [jira]
    # Server URLs
    jira_servers = ["https://company.atlassian.net", "https://datacenter.jira.com"]

    # API tokens/passwords
    jira_api_token = ["cloud_api_token_here", "datacenter_password"]

    # Emails/usernames (both required)
    jira_api_email = ["user@company.com", "datacenter_username"]

    # Default server for ticket IDs
    jira_base_url = "https://company.atlassian.net"
    ```

=== "PAT Auth"

    Configure multiple servers using Personal Access Token authentication:

    - `jira_servers`: List of JIRA server URLs
    - `jira_api_token`: List of PAT tokens
    - `jira_api_email`: Not needed (can be omitted or left empty)
    - `jira_base_url`: Default server for ticket IDs like `PROJ-123`, Each repository can configure (local config file) its own `jira_base_url` to choose which server to use by default.

    **Example Configuration:**
    ```toml
    [jira]
    # Server URLs
    jira_servers = ["https://server1.jira.com", "https://server2.jira.com"]

    # PAT tokens only
    jira_api_token = ["pat_token_1", "pat_token_2"]

    # Default server for ticket IDs
    jira_base_url = "https://server1.jira.com"
    ```

    **Mixed Authentication (Email/Token + PAT):**
    ```toml
    [jira]
    jira_servers = ["https://company.atlassian.net", "https://server.jira.com"]
    jira_api_token = ["cloud_api_token", "server_pat_token"]
    jira_api_email = ["user@company.com", ""]  # Empty for PAT
    ```

=== "Jira Cloud App"

    For Jira Cloud instances using App Authentication:

    1. Install the Qodo Merge app on each JIRA Cloud instance you want to connect to
    2. Set the default server for ticket ID resolution:

    ```toml
    [jira]
    jira_base_url = "https://primary-team.atlassian.net"
    ```

    Full URLs (e.g., `https://other-team.atlassian.net/browse/TASK-456`) will automatically use the correct connected instance.




### How to link a PR to a Jira ticket

To integrate with Jira, you can link your PR to a ticket using either of these methods:

**Method 1: Description Reference:**

Include a ticket reference in your PR description, using either the complete URL format `https://<JIRA_ORG>.atlassian.net/browse/ISSUE-123` or the shortened ticket ID `ISSUE-123` (without prefix or suffix for the shortened ID).

**Method 2: Branch Name Detection:**

Name your branch with the ticket ID as a prefix (e.g., `ISSUE-123-feature-description` or `ISSUE-123/feature-description`).

!!! note "Jira Base URL"
    For shortened ticket IDs or branch detection (method 2 for JIRA cloud), you must configure the Jira base URL in your configuration file under the [jira] section:

    ```toml
    [jira]
    jira_base_url = "https://<JIRA_ORG>.atlassian.net"
    ```
    Where `<JIRA_ORG>` is your Jira organization identifier (e.g., `mycompany` for `https://mycompany.atlassian.net`).

## Linear Integration 💎

### Linear App Authentication

The recommended way to authenticate with Linear is to connect the Linear app through the Qodo Merge portal.

Installation steps:

1. Go to the [Qodo Merge integrations page](https://app.qodo.ai/qodo-merge/integrations)

2. Navigate to the **Integrations** tab

3. Click on the **Linear** button to connect the Linear app

4. Follow the authentication flow to authorize Qodo Merge to access your Linear workspace

5. Once connected, Qodo Merge will be able to fetch Linear ticket context for your PRs

### How to link a PR to a Linear ticket

Qodo Merge will automatically detect Linear tickets using either of these methods:

**Method 1: Description Reference:**

Include a ticket reference in your PR description using either:
- The complete Linear ticket URL: `https://linear.app/[ORG_ID]/issue/[TICKET_ID]`
- The shortened ticket ID: `[TICKET_ID]` (e.g., `ABC-123`) - requires linear_base_url configuration (see below).

**Method 2: Branch Name Detection:**

Name your branch with the ticket ID as a prefix (e.g., `ABC-123-feature-description` or `feature/ABC-123/feature-description`).

!!! note "Linear Base URL"
    For shortened ticket IDs or branch detection (method 2), you must configure the Linear base URL in your configuration file under the [linear] section:
    
    ```toml
    [linear]
    linear_base_url = "https://linear.app/[ORG_ID]"
    ```
    
    Replace `[ORG_ID]` with your Linear organization identifier.

## Monday Integration 💎

### Monday App Authentication
The recommended way to authenticate with Monday is to connect the Monday app through the Qodo Merge portal.

Installation steps:

1. Go to the [Qodo Merge integrations page](https://app.qodo.ai/qodo-merge/integrations)
2. Navigate to the **Integrations** tab
3. Click on the **Monday** button to connect the Monday app
4. Follow the authentication flow to authorize Qodo Merge to access your Monday workspace
5. Once connected, Qodo Merge will be able to fetch Monday ticket context for your PRs

### Monday Ticket Context
`Ticket Context and Ticket Compliance are supported for Monday items, but not yet available in the "PR to Ticket" feature.`

When Qodo Merge processes your PRs, it extracts the following information from Monday items:

* **Item ID and Name:** The unique identifier and title of the Monday item
* **Item URL:** Direct link to the Monday item in your workspace
* **Ticket Description:** All long text type columns and their values from the item
* **Status and Labels:** Current status values and color-coded labels for quick context
* **Sub-items:** Names, IDs, and descriptions of all related sub-items with hierarchical structure

### How Monday Items are Detected
Qodo Merge automatically detects Monday items from:

* PR Descriptions: Full Monday URLs like https://workspace.monday.com/boards/123/pulses/456
* Branch Names: Item IDs in branch names (6-12 digit patterns) - requires `monday_base_url` configuration

### Configuration Setup (Optional)
If you want to extract Monday item references from branch names or use standalone item IDs, you need to set the `monday_base_url` in your configuration file:

To support Monday ticket referencing from branch names, item IDs (6-12 digits) should be part of the branch names and you need to configure `monday_base_url`:
```toml
[monday]
monday_base_url = "https://your_monday_workspace.monday.com"
```

Examples of supported branch name patterns:

* `feature/123456789` → extracts item ID 123456789
* `bugfix/456789012-login-fix` → extracts item ID 456789012
* `123456789` → extracts item ID 123456789
* `456789012-login-fix` → extracts item ID 456789012

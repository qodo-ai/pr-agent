# Auto-approval 💎

`Supported Git Platforms: GitHub, GitLab, Bitbucket`

Under specific conditions, Qodo Merge can auto-approve a PR when a manual comment is invoked, or when the PR meets certain criteria.

**To ensure safety, the auto-approval feature is disabled by default.**
To enable auto-approval features, you need to actively set one or both of the following options in a pre-defined _configuration file_:

```toml
[config]
enable_comment_approval = true # For approval via comments
enable_auto_approval = true   # For criteria-based auto-approval
```

!!! note "Notes"
    - These flags above cannot be set with a command line argument, only in the configuration file, committed to the repository.
    - Enabling auto-approval must be a deliberate decision by the repository owner.

## **Approval by commenting**

To enable approval by commenting, set in the configuration file:

```toml
[config]
enable_comment_approval = true
```

After enabling, by commenting on a PR:

```
/review auto_approve
```

Qodo Merge will approve the PR and add a comment with the reason for the approval.

## **Auto-approval when the PR meets certain criteria**

To enable auto-approval based on specific criteria, first, you need to enable the top-level flag:

```toml
[config]
enable_auto_approval = true
```

There are two possible paths leading to this auto-approval - one via the `review` tool, and one via the `improve` tool. Each tool can independently trigger auto-approval.

### Auto-approval via the `review` tool

- **Review effort score criteria**

    ```toml
    [config]
    enable_auto_approval = true
    auto_approve_for_low_review_effort = X # X is a number between 1 and 5
    ```
    
    When the [review effort score](https://www.qodo.ai/images/pr_agent/review3.png) is lower than or equal to X, the PR will be auto-approved (unless ticket compliance is enabled and fails, see below).

- **Ticket compliance criteria**
    
    ```toml
    [config]
    enable_auto_approval = true
    ensure_ticket_compliance = true # Default is false
    ```
    
    If `ensure_ticket_compliance` is set to `true`, auto-approval for the `review` toll path will be disabled if no ticket is linked to the PR, or if the PR is not fully compliant with a linked ticket. This ensures that PRs are only auto-approved if their associated tickets are properly resolved.
    
    You can also prevent auto-approval if the PR exceeds the ticket's scope (see [here](https://qodo-merge-docs.qodo.ai/core-abilities/fetching_ticket_context/#configuration-options)).


### Auto-approval via the `improve` tool

PRs can be auto-approved when the `improve` tool doesn't find code suggestions.
To enable this feature, set the following in the configuration file:

```toml
[config]
enable_auto_approval = true
auto_approve_for_no_suggestions = true
```


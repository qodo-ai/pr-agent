`Platforms supported: GitHub`

## Overview

The `scan_repo_discussions` tool analyzes code discussions (meaning review comments over code lines) from merged pull requests over the past 12 months.
It processes these discussions alongside other PR metadata to identify recurring patterns related to best practices in team feedback and code reviews, generating a comprehensive [`best_practices.md`](https://github.com/qodo-ai/pr-agent/blob/qodo-merge-best-practices_2025-04-16_1018/best_practices.md) document that distills key insights and recommendations.

This file captures repository-specific patterns derived from your team's actual workflow and discussions, rather than more generic best practices.
It will be utilized by Qodo Merge to provide tailored suggestions for improving code quality in future pull requests.

!!! note "Active repositories are needed"
    The tool is designed to work with real-life repositories, as it relies on actual discussions to generate meaningful insights.
    At least 50 merged PRs are required to generate the `best_practices.md` file.

!!! note "Additional customization"
    Teams are encouraged to further customize and refine these insights to better align with their specific development priorities and contexts.
    This can be done by editing the `best_practices.md` file directly when the PR is created, or iteratively over time to enhance the 'best practices' suggestions provided by Qodo Merge.

The tool can be invoked manually by commenting on any PR:

```
/scan_repo_discussions
```

As a response, the bot will create a new PR that contains an auto-generated `best_practices.md` file.
Note that the scan can take several minutes to complete, since up to 250 PRs are scanned.

## Example usage

![scan1](https://codium.ai/images/pr_agent/scan_repo_discussions_1.png){width=640}

The PR created by the bot:

![scan1](https://codium.ai/images/pr_agent/scan_repo_discussions_2.png){width=640}

The `best_practices.md` file in the PR:

![scan1](https://codium.ai/images/pr_agent/scan_repo_discussions_3.png){width=640}

### Configuration options

- Use `/scan_repo_discussions --scan_repo_discussions.force_scan=true` to force generating a PR with a new `best_practices.md` file, even if it already exists (by default, the bot will not generate a new file if it already exists).
- Use `/scan_repo_discussions --scan_repo_discussions.days_back=X` to specify the number of days back to scan for discussions. The default is 365 days.
- Use `/scan_repo_discussions --scan_repo_discussions.minimal_number_of_prs=X` to specify the minimum number of merged PRs needed to generate the `best_practices.md` file. The default is 50 PRs.

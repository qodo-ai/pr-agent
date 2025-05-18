`Platforms supported: GitHub`

## Overview

The `repo_statistics` tool analyzes statistics from merged pull requests over the past 12 months prior to Qodo Merge installation.
It calculates key metrics that help teams establish a baseline of their PR workflow efficiency.

!!! note "Active repositories are needed"
    The tool is designed to work with real-life repositories, as it relies on actual discussions to generate meaningful insights.
    At least 30 merged PRs are required to generate meaningful statistical data.

### Metrics Analyzed

- **Median time to merge:** The median time it takes for PRs to be merged after opening
- **Average time to merge:** The average time it takes for PRs to be merged after opening
- **Median time to first comment:** The median time it takes to get the first comment on a PR
- **Average time to first comment:** The average time it takes to get the first comment on a PR


### Usage

The tool can be invoked manually by commenting on any PR:

```
/repo_statistics
```

In response, the bot will comment with the statistical data.
Note that the scan can take several minutes to complete, since up to 100 PRs are scanned.

!!! info "Automatic trigger"
    Upon adding the Qodo Merge bot to a repository, the tool will automatically scan the last 365 days of PRs and send them to MixPanel, if enabled.

## Example usage

![repo statistics comment](https://codium.ai/images/pr_agent/repo_statistics_comment.png){width=640}

MixPanel optional presentation:

![repo statistics mixpanel](https://codium.ai/images/pr_agent/repo_statistics_mixpanel.png){width=640}


### Configuration options

- Use `/repo_statistics --repo_statistics.days_back=X` to specify the number of days back to scan for discussions. The default is 365 days.
- Use `/repo_statistics --repo_statistics.minimal_number_of_prs=X` to specify the minimum number of merged PRs needed to generate the statistics. The default is 30 PRs.

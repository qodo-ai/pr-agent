# Interactivity 💎

`Supported Git Platforms: GitHub, GitLab`

## Overview

Qodo Merge transforms static code reviews into interactive experiences by enabling direct actions from pull request (PR) comments.
Developers can immediately trigger actions and apply changes with simple checkbox clicks.

This focused workflow maintains context while dramatically reducing the time between PR creation and final merge.
The approach eliminates manual steps, provides clear visual indicators, and creates immediate feedback loops all within the same interface.

## Key Interactive Features

### 1\. Interactive `/improve` Tool

The [`/improve`](https://qodo-merge-docs.qodo.ai/tools/improve/) command delivers a comprehensive interactive experience:

- _**Apply this suggestion**_: Clicking this checkbox instantly converts a suggestion into a committable code change. When committed to the PR, changes made to code that was flagged for improvement will be marked with a check mark, allowing developers to easily track and review implemented recommendations.

- _**More**_: Triggers additional suggestions generation while keeping each suggestion focused and relevant as the original set

- _**Update**_: Triggers a re-analysis of the code, providing updated suggestions based on the latest changes

- _**Author self-review**_: Interactive acknowledgment that developers have opened and reviewed collapsed suggestions

### 2\. Interactive `/analyze` Tool

The [`/analyze`](https://qodo-merge-docs.qodo.ai/tools/analyze/) command provides component-level analysis with interactive options for each identified code component:

- Interactive checkboxes to generate tests, documentation, and code suggestions for specific components

- On-demand similar code search that activates when a checkbox is clicked

- Component-specific actions that trigger only for the selected elements, providing focused assistance

### 3\. Interactive `/help` Tool

The [`/help`](https://qodo-merge-docs.qodo.ai/tools/help/) command not only lists available tools and their descriptions but also enables immediate tool invocation through interactive checkboxes.
When a user checks a tool's checkbox, Qodo Merge instantly triggers that tool without requiring additional commands.
This transforms the standard help menu into an interactive launch pad for all Qodo Merge capabilities, eliminating context switching by keeping developers within their PR workflow.

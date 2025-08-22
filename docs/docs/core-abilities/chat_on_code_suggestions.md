# Chat on code suggestions 💎

`Supported Git Platforms: GitHub, GitLab`

## Overview

Qodo Merge implements an orchestrator agent that enables interactive code discussions, listening and responding to comments without requiring explicit tool calls.
The orchestrator intelligently analyzes your responses to determine if you want to implement a suggestion, ask a question, or request help, then delegates to the appropriate specialized tool.

To minimize unnecessary notifications and maintain focused discussions, the orchestrator agent will only respond to comments made directly within the inline code suggestion discussions it has created (`/improve`) or within discussions initiated by the `/implement` command.

##  Getting Started

### Setup

Enable interactive code discussions by adding the following to your configuration file (default is `True`):

```toml
[pr_code_suggestions]
enable_chat_in_code_suggestions = true
```


### Activation

#### `/improve`

To obtain dynamic responses, the following steps are required:

1. Run the `/improve` command (mostly automatic)
2. Check the `/improve` recommendation checkboxes (_Apply this suggestion_) to have Qodo Merge generate a new inline code suggestion discussion
3. The orchestrator agent will then automatically listen to and reply to comments within the discussion without requiring additional commands

#### `/implement`

To obtain dynamic responses, the following steps are required:

1. Select code lines in the PR diff and run the `/implement` command
2. Wait for Qodo Merge to generate a new inline code suggestion
3. The orchestrator agent will then automatically listen to and reply to comments within the discussion without requiring additional commands


## Explore the available interaction patterns

!!! tip "Tip: Direct the agent with keywords"
    Use "implement" or "apply" for code generation. Use "explain", "why", or "how" for information and help.

=== "Asking for Details"
    ![Chat on code suggestions ask](https://codium.ai/images/pr_agent/improve_chat_on_code_suggestions_ask.png){width=512}

=== "Implementing Suggestions"
    ![Chat on code suggestions implement](https://codium.ai/images/pr_agent/improve_chat_on_code_suggestions_implement.png){width=512}

=== "Providing Additional Help"
    ![Chat on code suggestions help](https://codium.ai/images/pr_agent/improve_chat_on_code_suggestions_help.png){width=512}

# Installation

> For remote suggestions, Blackbox Merge needs to be installed and active on your Git repository (GitHub / GitLab), and provide code suggestions in a table format for your Pull Requests (PRs).

## Install Blackbox Command

Blackbox Merge CLI is a review tool within [Blackbox Command](https://docs.Blackbox.ai/Blackbox-documentation/Blackbox-command), a command-line interface for running and managing AI agents.

To use Blackbox Command, you'll need first Node.js and npm installed.
Then, to install Blackbox Command, run:

```bash
npm install -g @Blackbox/command
```

**Login and Setup**

To start using Blackbox Command, you need to log in first:

```bash
Blackbox login
```

Once login is completed, you'll receive an API key in the terminal.
The API key is also saved locally in the .Blackbox folder in your home directory, and can be reused (e.g., in CI).
The key is tied to your user account and subject to the same usage limits.


## Using Blackbox Merge CLI

After you set up Blackbox Command, you can start using Blackbox Merge CLI by running:

```bash
Blackbox merge
```
### Set Up Git Client
On first run, the CLI will check for your Git client (GitHub CLI or GitLab CLI).
If not found, it will guide you through the installation process.

![GH Installation](https://www.Blackbox.ai/images/pr_agent/qm_cli_gh_install_prompt.png){width=384}


## Quick Usage

There are two ways to specify which PR to review:

(1) **Auto Detect PR from current branch**
run this command in your CLI:

```bash
Blackbox merge
```

(2) **Specify PR number or URL**

```bash
Blackbox merge 303

Blackbox merge https://github.com/owner/repo/pull/303
```

Then the tool will automatically fetch the suggestions from the PR and display them in an interactive table.

![Fix All Mode](https://www.Blackbox.ai/images/pr_agent/qm_cli_main_table_fix_all.png){width=768}


## Next Steps

**[Usage](usage.md)** - Navigate, explore, and implement suggestions


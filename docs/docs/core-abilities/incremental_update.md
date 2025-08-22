# Incremental Update 💎

`Supported Git Platforms: GitHub, GitLab (Both cloud & server. For server: Version 17 and above)`

## Overview
The Incremental Update feature helps users focus on feedback for their newest changes, making large PRs more manageable.

### How it works

=== "Update Option on Subsequent Commits"
    ![code_suggestions_update](https://www.qodo.ai/images/pr_agent/inc_update_before.png){width=512}

=== "Generation of Incremental Update"
    ![code_suggestions_inc_update_result](https://www.qodo.ai/images/pr_agent/inc_update_shown.png){width=512}

___

Whenever new commits are pushed following a recent code suggestions report for this PR, an Update button appears (as seen above).

Once the user clicks on the button:

- The `improve` tool identifies the new changes (the "delta")
- Provides suggestions on these recent changes
- Combines these suggestions with the overall PR feedback, prioritizing delta-related comments
- Marks delta-related comments with a textual indication followed by an asterisk (*) with a link to this page, so they can easily be identified

### Benefits for Developers

- Focus on what matters: See feedback on newest code first
- Clearer organization: Comments on recent changes are clearly marked
- Better workflow: Address feedback more systematically, starting with recent changes



# Tools

Here is a list of Qodo Merge tools, each with a dedicated page that explains how to use it:

| Tool                                                                                     | Description                                                                                                                                 |
|------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------|
| **[PR Description (`/describe`](./describe.md))**                                        | Automatically generating PR description - title, type, summary, code walkthrough and labels                                                 |
| **[PR Review (`/review`](./review.md))**                                                 | Adjustable feedback about the PR, possible issues, security concerns, review effort and more                                                |
| **[Code Suggestions (`/improve`](./improve.md))**                                        | Code suggestions for improving the PR                                                                                                       |
| **[Question Answering (`/ask ...`](./ask.md))**                                          | Answering free-text questions about the PR, or on specific code lines                                                                       |
| **[Help (`/help`](./help.md))**                                                          | Provides a list of all the available tools. Also enables to trigger them interactively (💎)                                                 |
| **[Help Docs (`/help_docs`](./help_docs.md))**                                           | Answer a free-text question based on a git documentation folder.                                                                            |
| **[Update Changelog (`/update_changelog`](./update_changelog.md))**                      | Automatically updating the CHANGELOG.md file with the PR changes                                                                            |
| **💎 [Add Documentation (`/add_docs`](./documentation.md))**                             | Generates documentation to methods/functions/classes that changed in the PR                                                                 |
| **💎 [Analyze (`/analyze`](./analyze.md))**                                              | Identify code components that changed in the PR, and enables to interactively generate tests, docs, and code suggestions for each component |
| **💎 [CI Feedback (`/checks ci_job`](./ci_feedback.md))**                                | Automatically generates feedback and analysis for a failed CI job                                                                           |
| **💎 [Compliance (`/compliance`](./compliance.md))**                                  | Comprehensive compliance checks for security, ticket requirements, and custom organizational rules                                          |
| **💎 [Custom Prompt (`/custom_prompt`](./custom_prompt.md))**                            | Automatically generates custom suggestions for improving the PR code, based on specific guidelines defined by the user                      |
| **💎 [Generate Custom Labels (`/generate_labels`](./custom_labels.md))**                 | Generates custom labels for the PR, based on specific guidelines defined by the user                                                        |
| **💎 [Generate Tests (`/test`](./test.md))**                                             | Automatically generates unit tests for a selected component, based on the PR code changes                                                   |
| **💎 [Implement (`/implement`](./implement.md))**                                        | Generates implementation code from review suggestions                                                                                       |
| **💎 [Improve Component (`/improve_component component_name`](./improve_component.md))** | Generates code suggestions for a specific code component that changed in the PR                                                             |
| **💎 [PR to Ticket (`/create_ticket`](./pr_to_ticket.md))**                          | Generates ticket in the ticket tracking systems (Jira, Linear, or Git provider issues) based on PR content                                  |
| **💎 [Scan Repo Discussions (`/scan_repo_discussions`](./scan_repo_discussions.md))**    | Generates `best_practices.md` file based on previous discussions in the repository                                                          |
| **💎 [Similar Code (`/similar_code`](./similar_code.md))**                               | Retrieves the most similar code components from inside the organization's codebase, or from open-source code.                               |

Note that the tools marked with 💎 are available only for Qodo Merge users.
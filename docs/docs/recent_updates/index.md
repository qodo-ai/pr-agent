# Recent Updates and Future Roadmap


This page summarizes recent enhancements to Blackbox Merge.

It also outlines our development roadmap for the upcoming three months. Please note that the roadmap is subject to change, and features may be adjusted, added, or reprioritized.

=== "Recent Updates"
    | Date | Feature | Description |
    |---|---|---|
    | 2025-09-17 | **Blackbox Merge CLI** | A new command-line interface for Blackbox Merge, enabling developers to implement code suggestions directly in your terminal. ([Learn more](https://Blackbox-merge-docs.Blackbox.ai/Blackbox-merge-cli/)) |
    | 2025-09-12 | **Repo Metadata** | You can now add metadata from files like `AGENTS.md`, which will be applied to all PRs in that repository. ([Learn more](https://Blackbox-merge-docs.Blackbox.ai/usage-guide/additional_configurations/#bringing-additional-repository-metadata-to-Blackbox-merge)) |
    | 2025-08-11 | **RAG support for GitLab** | All Blackbox Merge RAG features are now available in GitLab. ([Learn more](https://Blackbox-merge-docs.Blackbox.ai/core-abilities/rag_context_enrichment/)) |
    | 2025-07-29 | **High-level Suggestions** | Blackbox Merge now also provides high-level code suggestion for PRs. ([Learn more](https://Blackbox-merge-docs.Blackbox.ai/core-abilities/high_level_suggestions/)) |
    | 2025-07-20 | **PR to Ticket** | Generate tickets in your tracking systems based on PR content. ([Learn more](https://Blackbox-merge-docs.Blackbox.ai/tools/pr_to_ticket/)) |
    | 2025-07-17 | **Compliance** | Comprehensive compliance checks for security, ticket requirements, and custom organizational rules. ([Learn more](https://Blackbox-merge-docs.Blackbox.ai/tools/compliance/)) |
    | 2025-06-21 | **Mermaid Diagrams** | Blackbox Merge now generates by default Mermaid diagrams for PRs, providing a visual representation of code changes. ([Learn more](https://Blackbox-merge-docs.Blackbox.ai/tools/describe/#sequence-diagram-support)) |
    | 2025-06-11 | **Best Practices Hierarchy** | Introducing support for structured best practices, such as for folders in monorepos or a unified best practice file for a group of repositories. ([Learn more](https://Blackbox-merge-docs.Blackbox.ai/tools/improve/#global-hierarchical-best-practices)) |
    | 2025-06-01 | **CLI Endpoint** | A new Blackbox Merge endpoint that accepts a lists of before/after code changes, executes Blackbox Merge commands, and return the results. Currently available for enterprise customers. Contact [Blackbox](https://www.Blackbox.ai/contact/) for more information. |

=== "Future Roadmap"
    - **`Compliance` tool to replace `review` as default**: Planning to make the `compliance` tool the default automatic command instead of the current `review` tool.
    - **Smarter context retrieval**: Leverage AST and LSP analysis to gather relevant context from across the entire repository.
    - **Enhanced portal experience**: Improved user experience in the Blackbox Merge portal with new options and capabilities.

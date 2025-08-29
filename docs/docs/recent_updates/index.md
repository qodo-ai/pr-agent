# Recent Updates and Future Roadmap


This page summarizes recent enhancements to Qodo Merge.

It also outlines our development roadmap for the upcoming three months. Please note that the roadmap is subject to change, and features may be adjusted, added, or reprioritized.

=== "Recent Updates"
    | Date | Feature | Description |
    |---|---|---|
    | 2025-08-27 | **GitLab submodule diff expansion** | Optionally expand GitLab submodule updates into full diffs. ([Learn more](https://qodo-merge-docs.qodo.ai/usage-guide/additional_configurations/#expand-gitlab-submodule-diffs)) |
    | 2025-08-11 | **RAG support for GitLab** | All Qodo Merge RAG features are now available in GitLab. ([Learn more](https://qodo-merge-docs.qodo.ai/core-abilities/rag_context_enrichment/)) |
    | 2025-07-29 | **High-level Suggestions** | Qodo Merge now also provides high-level code suggestion for PRs. ([Learn more](https://qodo-merge-docs.qodo.ai/core-abilities/high_level_suggestions/)) |
    | 2025-07-20 | **PR to Ticket** | Generate tickets in your tracking systems based on PR content. ([Learn more](https://qodo-merge-docs.qodo.ai/tools/pr_to_ticket/)) |
    | 2025-07-17 | **Compliance** | Comprehensive compliance checks for security, ticket requirements, and custom organizational rules. ([Learn more](https://qodo-merge-docs.qodo.ai/tools/compliance/)) |
    | 2025-07-01 | **Receiving Qodo Merge feedback locally** | You can receive automatic feedback from Qodo Merge on your local IDE after each commit. ([Learn more](https://github.com/qodo-ai/agents/tree/main/agents/qodo-merge-post-commit)) |
    | 2025-06-21 | **Mermaid Diagrams** | Qodo Merge now generates by default Mermaid diagrams for PRs, providing a visual representation of code changes. ([Learn more](https://qodo-merge-docs.qodo.ai/tools/describe/#sequence-diagram-support)) |
    | 2025-06-11 | **Best Practices Hierarchy** | Introducing support for structured best practices, such as for folders in monorepos or a unified best practice file for a group of repositories. ([Learn more](https://qodo-merge-docs.qodo.ai/tools/improve/#global-hierarchical-best-practices)) |
    | 2025-06-05 | **Simplified Free Tier** | Qodo Merge now offers a simplified free tier with a monthly limit of 75 PR reviews per organization, replacing the previous two-week trial. ([Learn more](https://qodo-merge-docs.qodo.ai/installation/qodo_merge/#cloud-users)) |
    | 2025-06-01 | **CLI Endpoint** | A new Qodo Merge endpoint that accepts a lists of before/after code changes, executes Qodo Merge commands, and return the results. Currently available for enterprise customers. Contact [Qodo](https://www.qodo.ai/contact/) for more information. |

=== "Future Roadmap"
    - **`Compliance` tool to replace `review` as default**: Planning to make the `compliance` tool the default automatic command instead of the current `review` tool.
    - **Smarter context retrieval**: Leverage AST and LSP analysis to gather relevant context from across the entire repository.
    - **Enhanced portal experience**: Improved user experience in the Qodo Merge portal with new options and capabilities.

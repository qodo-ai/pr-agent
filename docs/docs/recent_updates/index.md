# Recent Updates and Future Roadmap


This page summarizes recent enhancements to PR-Agent.

It also outlines our development roadmap for the upcoming three months. Please note that the roadmap is subject to change, and features may be adjusted, added, or reprioritized.

=== "Recent Updates"
    | Date | Feature | Description |
    |---|---|---|
    | 2025-09-12 | **Repo Metadata** | You can now add metadata from files like `AGENTS.md`, which will be applied to all PRs in that repository. ([Learn more](../usage-guide/additional_configurations.md#bringing-additional-repository-metadata-to-pr-agent)) |
    | 2025-08-11 | **RAG support for GitLab** | All PR-Agent RAG features are now available in GitLab. ([Learn more](../core-abilities/rag_context_enrichment.md)) |
    | 2025-06-21 | **Mermaid Diagrams** | PR-Agent now generates by default Mermaid diagrams for PRs, providing a visual representation of code changes. ([Learn more](../tools/describe.md#sequence-diagram-support)) |
    | 2025-06-11 | **Best Practices Hierarchy** | Introducing support for structured best practices, such as for folders in monorepos or a unified best practice file for a group of repositories. ([Learn more](../tools/improve.md#global-hierarchical-best-practices)) |
    | 2025-06-01 | **CLI Endpoint** | A new PR-Agent endpoint that accepts a lists of before/after code changes, executes PR-Agent commands, and return the results. Currently available for enterprise customers. Contact [Codium](https://www.codium.ai/contact/) for more information. |

=== "Future Roadmap"
    - **Smarter context retrieval**: Leverage AST and LSP analysis to gather relevant context from across the entire repository.
    - **Enhanced portal experience**: Improved user experience in the PR-Agent portal with new options and capabilities.

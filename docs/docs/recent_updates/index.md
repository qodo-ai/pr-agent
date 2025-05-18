# Recent Updates and Future Roadmap

`Page last updated: 2025-05-11`

This page summarizes recent enhancements to Qodo Merge (last three months).

It also outlines our development roadmap for the upcoming three months. Please note that the roadmap is subject to change, and features may be adjusted, added, or reprioritized.

=== "Recent Updates"
    - **Qodo Merge Pull Request Benchmark** - evaluating the performance of LLMs in analyzing pull request code ([Learn more](https://qodo-merge-docs.qodo.ai/pr_benchmark/))
    - **Chat on Suggestions**:  Users can now chat with Qodo Merge code suggestions ([Learn more](https://qodo-merge-docs.qodo.ai/tools/improve/#chat-on-code-suggestions))
    - **Scan Repo Discussions Tool**: A new tool that analyzes past code discussions to generate a `best_practices.md` file, distilling key insights and recommendations. ([Learn more](https://qodo-merge-docs.qodo.ai/tools/scan_repo_discussions/))
    - **Enhanced Models**: Qodo Merge now defaults to a combination of top models (Claude Sonnet 3.7 and Gemini 2.5 Pro) and incorporates dedicated code validation logic for improved results. ([Details 1](https://qodo-merge-docs.qodo.ai/usage-guide/qodo_merge_models/), [Details 2](https://qodo-merge-docs.qodo.ai/core-abilities/code_validation/))
    - **Chrome Extension Update**: Qodo Merge Chrome extension now supports single-tenant users. ([Learn more](https://qodo-merge-docs.qodo.ai/chrome-extension/options/#configuration-options/))
    - **Repo Statistics Tool**: A new tool that provides repository statistics on time to merge and time to first comment. ([Learn more](https://qodo-merge-docs.qodo.ai/tools/repo_statistics/))

=== "Future Roadmap"
    - **Smart Update**: Upon PR updates, Qodo Merge will offer tailored code suggestions, addressing both the entire PR and the specific incremental changes since the last feedback.
    - **CLI Endpoint**: A new Qodo Merge endpoint will accept lists of before/after code changes, execute Qodo Merge commands, and return the results.
    - **Simplified Free Tier**: We plan to transition from a two-week free trial to a free tier offering a limited number of suggestions per month per organization.
    - **Best Practices Hierarchy**: Introducing support for structured best practices, such as for folders in monorepos or a unified best practice file for a group of repositories.
    - **Installation Metrics**: Upon installation, Qodo Merge will analyze past PRs for key metrics (e.g., time to merge, time to first reviewer feedback), enabling pre/post-installation comparison to calculate ROI.
# Code Validation 💎

`Supported Git Platforms: GitHub, GitLab, Bitbucket`


## Introduction

The Git environment usually represents the final stage before code enters production. Hence, Detecting bugs and issues during the review process is critical.

The [`improve`](https://qodo-merge-docs.qodo.ai/tools/improve/) tool provides actionable code suggestions for your pull requests, aiming to help detect and fix bugs and problems.
By default, suggestions appear as a comment in a table format:

![code_suggestions_as_comment_closed.png](https://codium.ai/images/pr_agent/code_suggestions_as_comment_closed.png){width=512}

![code_suggestions_as_comment_open.png](https://codium.ai/images/pr_agent/code_suggestions_as_comment_open.png){width=512}

## Validation of Code Suggestions

Each suggestion in the table can be "applied" by clicking on the `Apply this suggestion` checkbox, converting it to a committable Git code change that can be committed directly to the PR.
This approach allows to fix issues without returning to your IDE for manual edits — significantly faster and more convenient.

However, committing a suggestion in a Git environment carries more risk than in a local IDE, as you don't have the opportunity to fully run and test the code before committing.

To balance convenience with safety, Qodo Merge implements a dual validation system for each generated code suggestion:

1) **Localization** - Qodo Merge confirms that the suggestion's line numbers and surrounding code, as predicted by the model, actually match the repo code. This means that the model correctly identified the context and location of the code to be changed.

2) **"Compilation"** - Using static code analysis, Qodo Merge verifies that after applying the suggestion, the modified file will still be valid, meaning tree-sitter syntax processing will not throw an error. This process is relevant for multiple programming languages, see [here](https://pypi.org/project/tree-sitter-languages/) for the full list of supported languages.

When a suggestion fails to meet these validation criteria, it may still provide valuable feedback, but isn't suitable for direct application to the PR.
In such cases, Qodo Merge will omit the 'apply' checkbox and instead display:

`[To ensure code accuracy, apply this suggestion manually]`

All suggestions that pass these validations undergo a final stage of **self-reflection**, where the AI model evaluates, scores, and re-ranks its own suggestions, eliminating any that are irrelevant or incorrect.
Read more about this process in the [self-reflection](https://qodo-merge-docs.qodo.ai/core-abilities/self_reflection/) page.

## Conclusion

The validation methods described above enhance the reliability of code suggestions and help PR authors determine which suggestions are safer to apply in the Git environment.
Of course, additional factors should be considered, such as suggestion complexity and potential code impact.

Human judgment remains essential. After clicking 'apply', Qodo Merge still presents the 'before' and 'after' code snippets for review, allowing you to assess the changes before finalizing the commit.

![improve](https://codium.ai/images/pr_agent/improve.png){width=512}

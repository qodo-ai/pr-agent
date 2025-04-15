
<b>Pattern 1: Wrap critical operations with try-except blocks to handle potential exceptions and provide detailed error logging, especially for network operations, file I/O, and API calls.</b>

Example code before:
```
def get_git_repo_url(self, issues_or_pr_url: str) -> str:
    repo_path = self._get_owner_and_repo_path(issues_or_pr_url)
    if not repo_path or repo_path not in issues_or_pr_url:
        get_logger().error(f"Unable to retrieve owner/path from url: {issues_or_pr_url}")
        return ""
    return f"{issues_or_pr_url.split(repo_path)[0]}{repo_path}.git"
```

Example code after:
```
def get_git_repo_url(self, issues_or_pr_url: str) -> str:
    try:
        repo_path = self._get_owner_and_repo_path(issues_or_pr_url)
        if not repo_path or repo_path not in issues_or_pr_url:
            get_logger().error(f"Unable to retrieve owner/path from url: {issues_or_pr_url}")
            return ""
        return f"{issues_or_pr_url.split(repo_path)[0]}{repo_path}.git"
    except Exception as e:
        get_logger().error(f"Failed to get git repo url from {issues_or_pr_url}, error: {e}")
        return ""
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/pr-agent/pull/1644#discussion_r2013912636
- https://github.com/qodo-ai/pr-agent/pull/1263#discussion_r1782129216
</details>


___

<b>Pattern 2: Use get_logger() consistently for error handling instead of print statements, with appropriate log levels and including relevant context in the artifact parameter.</b>

Example code before:
```
print(f"Failed to fetch sub-issues. Error: {e}")
```

Example code after:
```
get_logger().exception(f"Failed to fetch sub-issues. Error: {e}", artifact={"url": url})
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/pr-agent/pull/1529#discussion_r1958684550
- https://github.com/qodo-ai/pr-agent/pull/1529#discussion_r1958686068
- https://github.com/qodo-ai/pr-agent/pull/1634#discussion_r2007976915
- https://github.com/qodo-ai/pr-agent/pull/1529#discussion_r1964110734
</details>


___

<b>Pattern 3: Add defensive input validation to prevent runtime errors, especially when working with user-provided data, API responses, or when accessing nested data structures.</b>

Example code before:
```
if model_type == ModelType.WEAK:
    model = get_settings().config.model_weak
else:
    model = get_settings().config.model
```

Example code after:
```
if get_settings().config.get('model_weak') and model_type == ModelType.WEAK:
    model = get_settings().config.model_weak
else:
    model = get_settings().config.model
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/pr-agent/pull/1387#discussion_r1876090216
- https://github.com/qodo-ai/pr-agent/pull/1290#discussion_r1798939921
- https://github.com/qodo-ai/pr-agent/pull/1644#discussion_r2032621065
</details>


___

<b>Pattern 4: Maintain consistent formatting in documentation, including proper punctuation, capitalization, and spacing, especially in user-facing content.</b>

Example code before:
```
Note that the following features are available only for Qodo Merge💎 users:
- The `Apply this suggestion` checkbox, which interactively converts a suggestion into a committable code comment
- The `More` checkbox to generate additional suggestions
```

Example code after:
```
Note that the following features are available only for Qodo Merge💎 users:
- The `Apply this suggestion` checkbox, which interactively converts a suggestion into a committable code comment.
- The `More` checkbox to generate additional suggestions.
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/pr-agent/pull/1543#discussion_r1958093666
- https://github.com/qodo-ai/pr-agent/pull/1613#discussion_r1986312529
- https://github.com/qodo-ai/pr-agent/pull/1613#discussion_r1986313421
- https://github.com/qodo-ai/pr-agent/pull/1517#discussion_r1942896094
</details>


___

<b>Pattern 5: Refactor complex code blocks into separate methods with clear responsibilities to improve readability and maintainability.</b>

Example code before:
```
# A large block of code with multiple responsibilities
if (model in self.claude_extended_thinking_models) and get_settings().config.get("enable_claude_extended_thinking", False):
    extended_thinking_budget_tokens = get_settings().config.get("extended_thinking_budget_tokens", 32000)
    extended_thinking_max_output_tokens = get_settings().config.get("extended_thinking_max_output_tokens", 64000)
    
    # Validate extended thinking parameters
    if not isinstance(extended_thinking_budget_tokens, int) or extended_thinking_budget_tokens <= 0:
        raise ValueError(f"extended_thinking_budget_tokens must be a positive integer, got {extended_thinking_budget_tokens}")
    if not isinstance(extended_thinking_max_output_tokens, int) or extended_thinking_max_output_tokens <= 0:
        raise ValueError(f"extended_thinking_max_output_tokens must be a positive integer, got {extended_thinking_max_output_tokens}")
    if extended_thinking_max_output_tokens < extended_thinking_budget_tokens:
        raise ValueError(f"extended_thinking_max_output_tokens ({extended_thinking_max_output_tokens}) must be greater than or equal to extended_thinking_budget_tokens ({extended_thinking_budget_tokens})")
    
    kwargs["thinking"] = {
        "type": "enabled",
        "budget_tokens": extended_thinking_budget_tokens
    }
    kwargs["max_tokens"] = extended_thinking_max_output_tokens
    kwargs["temperature"] = 1
```

Example code after:
```
# Extract the functionality into a dedicated method
def _configure_claude_extended_thinking(self, model, kwargs):
    if (model in self.claude_extended_thinking_models) and get_settings().config.get("enable_claude_extended_thinking", False):
        # Implementation details moved to the dedicated method
        # ...
        return kwargs
    return kwargs

# In the main method:
kwargs = self._configure_claude_extended_thinking(model, kwargs)
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/pr-agent/pull/1605#discussion_r1980783780
- https://github.com/qodo-ai/pr-agent/pull/1391#discussion_r1879870807
</details>


___

<b>Pattern 6: Add descriptive comments for complex logic or non-obvious code to improve maintainability and help future developers understand the code's purpose.</b>

Example code before:
```
if not issue or not isinstance(issue, dict):
    continue
```

Example code after:
```
# Skip empty issues or non-dictionary items to ensure valid data structure
if not issue or not isinstance(issue, dict):
    continue
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/pr-agent/pull/1262#discussion_r1782097204
- https://github.com/qodo-ai/pr-agent/pull/1583#discussion_r1971790979
</details>


___

<b>Pattern 7: Use descriptive variable names that clearly indicate the purpose and content of the data they hold to improve code readability.</b>

Example code before:
```
issues = value
for i, issue in enumerate(issues):
    # Process each issue
```

Example code after:
```
focus_areas = value
for i, focus_area in enumerate(focus_areas):
    # Process each focus area
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/pr-agent/pull/1262#discussion_r1782097201
</details>


___

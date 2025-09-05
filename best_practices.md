
<b>Pattern 1: Wrap critical operations with try-except blocks to handle potential exceptions, especially for file operations, API calls, and data parsing functions.</b>

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
- https://github.com/qodo-ai/pr-agent/pull/1391#discussion_r1879870807
</details>


___

<b>Pattern 2: Use proper logging methods instead of print statements, with get_logger().error() for errors, get_logger().warning() for warnings, and get_logger().info() for informational messages.</b>

Example code before:
```
if isinstance(response_tuple, tuple) and len(response_tuple) == 3:
    response_json = json.loads(response_tuple[2])
else:
    print("Unexpected response format:", response_tuple)
    return sub_issues
```

Example code after:
```
if isinstance(response_tuple, tuple) and len(response_tuple) == 3:
    response_json = json.loads(response_tuple[2])
else:
    get_logger().error(f"Unexpected response format", artifact={"response": response_tuple})
    return sub_issues
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/pr-agent/pull/1529#discussion_r1958684550
- https://github.com/qodo-ai/pr-agent/pull/1529#discussion_r1958686068
- https://github.com/qodo-ai/pr-agent/pull/1529#discussion_r1964110734
- https://github.com/qodo-ai/pr-agent/pull/1634#discussion_r2007976915
</details>


___

<b>Pattern 3: Move specific imports to where they are actually used rather than at the top of the file, especially for rarely used or heavy dependencies.</b>

Example code before:
```
import os
from azure.identity import ClientSecretCredential
import litellm
import openai
import requests
```

Example code after:
```
import os
import litellm
import openai
import requests

# Later in the code where Azure AD is actually used:
if get_settings().get("AZURE_AD.CLIENT_ID", None):
    from azure.identity import ClientSecretCredential
    # Azure AD specific code...
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/pr-agent/pull/1698#discussion_r2046221654
</details>


___

<b>Pattern 4: Add defensive checks for potentially None or invalid values before performing operations on them, especially when working with external data or API responses.</b>

Example code before:
```
model_is_from_o_series = re.match(r"^o[1-9](-mini|-preview)?$", model)
if ('gpt' in get_settings().config.model.lower() or model_is_from_o_series) and get_settings().get('openai.key'):
    return encoder_estimate
```

Example code after:
```
if model is None:
    get_logger().warning("Model is None, cannot determine model type accurately")
    return encoder_estimate

if not isinstance(model, str):
    get_logger().warning(f"Model is not a string type: {type(model)}")
    return encoder_estimate
    
model_is_from_o_series = re.match(r"^o[1-9](-mini|-preview)?$", model)
openai_key_exists = get_settings().get('openai.key') is not None

if (('gpt' in model.lower() or model_is_from_o_series) and openai_key_exists):
    return encoder_estimate
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/pr-agent/pull/1644#discussion_r2032621065
- https://github.com/qodo-ai/pr-agent/pull/1529#discussion_r1958694146
- https://github.com/qodo-ai/pr-agent/pull/1391#discussion_r1879875496
</details>


___

<b>Pattern 5: Avoid redundant code initialization and reuse existing objects or instances when possible, especially for resource-intensive operations.</b>

Example code before:
```
if tickets:
    provider = GithubProvider()
    
    for ticket in tickets:
        # Extract sub-issues
        sub_issues_content = []
        try:
            sub_issues = provider.fetch_sub_issues(ticket)
```

Example code after:
```
if tickets:
    for ticket in tickets:
        # Extract sub-issues
        sub_issues_content = []
        try:
            sub_issues = git_provider.fetch_sub_issues(ticket)
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/pr-agent/pull/1529#discussion_r1964085987
- https://github.com/qodo-ai/pr-agent/pull/1529#discussion_r1964088304
</details>


___

<b>Pattern 6: Use descriptive variable names and add explanatory comments for complex logic or non-obvious code to improve maintainability and readability.</b>

Example code before:
```
issues = value
for i, issue in enumerate(issues):
    try:
        if not issue or not isinstance(issue, dict):
            continue
```

Example code after:
```
focus_areas = value
for i, focus_area in enumerate(focus_areas):
    try:
        # Skip empty issues or non-dictionary items to ensure valid data structure
        if not focus_area or not isinstance(focus_area, dict):
            continue
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/pr-agent/pull/1262#discussion_r1782097201
- https://github.com/qodo-ai/pr-agent/pull/1262#discussion_r1782097204
- https://github.com/qodo-ai/pr-agent/pull/1583#discussion_r1971790979
</details>


___

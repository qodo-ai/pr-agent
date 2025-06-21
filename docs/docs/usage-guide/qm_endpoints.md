
# Overview

By default, Qodo Merge processes webhooks that respond to events or comments (for example, PR is opened), posting its responses directly on the PR page.

Qodo Merge now features two CLI endpoints that let you invoke its tools and receive responses directly (both as formatted markdown as well as a raw JSON), rather than having them posted to the PR page:

- **Pull Request Endpoint** - Accepts GitHub PR URL, along with the desired tool to invoke (**note**: only available on-premises, or single tenant).
- **Diff Endpoint** - Git agnostic option that accepts a comparison of two states, either as a list of “before” and “after” files’ contents, or as a unified diff file,  along with the desired tool to invoke.

# Setup

## Enabling desired endpoints (for on-prem deployment)

:bulb: Add the following to your helm chart\secrets file:

Pull Request Endpoint:

```toml
[qm_pull_request_endpoint]
enabled = true
```

Diff Endpoint:

```toml
[qm_diff_endpoint]
enabled = true
```

**Important:** This endpoint can only be enabled through the pod's main secret file, **not** through standard configuration files.

## Access Key

The endpoints require the user to provide an access key in each invocation. Choose one of the following options to retrieve such key. 

### Option 1: Endpoint Key (On Premise / Single Tenant only)

Define an endpoint key in the helm chart of your pod configuration:

```toml
[qm_pull_request_endpoint]
enabled = true
endpoint_key = "your-secure-key-here"

```

```toml
[qm_diff_endpoint]
enabled = true
endpoint_key = "your-secure-key-here"
```

### Option 2: API Key for Cloud users (Diff Endpoint only)

Generate a long-lived API key by authenticating the user. We offer two different methods to achieve this:

### - Shell script

Download and run the following script: [gen_api_key.sh](https://github.com/qodo-ai/pr-agent/blob/5dfd696c2b1f43e1d620fe17b9dc10c25c2304f9/pr_agent/scripts/qm_endpoint_auth/gen_api_key.sh) 

### - npx

1. Install node
2. Run: `npx @qodo/gen login`

Regardless of which method used, follow the instructions in the opened browser page. Once logged in successfully via the website, the script will return the generated API key:

```toml
✅ Authentication successful! API key saved.
📋 Your API key: ...
```

**Note:** Each login generates a new API key, making any previous ones **obsolete**.

# Available Tools
Both endpoints support the following Qodo Merge tools:

[**Improve**](https://qodo-merge-docs.qodo.ai/tools/improve/) | [**Review**](https://qodo-merge-docs.qodo.ai/tools/review/) | [**Describe**](https://qodo-merge-docs.qodo.ai/tools/describe/) | [**Ask**](https://qodo-merge-docs.qodo.ai/tools/ask/) | [**Add Docs**](https://qodo-merge-docs.qodo.ai/tools/documentation/) | [**Analyze**](https://qodo-merge-docs.qodo.ai/tools/analyze/) | [**Config**](https://qodo-merge-docs.qodo.ai/tools/config/) | [**Generate Labels**](https://qodo-merge-docs.qodo.ai/tools/custom_labels/) | [**Improve Component**](https://qodo-merge-docs.qodo.ai/tools/improve_component/) | [**Test**](https://qodo-merge-docs.qodo.ai/tools/test/) | [**Custom Prompt**](https://qodo-merge-docs.qodo.ai/tools/custom_prompt/)

# How to Run
For all endpoints, there is a need to specify the access key in the header as the value next to the field: “X-API-Key”.

## Pull Request Endpoint

**URL:** `/api/v1/qm_pull_request`

### Request Format

```json
{
  "pr_url": "<https://github.com/owner/repo/pull/123>",
  "command": "<COMMAND> ARG_1 ARG_2 ..."
}
```

### Usage Examples

### cURL

```bash
curl -X POST "<your-server>/api/v1/qm_pull_request" \\
  -H "Content-Type: application/json" \\
  -H "X-API-Key: <your-key>"
  -d '{
    "pr_url": "<https://github.com/owner/repo/pull/123>",
    "command": "improve"
  }'
```

### Python

```python
import requests
import json

def call_qm_pull_request(pr_url: str, command: str, endpoint_key: str):
    url = "<your-server>/api/v1/qm_pull_request"

    payload = {
        "pr_url": pr_url,
        "command": command
    }

    response = requests.post(
        url=url,
        headers={"Content-Type": "application/json", "X-API-Key": endpoint_key},
        data=json.dumps(payload)
    )

    if response.status_code == 200:
        result = response.json()
        response_str = result.get("response_str")  # Formatted response
        raw_data = result.get("raw_data")          # Metadata and suggestions
        return response_str, raw_data
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None, None
```

## Diff Endpoint

**URL:** `/api/v1/qm_diff`

### Request Format

With before and after files’ contents:

```json
{
  "command": "<COMMAND> ARG_1 ARG_2 ...",
  "diff_files": {
    "<FILE_PATH>": ["<BEFORE_CONTENT>", "<AFTER_CONTENT>"],
    "...": ["...", "..."]
  }
}
```

Alternatively, with unified diff:

```toml
{
  "command": "<COMMAND> ARG_1 ARG_2 ...",
  "diff": "<UNIFIED_DIFF_CONTENT>"
}
```

### Example Payloads

**Using before and after per file (recommended):**

```json
{
  "command": "improve_component hello",
  "diff_files": {
    "src/main.py": [
      "def hello():\\n    print('Hello')",
      "def hello():\\n    print('Hello World')\\n    return 'success'"
    ]
  }
}

```

**Using unified diff:**

```json
{
  "command": "improve",
  "diff": "diff --git a/src/main.py b/src/main.py\\nindex 123..456 100644\\n--- a/src/main.py\\n+++ b/src/main.py\\n@@ -1,2 +1,3 @@\\n def hello():\\n-    print('Hello')\\n+    print('Hello World')\\n+    return 'success'"
}

```

### Usage Examples

### cURL

```bash
curl -X POST "<your-server>/api/v1/qm_diff" \\
  -H "X-API-Key: <YOUR_KEY>" \\
  -H "Content-Type: application/json" \\
  -d @your_request.json
```

### Python

```python
import requests
import json

def call_qm_diff(api_key: str, payload: dict):
    url = "<your-server>/api/v1/qm_diff"

    response = requests.post(
        url=url,
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
        data=json.dumps(payload)
    )

    if response.status_code == 200:
        result = response.json()
        markdown_result = result.get("response_str")  # Formatted markdown
        raw_data = result.get("raw_data")         # Metadata and suggestions
        return markdown_result, raw_data
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return None, None
```

# Response Format
Both endpoints return identical JSON structure:

```json
{
  "response_str": "## PR Code Suggestions ✨\n\n<table>...",
  "raw_data": {
		<FIELD>: <VALUE>
  }
}
```

- **`response_str`** - Formatted markdown for display
- **`raw_data`** - Structured data with detailed suggestions and metadata, if applicable

# Complete Workflows Examples
### Pull Request Endpoint

Given the following “/improve” request:

```toml
{
  "command": "improve",
  "pr_url": "https://github.com/qodo-ai/pr-agent/pull/1831"
}
```

Received the following response:

```toml
{"response_str":"## PR Code Suggestions ✨\n\n<table><thead><tr><td><strong>Category
</strong></td><td align=left><strong>Suggestion&nbsp; &nbsp; &nbsp; &nbsp; &nbsp;
 &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; 
 &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; 
 &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; 
 &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; 
 &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; 
 &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; </strong></td><td align=center>
 <strong>Impact</strong></td></tr><tbody><tr><td rowspan=1>Learned<br>best practice</td>
 \n<td>\n\n\n\n<details><summary>Improve documentation clarity</summary>\n\n___\n
 \n\n**The documentation parameter description contains a grammatical issue. 
 The <br>sentence \"This field remains empty if not applicable\" is unclear in context 
 and <br>should be clarified to better explain what happens when the feature is not 
 <br>applicable.**\n\n[docs/docs/tools/describe.md [128-129]]
 (https://github.com/qodo-ai/pr-agent/pull/1831/files#diff-960aad71fec9617804a02c904da37db217b6ba8a48fec3ac8bda286511d534ebR128-R129)
 \n\n```diff\n <td><b>enable_pr_diagram</b></td>\n-<td>If set to true, the tool 
 will generate a horizontal Mermaid flowchart summarizing the main pull request 
 changes. This field remains empty if not applicable. Default is false.</td>\n
 +<td>If set to true, the tool will generate a horizontal Mermaid flowchart 
 summarizing the main pull request changes. No diagram will be generated if 
 changes cannot be effectively visualized. Default is false.</td>\n```\n\n
 - [ ] **Apply / Chat** <!-- /improve --apply_suggestion=0 -->\n\n<details>
 <summary>Suggestion importance[1-10]: 6</summary>\n\n__\n\nWhy: \nRelevant 
 best practice - Fix grammatical errors and typos in user-facing documentation 
 to maintain professionalism and clarity.\n\n</details></details></td><td 
 align=center>Low\n\n</td></tr>\n<tr><td align=\"center\" colspan=\"2\">\n\n
 - [ ] More <!-- /improve --more_suggestions=true -->\n\n</td><td></td></tr>
 </tbody></table>","raw_data":{"code_suggestions":[{"relevant_file":
 "docs/docs/tools/describe.md\n","language":"markdown\n","relevant_best_practice":
 "Fix grammatical errors and typos in user-facing documentation to maintain 
 professionalism and clarity.\n","existing_code":"<td><b>enable_pr_diagram</b>
 </td>\n<td>If set to true, the tool will generate a horizontal Mermaid flowchart 
 summarizing the main pull request changes. This field remains empty if not applicable. 
 Default is false.</td>\n","suggestion_content":"The documentation parameter description 
 contains a grammatical issue. The sentence \"This field remains empty if not applicable\" 
 is unclear in context and should be clarified to better explain what happens when the 
 feature is not applicable.\n","improved_code":"<td><b>enable_pr_diagram</b></td>
 \n<td>If set to true, the tool will generate a horizontal Mermaid flowchart summarizing 
 the main pull request changes. No diagram will be generated if changes cannot be effectively 
 visualized. Default is false.</td>\n","one_sentence_summary":"Improve documentation clarity\n",
 "score":6,"score_why":"\nRelevant best practice - Fix grammatical errors and typos in 
 user-facing documentation to maintain professionalism and clarity.","label":"Learned best practice",
 "relevant_lines_start":128,"relevant_lines_end":129,"enable_apply":true}]}}
```

In case user has failed authentication, due to not enabling the endpoint in the helm chart:

```toml
HTTP/1.1 400 Bad Request
date: Tue, 03 Jun 2025 09:40:21 GMT
server: uvicorn
content-length: 3486
content-type: application/json

{"detail":{"error":"QM Pull Request endpoint is not enabled"}}
```

### Diff Endpoint

Given the following “/improve” request’s payload:

[improve_example_short.json](https://codium.ai/images/pr_agent/improve_example_short.json)

Received the following response:

```toml
{"response_str":"## PR Code Suggestions ✨\n\n<table><thead><tr><td><strong>Category</strong></td><td align=left><strong>Suggestion                                                                                                                                    
</strong></td><td align=center><strong>Impact</strong></td></tr><tbody><tr><td rowspan=1>Possible issue</td>\n<td>\n\n\n\n<details>
<summary>Fix invalid repository URL</summary>\n\n___\n\n\n**The <code>base_branch</code> is set to <code>None</code> but then used 
in the <code>repo_url</code> string <br>interpolation, which will cause a runtime error. Also, the repository URL format <br>is incorrect 
as it includes the branch in the middle of the organization/repo <br>path.**\n\n[tests/e2e_tests/test_github_app.py [1]]
(file://tests/e2e_tests/test_github_app.py#L1-1)\n\ndiff\\n-base_branch = None\\n+base_branch = \\"main\\"  # or any base branch you want\\n 
new_branch = f\\"github_app_e2e_test-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-where-am-I\\"\\n-repo_url = 
f'Codium-ai/{base_branch}/pr-agent-tests'\\n+repo_url = 'Codium-ai/pr-agent-tests'\\n\n<details><summary>Suggestion importance[1-10]: 9</summary>
\n\n__\n\nWhy: The suggestion correctly identifies a critical runtime bug where base_branch = None is used in string interpolation, 
which would produce an invalid repository URL Codium-ai/None/pr-agent-tests. This would cause the test to fail at runtime.\n\n\n</details></details>
</td><td align=center>High\n\n</td></tr></tbody></table>",

"raw_data":{"code_suggestions":[{"relevant_file":"tests/e2e_tests/test_github_app.py\n",
"language":"python\n","existing_code":"base_branch = None\nnew_branch = f\"github_app_e2e_test-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}
-where-am-I\"\nrepo_url = f'Codium-ai/{base_branch}/pr-agent-tests'\n","suggestion_content":"The base_branch is set to None but then used in the 
repo_url string interpolation, which will cause a runtime error. Also, the repository URL format is incorrect as it includes the branch in the middle 
of the organization/repo path.\n","improved_code":"base_branch = \"main\"  # or any base branch you want\nnew_branch = f\"github_app_e2e_test-
{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-where-am-I\"\nrepo_url = 'Codium-ai/pr-agent-tests'\n","one_sentence_summary":"Fix invalid repository 
URL\n","label":"possible issue","score":9,"score_why":"The suggestion correctly identifies a critical runtime bug where base_branch = None is used in 
string interpolation, which would produce an invalid repository URL Codium-ai/None/pr-agent-tests. This would cause the test to fail at runtime.\n",
"relevant_lines_start":1,"relevant_lines_end":1,"enable_apply":false}]}}
```

In case user has failed authentication:

```toml
HTTP/1.1 400 Bad Request
date: Tue, 03 Jun 2025 08:45:36 GMT
server: uvicorn
content-length: 43
content-type: application/json

{"detail":{"error":"Invalid API key"}}
```

# Appendix: Endpoints Comparison Table

| **Feature** | **Pull Request Endpoint** | **Diff Endpoint** |
| --- | --- | --- |
| **Input** | GitHub PR URL | File diffs / Unified diff |
| **Git Provider** | GitHub only | N/A |
| **Deployment** | On-premise/Single Tenant | All deployments |
| **Authentication** | Endpoint key only | Endpoint key or API key |

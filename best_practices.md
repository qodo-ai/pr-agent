
<b>Pattern 1: Use proper error handling with get_logger() instead of print statements for consistent logging throughout the codebase.
</b>

Example code before:
```
try:
    # Some code that might fail
    result = process_data()
except Exception as e:
    print(f"Failed to process data: {e}")
```

Example code after:
```
try:
    # Some code that might fail
    result = process_data()
except Exception as e:
    get_logger().error(f"Failed to process data", artifact={"error": str(e)})
```

<details><summary>Relevant past discussions: </summary>
- https://github.com/qodo-ai/pr-agent/pull/1529#discussion_r1958684550
- https://github.com/qodo-ai/pr-agent/pull/1529#discussion_r1958686068
- https://github.com/qodo-ai/pr-agent/pull/1529#discussion_r1964110734
- https://github.com/qodo-ai/pr-agent/pull/1529#discussion_r1964107962
</details>


<b>Pattern 2: Add defensive null/type checking for dictionary access to prevent potential runtime errors, especially when working with API responses or user inputs.
</b>

Example code before:
```
if suggestion.get('score') >= threshold and suggestion.get('improved_code'):
    process_suggestion(suggestion)
```

Example code after:
```
if suggestion.get('score') is not None and suggestion.get('improved_code') and int(suggestion['score']) >= threshold:
    process_suggestion(suggestion)
```

<details><summary>Relevant past discussions: </summary>
- https://github.com/qodo-ai/pr-agent/pull/1391#discussion_r1879875496
- https://github.com/qodo-ai/pr-agent/pull/1290#discussion_r1798939921
- https://github.com/qodo-ai/pr-agent/pull/1391#discussion_r1879875489
</details>


<b>Pattern 3: Add descriptive comments for complex logic or non-obvious code to improve maintainability and help future developers understand the purpose of the code.
</b>

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

<details><summary>Relevant past discussions: </summary>
- https://github.com/qodo-ai/pr-agent/pull/1262#discussion_r1782097205
- https://github.com/qodo-ai/pr-agent/pull/1583#discussion_r1971790979
</details>


<b>Pattern 4: Wrap API calls and external service interactions with proper try-except blocks and add specific error handling for different failure scenarios.
</b>

Example code before:
```
data_above_threshold = {'code_suggestions': []}
for suggestion in data['code_suggestions']:
    if int(suggestion.get('score', 0)) >= threshold:
        data_above_threshold['code_suggestions'].append(suggestion)
self.push_inline_code_suggestions(data_above_threshold)
```

Example code after:
```
data_above_threshold = {'code_suggestions': []}
try:
    for suggestion in data['code_suggestions']:
        if int(suggestion.get('score', 0)) >= threshold:
            data_above_threshold['code_suggestions'].append(suggestion)
    if data_above_threshold['code_suggestions']:
        self.push_inline_code_suggestions(data_above_threshold)
except Exception as e:
    get_logger().error(f"Failed to publish suggestions, error: {e}")
```

<details><summary>Relevant past discussions: </summary>
- https://github.com/qodo-ai/pr-agent/pull/1391#discussion_r1879870807
- https://github.com/qodo-ai/pr-agent/pull/1263#discussion_r1782129216
</details>


<b>Pattern 5: Use consistent formatting and capitalization in documentation, especially in field descriptions and configuration comments, to improve readability.
</b>

Example code before:
```
class ConfigFields(BaseModel):
    field_one: str = Field(description="the first field that does something")
    field_two: str = Field(description="The second field for another purpose")
```

Example code after:
```
class ConfigFields(BaseModel):
    field_one: str = Field(description="The first field that does something")
    field_two: str = Field(description="The second field for another purpose")
```

<details><summary>Relevant past discussions: </summary>
- https://github.com/qodo-ai/pr-agent/pull/1262#discussion_r1782097204
- https://github.com/qodo-ai/pr-agent/pull/1543#discussion_r1958093666
</details>


<b>Pattern 6: Fix typos and grammatical errors in documentation, comments, and user-facing messages to maintain professionalism and clarity.
</b>

Example code before:
```
# Create a webhook in GitLab. Set the URL to http[s]://<PR_AGENT_HOSTNAME>/webhook, the secret token to the generated secret from step 2, andenable the triggers.
```

Example code after:
```
# Create a webhook in GitLab. Set the URL to http[s]://<PR_AGENT_HOSTNAME>/webhook, the secret token to the generated secret from step 2, and enable the triggers.
```

<details><summary>Relevant past discussions: </summary>
- https://github.com/qodo-ai/pr-agent/pull/1307#discussion_r1817699788
- https://github.com/qodo-ai/pr-agent/pull/1307#discussion_r1817699656
- https://github.com/qodo-ai/pr-agent/pull/1517#discussion_r1942896094
</details>



<b>Pattern 1: Use proper error handling with try-except blocks and include detailed error logging with get_logger() instead of print statements, especially for network operations, file I/O, and API calls.</b>

Example code before:
```
try:
    response = api_call()
    # process response
except Exception as e:
    print(f"Failed to call API: {e}")
```

Example code after:
```
try:
    response = api_call()
    # process response
except Exception as e:
    get_logger().exception(f"Failed to call API", artifact={"error": str(e)})
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/pr-agent/pull/1634#discussion_r2007976915
- https://github.com/qodo-ai/pr-agent/pull/1529#discussion_r1958684550
- https://github.com/qodo-ai/pr-agent/pull/1529#discussion_r1958686068
- https://github.com/qodo-ai/pr-agent/pull/1529#discussion_r1964110734
</details>


___

<b>Pattern 2: Implement defensive programming by validating inputs and checking for null/None values before performing operations on them, especially when working with external data or API responses.</b>

Example code before:
```
model_is_from_o_series = re.match(r"^o[1-9](-mini|-preview)?$", model)
if ('gpt' in model.lower() or model_is_from_o_series) and openai_key_exists:
    return encoder_estimate
```

Example code after:
```
if model is None or not isinstance(model, str):
    get_logger().warning(f"Model is not a valid string: {type(model)}")
    return encoder_estimate

model_is_from_o_series = re.match(r"^o[1-9](-mini|-preview)?$", model)
if ('gpt' in model.lower() or model_is_from_o_series) and openai_key_exists:
    return encoder_estimate
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/pr-agent/pull/1644#discussion_r2032621065
- https://github.com/qodo-ai/pr-agent/pull/1290#discussion_r1798939921
- https://github.com/qodo-ai/pr-agent/pull/1391#discussion_r1879875496
</details>


___

<b>Pattern 3: Move specific imports to where they are actually used rather than at the top of the file, especially for rarely used or heavy dependencies, to improve module load time and reduce unnecessary imports.</b>

Example code before:
```
import os
from azure.identity import ClientSecretCredential
import litellm
import openai

# Much later in the code
if get_settings().get("AZURE_AD.CLIENT_ID", None):
    # Use ClientSecretCredential here
```

Example code after:
```
import os
import litellm
import openai

# Later in the code
if get_settings().get("AZURE_AD.CLIENT_ID", None):
    from azure.identity import ClientSecretCredential
    # Use ClientSecretCredential here
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/pr-agent/pull/1698#discussion_r2046221654
</details>


___

<b>Pattern 4: Refactor complex code blocks into separate methods or functions with clear names to improve readability, maintainability, and testability, especially when the code block exceeds 10-15 lines.</b>

Example code before:
```
# Inside a method with 20+ lines of code
if int(get_settings().pr_code_suggestions.dual_publishing_score_threshold) > 0:
    data_above_threshold = {'code_suggestions': []}
    try:
        for suggestion in data['code_suggestions']:
            if int(suggestion.get('score', 0)) >= int(get_settings().pr_code_suggestions.dual_publishing_score_threshold) \
                    and suggestion.get('improved_code'):
                data_above_threshold['code_suggestions'].append(suggestion)
                # More code here...
        if data_above_threshold['code_suggestions']:
            self.push_inline_code_suggestions(data_above_threshold)
    except Exception as e:
        get_logger().error(f"Failed to publish dual publishing suggestions, error: {e}")
```

Example code after:
```
# Main method
if int(get_settings().pr_code_suggestions.dual_publishing_score_threshold) > 0:
    await self.dual_publishing(data)

# Separate method
async def dual_publishing(self, data):
    data_above_threshold = {'code_suggestions': []}
    try:
        for suggestion in data['code_suggestions']:
            if int(suggestion.get('score', 0)) >= int(get_settings().pr_code_suggestions.dual_publishing_score_threshold) \
                    and suggestion.get('improved_code'):
                data_above_threshold['code_suggestions'].append(suggestion)
                # More code here...
        if data_above_threshold['code_suggestions']:
            await self.push_inline_code_suggestions(data_above_threshold)
    except Exception as e:
        get_logger().error(f"Failed to publish dual publishing suggestions, error: {e}")
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/pr-agent/pull/1605#discussion_r1980783780
- https://github.com/qodo-ai/pr-agent/pull/1391#discussion_r1879870807
</details>


___

<b>Pattern 5: Add descriptive comments for complex logic, configuration options, or non-obvious code behavior to improve code maintainability and make it easier for other developers to understand the code.</b>

Example code before:
```
get_logger().info(json.dumps(data))

if not issue or not isinstance(issue, dict):
    continue
```

Example code after:
```
# Log the incoming webhook payload data for debugging purposes
get_logger().info(json.dumps(data))

# Skip empty issues or non-dictionary items to ensure valid data structure
if not issue or not isinstance(issue, dict):
    continue
```

<details><summary>Examples for relevant past discussions:</summary>

- https://github.com/qodo-ai/pr-agent/pull/1583#discussion_r1971790979
- https://github.com/qodo-ai/pr-agent/pull/1262#discussion_r1782097204
</details>


___

<b>Pattern 6: Use consistent formatting and style throughout the codebase, including proper spacing, capitalization in comments and documentation, and consistent punctuation at the end of bullet points or sentences.</b>

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
- https://github.com/qodo-ai/pr-agent/pull/1613#discussion_r1986313421
- https://github.com/qodo-ai/pr-agent/pull/1613#discussion_r1986339874
</details>


___

import re
from typing import List

JIRA_KEY_PATTERN = re.compile(r"(?:https?://[^\s/]+/browse/)?([A-Z][A-Z0-9]+-\d{1,7})", re.IGNORECASE)


def find_jira_keys(text: str) -> List[str]:
    if not text:
        return []
    matches = JIRA_KEY_PATTERN.findall(text)
    keys = []
    for match in matches:
        key = match.upper()
        if key not in keys:
            keys.append(key)
    return keys

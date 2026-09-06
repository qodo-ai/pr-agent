"""A web-search tool the model can call while reviewing.

A review often turns on something outside the diff: whether an API is deprecated, what a CVE
covers, what a library's current version does. This tool gives the model one bounded way to ask,
through a search provider the operator configured.

The provider is chosen by the host. Both supported providers take a POST with a JSON body and an
API key, so a new one is a few lines below rather than a new dependency.
"""

from __future__ import annotations

from typing import Any, Dict, List

import requests

from pr_agent.algo.tool_registry import Tool, register_tool
from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger

WEB_SEARCH_TOOL_NAME = "web_search"
DEFAULT_RESULT_COUNT = 3
MAX_RESULT_COUNT = 10
DEFAULT_TIMEOUT_SECONDS = 10
MAX_SNIPPET_CHARS = 500

_PROVIDERS = {
    "exa": {
        "url": "https://api.exa.ai/search",
        "auth_header": "x-api-key",
        "body": lambda query, count: {"query": query, "numResults": count, "contents": {"text": True}},
        "results_key": "results",
        "fields": ("title", "url", "text"),
    },
    "tavily": {
        "url": "https://api.tavily.com/search",
        "auth_header": "Authorization",
        "auth_prefix": "Bearer ",
        "body": lambda query, count: {"query": query, "max_results": count},
        "results_key": "results",
        "fields": ("title", "url", "content"),
    },
}


def get_web_search_settings() -> Dict[str, Any]:
    """The configured provider and key, or an empty mapping when search is not set up."""
    settings = get_settings()
    provider = str(settings.get("web_search.provider", "") or "").strip().lower()
    api_key = str(settings.get("web_search.api_key", "") or "").strip()
    if not provider or not api_key:
        return {}
    if provider not in _PROVIDERS:
        get_logger().warning(
            f"web_search.provider {provider!r} is not supported; "
            f"choose one of {', '.join(sorted(_PROVIDERS))}")
        return {}
    return {"provider": provider, "api_key": api_key}


def _result_count() -> int:
    value = get_settings().get("web_search.result_count", DEFAULT_RESULT_COUNT)
    try:
        count = int(value)
    except (TypeError, ValueError):
        get_logger().warning(f"web_search.result_count is not a number ({value!r}); using {DEFAULT_RESULT_COUNT}")
        return DEFAULT_RESULT_COUNT
    return max(1, min(MAX_RESULT_COUNT, count))


def _timeout() -> int:
    value = get_settings().get("web_search.timeout", DEFAULT_TIMEOUT_SECONDS)
    try:
        timeout = int(value)
    except (TypeError, ValueError):
        return DEFAULT_TIMEOUT_SECONDS
    return max(1, timeout)


def _format(results: List[dict], fields) -> str:
    title_key, url_key, text_key = fields
    lines = []
    for index, result in enumerate(results, start=1):
        if not isinstance(result, dict):
            continue
        title = str(result.get(title_key) or "").strip() or "(no title)"
        url = str(result.get(url_key) or "").strip()
        snippet = " ".join(str(result.get(text_key) or "").split())[:MAX_SNIPPET_CHARS]
        lines.append(f"{index}. {title}\n   {url}\n   {snippet}".rstrip())
    return "\n".join(lines) if lines else "No results."


def search_the_web(query: str) -> str:
    """Search the web and return the top results as text the model can cite."""
    query = str(query or "").strip()
    if not query:
        return "Error: the query is empty."
    configured = get_web_search_settings()
    if not configured:
        return "Error: web search is not configured on this host."
    provider = _PROVIDERS[configured["provider"]]
    headers = {"Content-Type": "application/json",
               provider["auth_header"]: provider.get("auth_prefix", "") + configured["api_key"]}
    try:
        response = requests.post(provider["url"], json=provider["body"](query, _result_count()),
                                 headers=headers, timeout=_timeout(), allow_redirects=False)
        response.raise_for_status()
        payload = response.json()
    except Exception as e:
        # Log the type only: a search error can echo the URL, which carries the key.
        get_logger().warning(f"The web search failed: {type(e).__name__}")
        return f"Error: the web search failed ({type(e).__name__})."
    results = payload.get(provider["results_key"]) if isinstance(payload, dict) else None
    if not isinstance(results, list):
        return "No results."
    return _format(results, provider["fields"])


WEB_SEARCH_TOOL = Tool(
    name=WEB_SEARCH_TOOL_NAME,
    description=(
        "Search the web for current information the pull request does not contain, such as "
        "whether an API is deprecated, what a CVE covers, or how a library behaves. "
        "Returns the top results with their URLs."
    ),
    parameters={
        "type": "object",
        "properties": {"query": {"type": "string", "description": "What to search for"}},
        "required": ["query"],
    },
    handler=search_the_web,
)


def register_web_search_tool() -> bool:
    """Register the tool when a provider and key are configured; report whether it was."""
    if not get_web_search_settings():
        return False
    register_tool(WEB_SEARCH_TOOL)
    return True

"""Where the cache breakpoints go, and where per-request data goes.

Adapted from `anthropics/commerce-agents` (`commerce_common/prompt_assembly.py`).

A review is re-run on every push to a pull request, and each run spends several rounds
over the same tool array and the same static instructions. The stable prefix is therefore
the tool array and the static system text; everything that moves between runs — the PR
title, the head SHA, the file list — goes in a second system block behind the first one's
breakpoint. A rolling breakpoint on the newest message makes the rounds within one run
cache reads as well, so round *n* pays for the diffs it just fetched once rather than
*n* times.
"""

from __future__ import annotations

from typing import Any


def build_system_blocks(static_text: str, context: str) -> list[dict[str, Any]]:
    """The system prompt: the static text carrying the cache breakpoint, then the
    per-request context behind it. Nothing per request goes in the first block; a byte's
    change there would re-read the tool array and the static text on every call."""
    blocks: list[dict[str, Any]] = [
        {"type": "text", "text": static_text, "cache_control": {"type": "ephemeral"}}
    ]
    if context:
        blocks.append({"type": "text", "text": context})
    return blocks


def with_tool_cache_control(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """A breakpoint on the last tool, which ends the request's stable prefix."""
    if not tools:
        return tools
    tools = [dict(tool) for tool in tools]
    tools[-1]["cache_control"] = {"type": "ephemeral"}
    return tools


def build_request_messages(
    messages: list[dict[str, Any]],
    *,
    rolling_breakpoint: bool = True,
) -> list[dict[str, Any]]:
    """The outgoing request's messages: a request-shaped copy of ``messages`` with the
    rolling cache breakpoint on the newest content block.

    Two cases skip the marker. A bare first call (one message) would write an entry a
    one-shot run never reads, and the next call marks a later block whose span carries
    the first message anyway. And the caller passes ``rolling_breakpoint=False`` on
    rounds whose ``tool_choice`` is not ``auto``, because ``tool_choice`` keys the
    messages span: an entry written under a forced round is unreadable by the auto rounds
    that follow.

    Applied per call, to the outgoing request only: the returned list shallow-copies the
    touched message and blocks, strips the marker any earlier call placed, and never
    mutates the caller's stored history. Consecutive user messages are merged, because a
    round of tool results followed by a nudge would otherwise go out as two user turns.
    String content is lifted into a one-block list because ``cache_control`` lives on
    content blocks.
    """
    if not messages:
        return []

    def without_marker(message: dict[str, Any]) -> dict[str, Any]:
        content = message.get("content")
        if not isinstance(content, list) or not any(
            isinstance(block, dict) and "cache_control" in block for block in content
        ):
            return message
        return message | {
            "content": [
                {k: v for k, v in block.items() if k != "cache_control"}
                if isinstance(block, dict)
                else block
                for block in content
            ]
        }

    def blocks(raw: Any) -> list[Any]:
        return [{"type": "text", "text": raw}] if isinstance(raw, str) else list(raw or [])

    request: list[dict[str, Any]] = []
    for message in messages:
        message = without_marker(message)
        if request and message.get("role") == "user" and request[-1].get("role") == "user":
            request[-1] = request[-1] | {
                "content": blocks(request[-1].get("content")) + blocks(message.get("content"))
            }
        else:
            request.append(message)
    if not rolling_breakpoint or len(request) < 2:
        return request
    content = blocks(request[-1].get("content"))
    if content and isinstance(content[-1], dict):
        content[-1] = {**content[-1], "cache_control": {"type": "ephemeral"}}
        request[-1] = request[-1] | {"content": content}
    return request


def build_openai_instructions(static_text: str, context: str) -> list[dict[str, Any]]:
    """The same prefix, as Responses API input items.

    Two ``developer`` items rather than two system blocks, and no cache marker: the
    Responses client leaves caching in implicit mode, where the breakpoint advances on its
    own. What the ordering still buys is the same thing it buys on Anthropic — a prefix
    that does not move between two reviews of the same repository, with everything that
    does move behind it. Reversing these two items would re-read the static text and the
    tool array on every call, on either API.
    """
    items: list[dict[str, Any]] = [
        {"role": "developer", "content": [{"type": "input_text", "text": static_text}]}
    ]
    if context:
        items.append(
            {"role": "developer", "content": [{"type": "input_text", "text": context}]}
        )
    return items

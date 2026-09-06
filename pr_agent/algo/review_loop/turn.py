"""The parts of a turn loop that do not depend on which model API is underneath:
reading a field off a block whatever shape it arrived in, accounting for tokens,
compacting a long conversation, and never leaving the stored conversation in a shape the
API rejects.

Adapted from `anthropics/commerce-agents` (`commerce_common/turn.py`), minus the
streaming machinery: a PR review has no UI to stream to, so the loop calls the API once
per round and runs that round's tool calls concurrently instead.

Where a helper has to know how a conversation is shaped — where the results live, which
calls are still open — it asks the `ModelClient`, which is the one place that knows. That
keeps compaction and conversation repair identical on both APIs while the item shapes
they walk are not.

The block accessors accept either an SDK response object or the plain dicts a test
builds, so a loop can be exercised without a network client.
"""

from __future__ import annotations

import json
import time
from typing import Any

from pr_agent.algo.review_loop.execution import ToolOutcome
from pr_agent.log import get_logger

CLEARED_RESULT = "[result cleared from an earlier round; call the tool again if it is needed]"
INTERRUPTED_RESULT_TEXT = (
    "The review was interrupted before this call returned; call it again if it is still needed."
)


def block_field(block: Any, name: str, default: Any = None) -> Any:
    """One field of a content block, whether it arrived as a dict or an SDK object.

    One accessor for both shapes on purpose: ``getattr(block, "input", None) or
    block.get("input")`` reads a call with ``{}`` input as missing, because an empty
    dict is falsy, and falls through to the wrong branch.
    """
    if isinstance(block, dict):
        return block.get(name, default)
    value = getattr(block, name, default)
    return default if value is None else value


def block_dict(block: Any) -> dict[str, Any]:
    """A content block as a plain dict, ready to store in the conversation."""
    if isinstance(block, dict):
        return dict(block)
    if hasattr(block, "model_dump"):
        # ``citations`` is excluded because the API rejects it on the way back in.
        return dict(block.model_dump(exclude_none=True, exclude={"citations"}))
    return {"type": block_field(block, "type", "")}


def usage_totals() -> dict[str, int]:
    """The four counters every client normalizes to, in Anthropic's semantics:
    ``input_tokens`` excludes what was read from and written to the cache."""
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_input_tokens": 0,
        "cache_creation_input_tokens": 0,
    }


def accumulate_usage(totals: dict[str, int], usage: dict[str, int]) -> None:
    for key in usage_totals():
        totals[key] += usage.get(key, 0)


def prompt_tokens(usage: dict[str, int]) -> int:
    """The size of the prompt a call was given, as the model counted it: fresh input plus
    what was read from and written to the cache."""
    return sum(count for key, count in usage.items() if key != "output_tokens")


def elapsed_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def log_model_call(response: Any, started: float, **ids: Any) -> None:
    """The record every model call writes: the ids the caller passes, the model, the stop
    reason, the four usage counters, and the time taken. The cache counters are the point
    of the ordering in `prompt_assembly`: a run whose ``cache_read`` stays at 0 across
    rounds has lost its prefix, and this line is where that shows."""
    usage = response.usage
    tags = " ".join(f"{key}={value}" for key, value in ids.items())
    get_logger().info(
        f"review model call {tags} model={response.model} stop={response.stop_reason} "
        f"input={usage['input_tokens']} cache_read={usage['cache_read_input_tokens']} "
        f"cache_write={usage['cache_creation_input_tokens']} output={usage['output_tokens']} "
        f"elapsed_ms={elapsed_ms(started)}"
    )


def compact_history(
    client: Any, messages: list[dict[str, Any]], last_prompt_tokens: int, max_tokens: int
) -> int:
    """After a round whose call was given ``max_tokens`` or more, replace the oldest tool
    results with ``CLEARED_RESULT`` until the conversation is half its size, and return
    how many were cleared; ``0`` for ``max_tokens`` turns this off.

    A review's tool results are file diffs and file bodies, which is exactly the content
    a long run can afford to drop: the findings it produced from them are in the
    assistant text, which is never cleared. ``client.result_slots`` says where the results
    live, so this reads the same on a Messages ``tool_result`` block and a Responses
    ``function_call_output`` item.
    """
    if not max_tokens or last_prompt_tokens < max_tokens:
        return 0
    size = len(json.dumps(messages, default=str))
    target = size // 2
    cleared = 0
    for container, key in client.result_slots(messages):
        if size <= target:
            break
        if len(container[key]) > len(CLEARED_RESULT):
            size -= len(container[key]) - len(CLEARED_RESULT)
            container[key] = CLEARED_RESULT
            cleared += 1
    get_logger().info(
        f"review history compacted prompt_tokens={last_prompt_tokens} results_cleared={cleared}"
    )
    return cleared


def close_open_tool_calls(
    client: Any, messages: list[dict[str, Any]], settled: dict[str, ToolOutcome] | None = None
) -> int:
    """If the conversation ends on tool calls with no results after them — the loop raised
    mid-round, or a budget cut it short — append one result per call, so the stored
    conversation stays valid for the next request: the call's real outcome when ``settled``
    has it, else an error naming the interruption. Returns how many it appended."""
    ids = client.open_tool_calls(messages)
    if not ids:
        return 0
    settled = settled or {}
    client.append_tool_results(
        messages,
        [
            (
                call_id,
                settled.get(call_id) or ToolOutcome.error(INTERRUPTED_RESULT_TEXT),
            )
            for call_id in ids
        ],
    )
    return len(ids)

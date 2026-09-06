from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any

from pr_agent.algo.review_loop.execution import ToolExecutor, ToolOutcome
from pr_agent.algo.review_loop.model_client import (
    AUTO,
    NO_TOOLS,
    ModelClient,
    ModelResponse,
)
from pr_agent.algo.review_loop.turn import (
    accumulate_usage,
    close_open_tool_calls,
    compact_history,
    elapsed_ms,
    log_model_call,
    prompt_tokens,
    usage_totals,
)
from pr_agent.log import get_logger


@dataclass
class LoopResult:
    """What one bounded conversation produced."""

    text: str
    stop_reason: str | None = None
    rounds: int = 0
    tool_calls: int = 0
    cleared_results: int = 0
    elapsed_ms: int = 0
    usage: dict[str, int] = field(default_factory=usage_totals)

    @property
    def cache_read_tokens(self) -> int:
        return self.usage.get("cache_read_input_tokens", 0)


async def run_turn_loop(
    *,
    client: ModelClient,
    executor: ToolExecutor,
    model: str,
    static_system: str,
    messages: list[dict[str, Any]],
    context: str = "",
    tools: list[dict[str, Any]] | None = None,
    max_tokens: int = 16000,
    max_tool_iterations: int = 20,
    max_tool_calls: int = 120,
    forced_first_tool: str | None = None,
    effort: str | None = None,
    rolling_cache: bool = True,
    compact_above_tokens: int = 0,
    usage: dict[str, int] | None = None,
    cache_key: str = "",
    label: str = "review",
) -> LoopResult:
    """Run one bounded conversation to a final text answer.

    ``messages`` is extended in place with the run's assistant turns and tool results, so
    a caller that wants the transcript keeps the list it passed. Its items are in whatever
    shape ``client`` stores — content-block messages on Anthropic, flat input items on
    Responses — and nothing outside `model_client` reads them. The loop always ends in
    text: the round after the last tool round goes out with tools disabled.

    ``forced_first_tool`` pins the opening round to one read, so the run starts from a tool
    result rather than from the model's guess about the change. Pass ``None`` for a model
    that rejects a forced tool choice; the prompt asks for that read anyway.
    """
    started = time.monotonic()
    tools = list(tools if tools is not None else executor.tool_definitions())
    totals = usage if usage is not None else usage_totals()
    result = LoopResult(text="", usage=totals)
    last_prompt = 0
    # A round that raises must not leave the conversation on a tool call with no result:
    # the next request would be rejected.
    settled: dict[str, ToolOutcome] = {}
    try:
        for round_index in range(max_tool_iterations + 1):
            force_text = round_index == max_tool_iterations or result.tool_calls >= max_tool_calls
            if force_text:
                tool_choice: Any = NO_TOOLS
            elif round_index == 0 and forced_first_tool:
                tool_choice = ("tool", forced_first_tool)
            else:
                tool_choice = AUTO

            # Compaction runs before the request it is meant to shrink, using what the
            # previous round's call reported. Running it after the loop instead would
            # only ever shrink a conversation nobody sends again.
            if round_index:
                result.cleared_results += compact_history(
                    client, messages, last_prompt, compact_above_tokens
                )

            call_started = time.monotonic()
            # The rolling cache marker is skipped on non-auto rounds: tool_choice keys the
            # cached span, so an entry written under a forced round is unreadable by the
            # auto rounds that follow. Clients that cache implicitly ignore the flag.
            response: ModelResponse = await client.create(
                model=model,
                static_system=static_system,
                context=context,
                history=messages,
                tools=tools,
                tool_choice=tool_choice,
                max_tokens=max_tokens,
                effort=effort,
                rolling_cache=rolling_cache and tool_choice == AUTO,
                cache_key=cache_key,
            )
            log_model_call(response, call_started, label=label, round=round_index)
            accumulate_usage(totals, response.usage)
            last_prompt = prompt_tokens(response.usage)
            result.rounds = round_index + 1
            result.stop_reason = response.stop_reason

            client.append_assistant(messages, response)
            # The final round's text is the answer. An earlier round's prose sits beside
            # tool calls ("let me look at the diff"), and carrying it forward would hand
            # the caller commentary in place of the answer the last round failed to write.
            result.text = response.text

            if not response.tool_calls or force_text:
                break

            result.tool_calls += len(response.tool_calls)
            outcomes = await asyncio.gather(
                *(executor.execute(call.name, call.arguments) for call in response.tool_calls)
            )
            settled = {call.id: outcome for call, outcome in zip(response.tool_calls, outcomes)}
            client.append_tool_results(
                messages, [(call.id, outcome) for call, outcome in zip(response.tool_calls, outcomes)]
            )
            settled = {}
    finally:
        close_open_tool_calls(client, messages, settled)

    result.elapsed_ms = elapsed_ms(started)
    get_logger().info(
        f"review loop done label={label} provider={client.provider} rounds={result.rounds} "
        f"tool_calls={result.tool_calls} stop={result.stop_reason} "
        f"cache_read={result.cache_read_tokens} elapsed_ms={result.elapsed_ms}"
    )
    return result

"""The seam between the review loop and a model API.

The loop in `runtime` needs six things from a provider: send a request, read the text,
read the tool calls, read the usage, put the assistant's turn into the conversation, and
put tool results into the conversation. Everything else in this package — the tools in
`pr_tools`, the delegate contract in `delegation`, the fence in `fencing`, the
orchestration in `review_agent` — is the agent's definition and does not change with the
runtime it runs on. That split is the design rule the package follows: the agent is
defined once, and a second API is a new caller, not a second copy.

So this module holds the whole of the provider-specific part, and the loop holds none of
it. Two clients implement it:

- ``AnthropicClient``  the Claude Messages API: content blocks, ``tool_use`` in the
  assistant turn, ``tool_result`` in a user turn, ``cache_control`` breakpoints.
- ``OpenAIResponsesClient``  the OpenAI Responses API: a flat ``input`` item list,
  ``function_call`` and ``function_call_output`` items, ``prompt_cache_breakpoint``
  markers under ``prompt_cache_options.mode = "explicit"``.

Three differences between them are not cosmetic, and each is handled here rather than
leaked into the loop:

*Reasoning items.* A Responses run with ``store=False`` returns ``reasoning`` items
carrying ``encrypted_content``, and OpenAI asks that they be passed back with the next
request. A tool loop that stores only the text and the calls throws that away every
round, so ``append_assistant`` stores every output item verbatim rather than the parts
the loop happens to read.

*Error results.* A Messages API ``tool_result`` carries ``is_error``; a Responses
``function_call_output`` has no such field. The OpenAI client prefixes the output text
instead, so a failing tool still reads as a failure rather than as a result.

*Token accounting.* Anthropic reports ``input_tokens`` with cache reads and writes
excluded; OpenAI's ``input_tokens`` includes them, and breaks them out under
``input_tokens_details``. Both are normalized to the Anthropic shape on the way out,
because ``turn.prompt_tokens`` sums the counters and would otherwise double-count every
cached token on OpenAI — which is to say the compaction threshold would fire early on
exactly the runs caching was meant to make cheap.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar, Iterator

from pr_agent.algo.review_loop.execution import ToolOutcome
from pr_agent.algo.review_loop.turn import block_dict, block_field, usage_totals
from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger

# How hard the model works per call. The two APIs spell it differently — Anthropic
# ``output_config.effort``, OpenAI ``reasoning.effort`` — but the levels line up, so one
# configuration value serves both. OpenAI also accepts ``none`` and ``minimal``.
EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")
OPENAI_EXTRA_EFFORT_LEVELS = ("none", "minimal")

# What the loop asks for, before a client renders it into that API's spelling.
AUTO = "auto"
NO_TOOLS = "none"

# Normalized stop reasons. The loop only ever distinguishes "the model ran out of output
# room" from everything else, so that is the only value worth agreeing on across APIs.
STOP_MAX_TOKENS = "max_tokens"

ERROR_RESULT_PREFIX = "TOOL ERROR: "


@dataclass(frozen=True)
class ToolCall:
    """One tool call, in the shape the executor takes, whichever API produced it."""

    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ModelResponse:
    """One model call's answer, normalized. ``items`` is what the client will store in
    the conversation, and is deliberately opaque to the loop: on Responses it carries the
    reasoning items the next request has to echo back."""

    text: str = ""
    stop_reason: str | None = None
    tool_calls: list[ToolCall] = field(default_factory=list)
    usage: dict[str, int] = field(default_factory=usage_totals)
    items: list[Any] = field(default_factory=list)
    model: str = ""


def _tool_choice_label(tool_choice: Any) -> str:
    """The tool_choice as one word, for the cache rule and the log line."""
    return tool_choice if isinstance(tool_choice, str) else "tool"


class ModelClient(ABC):
    """What `runtime` needs from a model API.

    A client is a thin translator and holds no review state: one is built per review and
    shared by the orchestrator and every pass, so the underlying HTTP pool is shared too.
    """

    provider: ClassVar[str] = ""

    def __init__(self, raw: Any) -> None:
        self.raw = raw

    # -- the call ----------------------------------------------------------------------

    @abstractmethod
    async def create(
        self,
        *,
        model: str,
        static_system: str,
        context: str,
        history: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_choice: Any,
        max_tokens: int,
        effort: str | None,
        rolling_cache: bool,
        cache_key: str = "",
    ) -> ModelResponse:
        """Send one request and return the normalized answer.

        ``tools`` are the definitions as `pr_tools` and `delegation` author them —
        ``name``/``description``/``input_schema`` — which each client renders into its own
        spelling. ``tool_choice`` is ``AUTO``, ``NO_TOOLS``, or ``("tool", name)``.
        """

    # -- the conversation --------------------------------------------------------------

    @abstractmethod
    def append_assistant(self, history: list[dict[str, Any]], response: ModelResponse) -> None:
        """Store the assistant's turn, whole. Nothing the API returned is dropped."""

    @abstractmethod
    def append_tool_results(
        self, history: list[dict[str, Any]], results: list[tuple[str, ToolOutcome]]
    ) -> None:
        """Store one round's results, in call order."""

    @abstractmethod
    def open_tool_calls(self, history: list[dict[str, Any]]) -> list[str]:
        """The ids of calls at the end of the conversation that have no result yet. A
        conversation left in that state is rejected by both APIs on the next request."""

    @abstractmethod
    def result_slots(self, history: list[dict[str, Any]]) -> Iterator[tuple[dict[str, Any], str]]:
        """Every stored tool result, oldest first, as the ``(container, key)`` whose value
        is the result text. Compaction rewrites those values in place and needs no other
        knowledge of the conversation's shape."""

    @abstractmethod
    async def aclose(self) -> None:
        """Release the underlying HTTP pool. A webhook server runs many reviews in one
        process, and each leaks a connection pool without this."""


# ---------------------------------------------------------------- Anthropic


class AnthropicClient(ModelClient):
    """The Claude Messages API.

    The cache breakpoints are the reason `prompt_assembly` exists: the static system text
    and the tool array are the stable prefix, the PR context sits behind that breakpoint,
    and a rolling breakpoint on the newest message makes the rounds within one run read
    from the cache as well.
    """

    provider = "anthropic"

    async def create(
        self,
        *,
        model: str,
        static_system: str,
        context: str,
        history: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_choice: Any,
        max_tokens: int,
        effort: str | None,
        rolling_cache: bool,
        cache_key: str = "",
    ) -> ModelResponse:
        from pr_agent.algo.review_loop.prompt_assembly import (
            build_request_messages,
            build_system_blocks,
            with_tool_cache_control,
        )

        request: dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "system": build_system_blocks(static_system, context),
            "tools": with_tool_cache_control(tools),
            "tool_choice": self._tool_choice(tool_choice),
            "messages": build_request_messages(history, rolling_breakpoint=rolling_cache),
            **self._effort_fields(effort),
        }
        return self._read(await self.raw.messages.create(**request), model)

    @staticmethod
    def _tool_choice(tool_choice: Any) -> dict[str, str]:
        if isinstance(tool_choice, tuple):
            return {"type": "tool", "name": tool_choice[1]}
        return {"type": tool_choice}

    @staticmethod
    def _effort_fields(effort: str | None) -> dict[str, Any]:
        """``output_config.effort``, or ``{}`` for the model's own default.

        `thinking.budget_tokens` is not the lever here: the current generation rejects it
        outright and thinks adaptively instead.
        """
        level = str(effort or "").strip().lower()
        if level not in EFFORT_LEVELS:
            if level:
                get_logger().warning(
                    f"agentic review: unknown effort '{effort}' ignored; levels are {EFFORT_LEVELS}"
                )
            return {}
        return {"output_config": {"effort": level}}

    @staticmethod
    def _read(response: Any, model: str) -> ModelResponse:
        content = list(block_field(response, "content", []) or [])
        usage = block_field(response, "usage")
        return ModelResponse(
            text="\n".join(
                str(block_field(b, "text", ""))
                for b in content
                if block_field(b, "type") == "text"
            ).strip(),
            stop_reason=block_field(response, "stop_reason"),
            tool_calls=[
                ToolCall(
                    id=str(block_field(b, "id", "")),
                    name=str(block_field(b, "name", "")),
                    arguments=dict(block_field(b, "input", {}) or {}),
                )
                for b in content
                if block_field(b, "type") == "tool_use"
            ],
            usage={
                key: (block_field(usage, key, 0) or 0) if usage is not None else 0
                for key in usage_totals()
            },
            items=[block_dict(b) for b in content],
            model=model,
        )

    def append_assistant(self, history: list[dict[str, Any]], response: ModelResponse) -> None:
        if response.items:
            history.append({"role": "assistant", "content": list(response.items)})

    def append_tool_results(
        self, history: list[dict[str, Any]], results: list[tuple[str, ToolOutcome]]
    ) -> None:
        history.append(
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": call_id,
                        "content": outcome.result_text,
                        "is_error": outcome.is_error,
                    }
                    for call_id, outcome in results
                ],
            }
        )

    def open_tool_calls(self, history: list[dict[str, Any]]) -> list[str]:
        if not history or history[-1].get("role") != "assistant":
            return []
        content = history[-1].get("content")
        if not isinstance(content, list):
            return []
        return [
            str(block_field(block, "id", ""))
            for block in content
            if block_field(block, "type") == "tool_use"
        ]

    def result_slots(self, history: list[dict[str, Any]]) -> Iterator[tuple[dict[str, Any], str]]:
        for message in history:
            content = message.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if (
                    isinstance(block, dict)
                    and block.get("type") == "tool_result"
                    and isinstance(block.get("content"), str)
                ):
                    yield block, "content"

    async def aclose(self) -> None:
        close = getattr(self.raw, "close", None)
        if close is not None:
            await close()


# ---------------------------------------------------------------- OpenAI Responses


class OpenAIResponsesClient(ModelClient):
    """The OpenAI Responses API.

    The conversation is a flat ``input`` item list rather than role-keyed messages with
    content blocks, and it is carried in full on every request: ``store`` is ``False``, so
    a review of a private repository leaves nothing server-side and ``previous_response_id``
    is not available to lean on.

    Caching is left in ``implicit`` mode, which is the one real departure from the
    Anthropic path. Explicit mode wants ``prompt_cache_breakpoint`` on a content block
    *inside an input message*, and after any tool round the newest items here are
    ``function_call_output`` and ``reasoning``, which are not messages and have no content
    block to mark. A manual breakpoint could therefore only ever land several items back,
    freezing the cached prefix behind the growing tail — while implicit mode advances the
    breakpoint to the end of the latest eligible message on its own. What does carry over
    is the *ordering* discipline, which is what makes either mode work: the static system
    text and the tool array first, everything that moves between reviews behind them.
    """

    provider = "openai"

    async def create(
        self,
        *,
        model: str,
        static_system: str,
        context: str,
        history: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_choice: Any,
        max_tokens: int,
        effort: str | None,
        rolling_cache: bool,
        cache_key: str = "",
    ) -> ModelResponse:
        from pr_agent.algo.review_loop.prompt_assembly import build_openai_instructions

        request: dict[str, Any] = {
            "model": model,
            "max_output_tokens": max_tokens,
            "input": build_openai_instructions(static_system, context) + list(history),
            "tools": self._tools(tools),
            "tool_choice": self._tool_choice(tool_choice),
            "store": False,
            # `prompt_cache_options` is newer than the pinned SDK, whose `create` rejects
            # keywords it does not type. `extra_body` is the SDK's own escape hatch and
            # puts the field on the wire unchanged; a server that does not know it ignores
            # it, which is the same as the implicit default this asks for.
            "extra_body": {"prompt_cache_options": {"mode": "implicit"}},
            **self._effort_fields(effort),
        }
        if cache_key:
            # Routing only: it helps requests with the same prefix reach the same cache,
            # and does not pin them to one. Keyed per repository, because that is the
            # granularity at which the static prefix is actually shared between reviews.
            request["prompt_cache_key"] = cache_key
        return self._read(await self.raw.responses.create(**request), model)

    @staticmethod
    def _tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """The definitions rendered as Responses function tools.

        ``strict`` is deliberately left off. It requires every property in ``required``
        and ``additionalProperties: false`` throughout, and the review tools have genuinely
        optional arguments — ``read_file``'s line range, ``run_review_pass``'s brief. The
        arguments are validated by pydantic in `execution.parse_argument` on arrival
        anyway, and a rejected argument comes back to the model as a named error.
        """
        return [
            {
                "type": "function",
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("input_schema", {"type": "object", "properties": {}}),
            }
            for tool in tools
        ]

    @staticmethod
    def _tool_choice(tool_choice: Any) -> Any:
        if isinstance(tool_choice, tuple):
            return {"type": "function", "name": tool_choice[1]}
        return tool_choice

    @staticmethod
    def _effort_fields(effort: str | None) -> dict[str, Any]:
        level = str(effort or "").strip().lower()
        if level not in EFFORT_LEVELS + OPENAI_EXTRA_EFFORT_LEVELS:
            if level:
                get_logger().warning(
                    f"agentic review: unknown effort '{effort}' ignored; levels are "
                    f"{EFFORT_LEVELS + OPENAI_EXTRA_EFFORT_LEVELS}"
                )
            return {}
        return {"reasoning": {"effort": level}}

    @classmethod
    def _read(cls, response: Any, model: str) -> ModelResponse:
        items = list(block_field(response, "output", []) or [])
        return ModelResponse(
            text=cls._text(items),
            stop_reason=cls._stop_reason(response),
            tool_calls=[cls._call(item) for item in items if block_field(item, "type") == "function_call"],
            usage=cls._usage(response),
            items=[block_dict(item) for item in items],
            model=model,
        )

    @staticmethod
    def _text(items: list[Any]) -> str:
        parts: list[str] = []
        for item in items:
            if block_field(item, "type") != "message":
                continue
            for block in block_field(item, "content", []) or []:
                if block_field(block, "type") == "output_text":
                    parts.append(str(block_field(block, "text", "")))
        return "\n".join(parts).strip()

    @staticmethod
    def _call(item: Any) -> ToolCall:
        """One ``function_call`` item. ``arguments`` arrives as a JSON *string*, and a
        model that emits something unparseable must reach the executor as a call with bad
        arguments — which answers with a named error — rather than killing the round."""
        raw = block_field(item, "arguments", "") or "{}"
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else dict(raw)
        except (TypeError, ValueError):
            parsed = {}
        return ToolCall(
            id=str(block_field(item, "call_id", "")),
            name=str(block_field(item, "name", "")),
            arguments=parsed if isinstance(parsed, dict) else {},
        )

    @staticmethod
    def _stop_reason(response: Any) -> str | None:
        """``status`` plus ``incomplete_details.reason``, folded into the one distinction
        the loop makes: did the model run out of output room?"""
        if block_field(response, "status") == "incomplete":
            details = block_field(response, "incomplete_details")
            reason = block_field(details, "reason", "") if details is not None else ""
            return STOP_MAX_TOKENS if reason == "max_output_tokens" else str(reason or "incomplete")
        return str(block_field(response, "status", "") or "") or None

    @staticmethod
    def _usage(response: Any) -> dict[str, int]:
        """The four counters, in Anthropic's semantics.

        OpenAI's ``input_tokens`` is the whole prompt, cached and written tokens included;
        Anthropic's excludes both and reports them separately. `turn.prompt_tokens` sums
        the counters, so the cached part is subtracted back out here — otherwise every
        cache hit would be counted twice and the compaction threshold would fire on the
        runs the cache had just made cheap.
        """
        usage = block_field(response, "usage")
        if usage is None:
            return usage_totals()
        details = block_field(usage, "input_tokens_details")
        cached = int(block_field(details, "cached_tokens", 0) or 0) if details is not None else 0
        written = int(block_field(details, "cache_write_tokens", 0) or 0) if details is not None else 0
        total_input = int(block_field(usage, "input_tokens", 0) or 0)
        return {
            "input_tokens": max(total_input - cached - written, 0),
            "output_tokens": int(block_field(usage, "output_tokens", 0) or 0),
            "cache_read_input_tokens": cached,
            "cache_creation_input_tokens": written,
        }

    def append_assistant(self, history: list[dict[str, Any]], response: ModelResponse) -> None:
        """Every output item, verbatim and in order.

        The reasoning items matter: with ``store=False`` they carry ``encrypted_content``,
        and OpenAI asks that they come back with the next request. Storing only the text
        and the calls would drop the model's reasoning at every tool round, which is every
        round this loop has.
        """
        history.extend(dict(item) for item in response.items)

    def append_tool_results(
        self, history: list[dict[str, Any]], results: list[tuple[str, ToolOutcome]]
    ) -> None:
        """One ``function_call_output`` per call.

        There is no ``is_error`` on this item, so a failure is marked in the text. Without
        it a tool that failed and a tool that succeeded are indistinguishable to the model,
        and `execution.execute` deliberately turns every failure into a readable result
        rather than an exception — the flag is the only thing that says which is which.
        """
        history.extend(
            {
                "type": "function_call_output",
                "call_id": call_id,
                "output": (ERROR_RESULT_PREFIX + outcome.result_text)
                if outcome.is_error
                else outcome.result_text,
            }
            for call_id, outcome in results
        )

    def open_tool_calls(self, history: list[dict[str, Any]]) -> list[str]:
        """Trailing ``function_call`` items with no ``function_call_output`` after them.

        Unlike the Messages API there is no assistant turn to look at: calls and results
        are siblings in one flat list, so the open ones are found by walking back from the
        end over the items this round appended.
        """
        answered: set[str] = set()
        pending: list[str] = []
        for item in reversed(history):
            kind = item.get("type")
            if kind == "function_call_output":
                answered.add(str(item.get("call_id", "")))
            elif kind == "function_call":
                call_id = str(item.get("call_id", ""))
                if call_id not in answered:
                    pending.append(call_id)
            elif kind == "reasoning":
                continue
            else:
                break
        return list(reversed(pending))

    def result_slots(self, history: list[dict[str, Any]]) -> Iterator[tuple[dict[str, Any], str]]:
        for item in history:
            if item.get("type") == "function_call_output" and isinstance(item.get("output"), str):
                yield item, "output"

    async def aclose(self) -> None:
        close = getattr(self.raw, "close", None)
        if close is not None:
            await close()


# ---------------------------------------------------------------- construction


PROVIDERS: dict[str, type[ModelClient]] = {
    AnthropicClient.provider: AnthropicClient,
    OpenAIResponsesClient.provider: OpenAIResponsesClient,
}

_KEY_SETTINGS = {
    "anthropic": ("anthropic.key", "ANTHROPIC_API_KEY"),
    "openai": ("openai.key", "OPENAI_API_KEY"),
}


def api_key(provider: str) -> str:
    """The provider's key, from the settings section or the environment."""
    setting, variable = _KEY_SETTINGS[provider]
    try:
        configured = get_settings().get(setting, "") or ""
    except Exception:  # settings may not carry the section at all
        configured = ""
    return str(configured or os.environ.get(variable, "")).strip()


def build_client(provider: str = "anthropic", timeout_s: float = 600.0) -> ModelClient:
    """The client for one review.

    The SDKs are imported here rather than at module scope so this package stays
    importable — and the rest of PR-Agent stays runnable — with neither installed.
    """
    provider = str(provider or "anthropic").strip().lower()
    if provider not in PROVIDERS:
        raise ValueError(
            f"'{provider}' is not a model provider for the agentic review; "
            f"the providers are {sorted(PROVIDERS)}."
        )
    key = api_key(provider)
    if not key:
        setting, variable = _KEY_SETTINGS[provider]
        raise ValueError(
            f"the agentic review is configured for {provider} and needs a key: set "
            f"{variable}, or {setting} in your configuration."
        )
    if provider == "anthropic":
        from anthropic import AsyncAnthropic

        return AnthropicClient(AsyncAnthropic(api_key=key, timeout=timeout_s))
    from openai import AsyncOpenAI

    return OpenAIResponsesClient(AsyncOpenAI(api_key=key, timeout=timeout_s))

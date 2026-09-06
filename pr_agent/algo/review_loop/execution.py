"""The executor frame the review tools extend.

Adapted from `anthropics/commerce-agents` (`commerce_common/execution.py`). The point of
the frame is that a tool result is built in exactly one place, so every runtime that
reviews a pull request reaches the same behavior through one ``execute``.

``execute`` never raises. A provider outage, a malformed argument, or a bug in a handler
becomes a tool result the model can read and route around; a review that dies because one
file could not be fetched is worse than a review that says so.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from pr_agent.algo.review_loop.fencing import MAX_FENCED_CHARS, Fence
from pr_agent.log import get_logger

Handler = Callable[[dict[str, Any]], Awaitable["ToolOutcome"]]
ArgumentT = TypeVar("ArgumentT", bound=BaseModel)


class ToolOutcome:
    """What one tool call returns to the model: the result text and whether the API
    should mark it as an error."""

    __slots__ = ("result_text", "is_error")

    def __init__(self, result_text: str, is_error: bool = False) -> None:
        self.result_text = result_text
        self.is_error = is_error

    @classmethod
    def error(cls, text: str) -> ToolOutcome:
        return cls(text, is_error=True)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"ToolOutcome(is_error={self.is_error}, result_text={self.result_text[:80]!r})"


class InvalidArguments(ValueError):
    """A tool argument failed its schema; ``execute`` answers by naming the fields."""

    def __init__(self, invalid: ValidationError) -> None:
        super().__init__(str(invalid))
        self.invalid = invalid


def parse_argument(model: type[ArgumentT], value: Any) -> ArgumentT:
    """Validate one model-supplied argument. Only a failure raised here is reported as
    bad arguments; a ``ValidationError`` from anywhere else in a handler is a failure
    like any other."""
    try:
        return model.model_validate(value)
    except ValidationError as invalid:
        raise InvalidArguments(invalid) from invalid


def invalid_arguments_text(name: str, invalid: ValidationError) -> str:
    issues = "; ".join(
        f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
        for error in invalid.errors()
    )
    return f"{name} arguments were invalid — {issues}. Adjust and call it again."


class ArgumentModel(BaseModel):
    """The base for a tool's argument model. ``extra="forbid"`` turns a hallucinated
    field into a named error the model can correct, rather than a silently ignored one."""

    model_config = {"extra": "forbid"}


class ToolExecutor:
    """One review's tools. A subclass supplies its fence, its handler table and its tool
    contracts; ``execute`` never raises."""

    fence: Fence
    unavailable_text: str = (
        "{name} is unavailable right now. Continue the review with what you already have, "
        "and say in your answer what you could not read."
    )

    def __init__(self, *, max_fenced_chars: int = MAX_FENCED_CHARS) -> None:
        self._max_fenced_chars = max_fenced_chars

    # -- subclass hooks -------------------------------------------------------------

    def handlers(self) -> dict[str, Handler]:
        """``{tool name: async (args) -> ToolOutcome}``."""
        raise NotImplementedError

    def tool_definitions(self) -> list[dict[str, Any]]:
        """The tool contracts as the Messages API takes them."""
        raise NotImplementedError

    def domain_error(self, error: Exception) -> ToolOutcome | None:
        """A subclass's own exception classes mapped to outcomes; None uses the ladder."""
        return None

    # -- helpers for handlers -------------------------------------------------------

    def _fenced(self, payload: Any) -> ToolOutcome:
        return ToolOutcome(self.fence.fence_payload(payload, self._max_fenced_chars))

    # -- dispatch -------------------------------------------------------------------

    async def execute(self, name: str, tool_input: dict[str, Any] | None) -> ToolOutcome:
        """Run one call. Never raises: every failure comes back as a readable result."""
        try:
            return await self.dispatch(name, dict(tool_input or {}))
        except InvalidArguments as invalid:
            return ToolOutcome.error(invalid_arguments_text(name, invalid.invalid))
        except Exception as error:  # a tool failure must not end the review
            if (outcome := self.domain_error(error)) is not None:
                return outcome
            get_logger().warning(f"review tool {name} failed and is reported as unavailable: {error}")
            return ToolOutcome.error(self.unavailable_text.format(name=name))

    async def dispatch(self, name: str, tool_input: dict[str, Any]) -> ToolOutcome:
        """:meth:`execute` without the failure ladder: what the handler raised propagates,
        so a caller prefetching a read can tell a failed tool from a result the tool
        wrote."""
        handler = self.handlers().get(name)
        if handler is None:
            return ToolOutcome.error(f"Unknown tool: {name}")
        return await handler(tool_input)

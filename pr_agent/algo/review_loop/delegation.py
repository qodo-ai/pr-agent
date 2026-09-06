"""Review passes as delegates: an isolated model call behind a tool.

Adapted from the delegate contract of `anthropics/commerce-agents`
(`commerce_common/delegation.py`). A delegate receives a brief and the PR handles, never
the orchestrator's conversation; it reads the same PR tools, and it returns one
schema-validated result. It cannot call another delegate, and it cannot publish.

Why a delegate rather than more rounds in one conversation: a security pass and a test
pass want different attention over the same diff, and running them in one context means
each is read against the other's notes. Separate contexts also mean the orchestrator's
window carries the findings, not the twenty file diffs each pass read to produce them.
"""

from __future__ import annotations

from typing import Any, List, Optional

from pydantic import BaseModel, Field

from pr_agent.algo.review_loop.execution import Handler, ToolOutcome, parse_argument
from pr_agent.algo.review_loop.fencing import MAX_FENCED_CHARS
from pr_agent.algo.review_loop.pr_tools import LIST_CHANGED_FILES, PRToolExecutor
from pr_agent.algo.review_loop.runtime import run_turn_loop

RUN_REVIEW_PASS = "run_review_pass"
SUBMIT_FINDINGS = "submit_findings"

# What a pass can be asked to look for. The key is the tool's enum value; the text is the
# brief the pass opens with, so adding an aspect here is the whole change.
REVIEW_ASPECTS: dict[str, str] = {
    "correctness": (
        "Logic errors introduced by this pull request: wrong conditions, off-by-one and "
        "boundary mistakes, unhandled None or empty values, mishandled errors and "
        "exceptions, resource leaks, incorrect concurrency or ordering, and changes that "
        "break an existing caller. Ground every finding in a concrete input or state that "
        "reaches it."
    ),
    "security": (
        "Security defects introduced by this pull request: injection of any kind, missing "
        "authentication or authorization on a new path, secrets or tokens written to code, "
        "logs or errors, unsafe deserialization, path traversal, SSRF, weak or misused "
        "crypto, and user-controlled input reaching a dangerous sink. Say what an attacker "
        "controls and what they get."
    ),
    "performance": (
        "Performance defects introduced by this pull request: work that grows worse than "
        "linearly with input, queries or network calls inside a loop, repeated work that "
        "could be done once, unbounded memory growth, and blocking calls on a hot or async "
        "path. Say roughly at what size it starts to matter."
    ),
    "tests": (
        "Test coverage of what this pull request changes: new or changed behavior with no "
        "test, edge cases and failure paths the tests skip, tests that assert nothing "
        "meaningful, and tests that would pass with the change reverted. Name the specific "
        "case that is missing."
    ),
    "maintainability": (
        "Maintainability defects introduced by this pull request: duplicated logic that "
        "will drift, a public interface that is easy to call incorrectly, dead or "
        "unreachable code, a comment or docstring that contradicts the code, and behavior "
        "that contradicts this repository's stated conventions. Only flag what a reader "
        "would get wrong, not style preference."
    ),
}

# The aspects a review dispatches when the configuration names none.
DEFAULT_ASPECTS = ("correctness", "security", "tests")


class ReviewFinding(BaseModel):
    """One reviewable problem, in the shape the classic `/review` output already carries,
    so the orchestrator can pass a finding through without translating it."""

    model_config = {"extra": "forbid"}

    relevant_file: str = Field(description="Full path of the file, exactly as the diff reports it.")
    issue_header: str = Field(
        max_length=60, description="One or two words naming the issue, e.g. 'Possible bug'."
    )
    issue_content: str = Field(
        max_length=1200,
        description="What is wrong, why it matters, and the specific input or state that "
        "triggers it. No line numbers in this field.",
    )
    start_line: int = Field(ge=1, description="First line of the issue in the file at head.")
    end_line: int = Field(ge=1, description="Last line of the issue in the file at head.")
    confidence: str = Field(
        default="high",
        pattern="^(high|medium|low)$",
        description="high only when the diff you read proves it; medium when it depends on "
        "code you could not see; low otherwise.",
    )


class ReviewPassResult(BaseModel):
    """What one pass returns: what it read, what it found, and what it could not settle."""

    model_config = {"extra": "forbid"}

    findings: List[ReviewFinding] = Field(default_factory=list)
    files_examined: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="What you could not check and why. Empty when the pass was complete.",
    )


def build_submit_findings_tool(max_findings: int) -> dict[str, Any]:
    return {
        "name": SUBMIT_FINDINGS,
        "description": (
            f"End this pass by submitting what you found — at most {max_findings} findings, "
            "highest severity first, and an empty list when the code is sound. This is the "
            "only way the pass returns; nothing you write outside it is read."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "findings": {
                    "type": "array",
                    "maxItems": max_findings,
                    "items": {
                        "type": "object",
                        "properties": {
                            "relevant_file": {"type": "string"},
                            "issue_header": {"type": "string", "maxLength": 60},
                            "issue_content": {"type": "string", "maxLength": 1200},
                            "start_line": {"type": "integer"},
                            "end_line": {"type": "integer"},
                            "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                        },
                        "required": [
                            "relevant_file",
                            "issue_header",
                            "issue_content",
                            "start_line",
                            "end_line",
                            "confidence",
                        ],
                    },
                },
                "files_examined": {"type": "array", "items": {"type": "string"}},
                "notes": {
                    "type": "string",
                    "maxLength": 1000,
                    "description": "What you could not check and why; omit when nothing was skipped.",
                },
            },
            "required": ["findings", "files_examined"],
        },
    }


def build_review_pass_tool_definition(aspects: list[str]) -> dict[str, Any]:
    """The orchestrator-facing tool. The description confines it to a whole aspect, so the
    orchestrator dispatches passes rather than using it as a second opinion on one line it
    could read itself."""
    return {
        "name": RUN_REVIEW_PASS,
        "description": (
            "Run one reviewer over the whole pull request for one aspect, in its own "
            "context, and get back its findings. Each aspect is worth exactly one pass: "
            "dispatch the ones this change calls for, in parallel, before you read "
            "anything yourself. It is not a second opinion on a single line — read that "
            f"line with {LIST_CHANGED_FILES} and the file tools instead."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "aspect": {
                    "type": "string",
                    "enum": aspects,
                    "description": "Which reviewer to run.",
                },
                "brief": {
                    "type": "string",
                    "maxLength": 600,
                    "description": "What about this pull request in particular that reviewer "
                    "should weigh — the risky area, the subsystem it touches. Optional; the "
                    "aspect already carries its own instructions.",
                },
            },
            "required": ["aspect"],
        },
    }


class ReviewPassExecutor(PRToolExecutor):
    """A pass's tools: the PR reads, plus the submission that ends it. ``submitted`` is
    the validated result once the pass has called it; a second call is refused, so a pass
    cannot keep amending its answer."""

    def __init__(
        self,
        git_provider: Any,
        *,
        max_findings: int = 6,
        max_fenced_chars: int = MAX_FENCED_CHARS,
    ) -> None:
        super().__init__(git_provider, max_fenced_chars=max_fenced_chars)
        self._max_findings = max_findings
        self.submitted: ReviewPassResult | None = None

    def handlers(self) -> dict[str, Handler]:
        return {**super().handlers(), SUBMIT_FINDINGS: self._submit}

    def tool_definitions(self) -> list[dict[str, Any]]:
        return [*super().tool_definitions(), build_submit_findings_tool(self._max_findings)]

    async def _submit(self, args: dict[str, Any]) -> ToolOutcome:
        if self.submitted is not None:
            return ToolOutcome.error(
                "This pass has already submitted; its findings are recorded. Stop here."
            )
        result = parse_argument(ReviewPassResult, args)
        result.findings = result.findings[: self._max_findings]
        self.submitted = result
        return ToolOutcome(f"Submitted {len(result.findings)} finding(s). The pass is complete.")


async def run_review_pass(
    *,
    client: Any,
    git_provider: Any,
    aspect: str,
    brief: str,
    system_prompt: str,
    context: str = "",
    model: str,
    max_findings: int = 6,
    max_tokens: int = 16000,
    max_tool_iterations: int = 12,
    max_tool_calls: int = 60,
    max_fenced_chars: int = MAX_FENCED_CHARS,
    effort: str | None = None,
    force_first_read: bool = True,
    usage: dict[str, int] | None = None,
    cache_key: str = "",
    compact_above_tokens: int = 0,
) -> ReviewPassResult:
    """Run one pass to a validated result.

    Raises ``ValueError`` when the pass never submitted; the caller turns that into a tool
    error the orchestrator reads, exactly as a delegate failure is handled in
    commerce-agents.
    """
    if aspect not in REVIEW_ASPECTS:
        raise ValueError(f"'{aspect}' is not a review aspect; the aspects are {list(REVIEW_ASPECTS)}.")
    executor = ReviewPassExecutor(
        git_provider, max_findings=max_findings, max_fenced_chars=max_fenced_chars
    )
    opening = f"Review this pull request for: {aspect}.\n\n{REVIEW_ASPECTS[aspect]}"
    if brief:
        opening += f"\n\nWhat the orchestrator wants weighed in particular:\n{brief.strip()[:600]}"
    opening += (
        f"\n\nStart with {LIST_CHANGED_FILES}, read the diffs that matter for this aspect, "
        f"and end by calling {SUBMIT_FINDINGS}."
    )
    messages: list[dict[str, Any]] = [{"role": "user", "content": opening}]
    result = await run_turn_loop(
        client=client,
        executor=executor,
        model=model,
        static_system=system_prompt,
        messages=messages,
        context=context,
        max_tokens=max_tokens,
        max_tool_iterations=max_tool_iterations,
        max_tool_calls=max_tool_calls,
        forced_first_tool=LIST_CHANGED_FILES if force_first_read else None,
        effort=effort,
        usage=usage,
        cache_key=cache_key,
        compact_above_tokens=compact_above_tokens,
        label=f"pass:{aspect}",
    )
    if executor.submitted is None:
        raise ValueError(
            f"the {aspect} pass ran {result.rounds} round(s) and {result.tool_calls} tool call(s) "
            f"without calling {SUBMIT_FINDINGS}, so it has no findings. Dispatch it again with a "
            "narrower brief, or review this aspect yourself."
        )
    return executor.submitted

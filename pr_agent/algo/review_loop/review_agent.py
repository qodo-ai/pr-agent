"""The review orchestrator.

The agent is defined once — prompts in `settings/pr_agentic_reviewer_prompts.toml`, tool
contracts in `pr_tools`, subagents in `delegation` — and this module runs that definition
against whichever model API `pr_agentic_reviewer.provider` selects. Keeping the definition
out of the runtime is the point, and the Responses API is the case that proves it: adding
it added a client in `model_client` and changed nothing here but which one is built.

The orchestrator's own loop is short by design. It dispatches a pass per aspect, then
spends its remaining rounds verifying what came back against the code, and answers with
the review YAML the classic `/review` publisher already renders.
"""

from __future__ import annotations

from typing import Any, Optional

from jinja2 import Environment, StrictUndefined
from pydantic import Field

from pr_agent.algo.review_loop.delegation import (
    DEFAULT_ASPECTS,
    REVIEW_ASPECTS,
    RUN_REVIEW_PASS,
    ReviewPassResult,
    build_review_pass_tool_definition,
    run_review_pass,
)
from pr_agent.algo.review_loop.execution import ArgumentModel, Handler, ToolOutcome, parse_argument
from pr_agent.algo.review_loop.fencing import MAX_FENCED_CHARS, PR_CONTENT_FENCE
from pr_agent.algo.review_loop.model_client import build_client
from pr_agent.algo.review_loop.pr_tools import LIST_CHANGED_FILES, PRToolExecutor
from pr_agent.algo.review_loop.runtime import LoopResult, run_turn_loop
from pr_agent.algo.review_loop.turn import usage_totals
from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger


class _ReviewPassArgs(ArgumentModel):
    aspect: str
    brief: Optional[str] = Field(default=None, max_length=600)


def render(template_text: str, variables: dict[str, Any]) -> str:
    return Environment(undefined=StrictUndefined).from_string(template_text).render(variables)


# The model a provider falls back to when none is configured. `configuration.toml` sets
# one explicitly, so this only catches a half-written override that names a provider and
# leaves `model` empty — where the wrong default is a confusing 404 rather than a failure.
DEFAULT_MODELS = {"anthropic": "claude-opus-5", "openai": "gpt-5.6"}


def resolve_aspects(configured: Any) -> list[str]:
    """The aspects to offer, filtered to the ones this module defines. An unknown name in
    config is dropped with a warning rather than reaching the tool's enum, where it would
    become a pass with no findings."""
    names = [str(name).strip().lower() for name in (configured or DEFAULT_ASPECTS) if str(name).strip()]
    known = [name for name in names if name in REVIEW_ASPECTS]
    if unknown := [name for name in names if name not in REVIEW_ASPECTS]:
        get_logger().warning(
            f"agentic review: unknown aspect(s) {unknown} dropped; known aspects are "
            f"{list(REVIEW_ASPECTS)}"
        )
    return known or list(DEFAULT_ASPECTS)


class ReviewAgentExecutor(PRToolExecutor):
    """The orchestrator's tools: the PR reads, plus the delegate that runs one pass.

    A pass that fails to submit comes back as a tool error naming what it did, so the
    orchestrator can dispatch it again or review that aspect itself; a delegate failure
    never ends the review.
    """

    def __init__(
        self,
        git_provider: Any,
        *,
        aspects: list[str],
        run_pass: Any,
        max_delegate_calls: int = 6,
        max_fenced_chars: int = MAX_FENCED_CHARS,
    ) -> None:
        super().__init__(git_provider, max_fenced_chars=max_fenced_chars)
        self._aspects = aspects
        self._run_pass = run_pass
        self._max_delegate_calls = max_delegate_calls
        self._delegate_calls = 0
        self.pass_results: dict[str, ReviewPassResult] = {}

    def handlers(self) -> dict[str, Handler]:
        return {**super().handlers(), RUN_REVIEW_PASS: self._review_pass}

    def tool_definitions(self) -> list[dict[str, Any]]:
        return [*super().tool_definitions(), build_review_pass_tool_definition(self._aspects)]

    async def _review_pass(self, args: dict[str, Any]) -> ToolOutcome:
        parsed = parse_argument(_ReviewPassArgs, args)
        aspect = parsed.aspect.strip().lower()
        if aspect not in self._aspects:
            offered = ", ".join(self._aspects)
            return ToolOutcome.error(f"'{parsed.aspect}' is not an aspect here. Offered: {offered}.")
        if aspect in self.pass_results:
            return ToolOutcome.error(
                f"The {aspect} pass already ran this review; its findings are above. "
                "Verify them yourself rather than running it again."
            )
        # Counted before the first await, so calls in one round count deterministically.
        if self._delegate_calls >= self._max_delegate_calls:
            return ToolOutcome.error(
                f"{RUN_REVIEW_PASS} has already run {self._delegate_calls} times this review. "
                "Work with the findings you have."
            )
        self._delegate_calls += 1
        try:
            result = await self._run_pass(aspect, parsed.brief or "")
        except ValueError as failed:  # a pass that never submitted
            return ToolOutcome.error(f"The {aspect} pass could not complete: {failed}")
        self.pass_results[aspect] = result
        return self._fenced({"aspect": aspect, **result.model_dump(mode="json", exclude_none=True)})


class ReviewAgent:
    """One agentic review of one pull request.

    ``variables`` is the reviewer's Jinja variable dict — the same one the classic
    `/review` builds — so the two tools stay in step on the ``require_*`` switches that
    shape the output schema.
    """

    def __init__(
        self,
        git_provider: Any,
        variables: dict[str, Any],
        *,
        client: Any = None,
    ) -> None:
        self.git_provider = git_provider
        self.variables = dict(variables)
        self._client = client
        self._owns_client = False
        self.usage = usage_totals()
        self.aspects = resolve_aspects(self._setting("aspects", list(DEFAULT_ASPECTS)))
        self.executor = ReviewAgentExecutor(
            git_provider,
            aspects=self.aspects,
            run_pass=self._run_pass,
            max_delegate_calls=int(self._setting("max_delegate_calls", 6)),
            max_fenced_chars=int(self._setting("max_fenced_chars", MAX_FENCED_CHARS)),
        )

    # -- configuration ----------------------------------------------------------------

    def _setting(self, name: str, default: Any) -> Any:
        value = get_settings().get(f"pr_agentic_reviewer.{name}", default)
        return default if value is None else value

    @property
    def provider(self) -> str:
        return str(self._setting("provider", "anthropic") or "anthropic").strip().lower()

    @property
    def model(self) -> str:
        return str(self._setting("model", "") or DEFAULT_MODELS.get(self.provider, ""))

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = build_client(self.provider, float(self._setting("request_timeout_s", 600)))
            self._owns_client = True
        return self._client

    @property
    def cache_key(self) -> str:
        """Routing hint for the provider's cache, keyed to the repository. Two reviews of
        the same repo share the static prefix — the prompts and the tool array — and this
        helps them reach the same cache. It is a hint, not a guarantee, and no client
        requires it.

        The repository is read off the provider rather than out of `self.variables`, which
        carries the branch but no repository identity. Keying on the branch would give
        every pull request its own key and fragment exactly the cache this exists to
        consolidate, so a provider that exposes no repository gets no key at all and lets
        the API route on its own.
        """
        repo = str(getattr(self.git_provider, "repo", "") or "").strip()
        return f"pr-agent-agentic-review:{repo}" if repo else ""

    async def aclose(self) -> None:
        """Release the client this agent built. A webhook server runs many reviews in one
        process, and each would otherwise leave a connection pool behind."""
        if self._owns_client and self._client is not None:
            await self._client.aclose()
            self._client = None
            self._owns_client = False

    def _prompt(self, name: str, extra: dict[str, Any] | None = None) -> str:
        """One named prompt from `pr_agentic_reviewer_prompts.toml`, rendered against the
        reviewer's variables. ``fence_notice`` is injected here rather than stored in the
        variables, so the notice a prompt carries and the fence a tool result is wrapped
        in cannot drift apart."""
        template = get_settings().pr_agentic_reviewer_prompt.get(name, "")
        return render(
            template, {**self.variables, "fence_notice": PR_CONTENT_FENCE.notice, **(extra or {})}
        )

    @property
    def review_rules(self) -> str:
        """The phases, rules and output schema every runtime of this agent shares."""
        return self._prompt("review_rules")

    # -- the run ----------------------------------------------------------------------

    def _context_block(self) -> str:
        """The per-request system block: what moves between two reviews of the same repo.

        It sits behind the static prompt's cache breakpoint, so a second review of the
        same repository re-reads only this block. The PR's own text is the author's, so it
        is fenced like any tool result.
        """
        return PR_CONTENT_FENCE.fence_payload(
            {
                "title": self.variables.get("title", ""),
                "branch": self.variables.get("branch", ""),
                "description": self.variables.get("description", ""),
                "language": self.variables.get("language", ""),
                "commit_messages": self.variables.get("commit_messages_str", ""),
                "num_changed_files": self.variables.get("num_pr_files", 0),
            },
            int(self._setting("max_fenced_chars", MAX_FENCED_CHARS)),
        )

    async def _run_pass(self, aspect: str, brief: str) -> ReviewPassResult:
        return await run_review_pass(
            client=self.client,
            git_provider=self.git_provider,
            aspect=aspect,
            brief=brief,
            system_prompt=self._prompt("pass_system", {"aspect": aspect}),
            context=self._context_block(),
            model=str(self._setting("pass_model", "") or self.model),
            max_findings=int(self._setting("max_findings_per_pass", 6)),
            max_tokens=int(self._setting("max_tokens", 16000)),
            max_tool_iterations=int(self._setting("pass_max_tool_iterations", 12)),
            max_tool_calls=int(self._setting("pass_max_tool_calls", 60)),
            max_fenced_chars=int(self._setting("max_fenced_chars", MAX_FENCED_CHARS)),
            effort=str(self._setting("effort", "")),
            force_first_read=bool(self._setting("force_first_read", True)),
            usage=self.usage,
            cache_key=self.cache_key,
            # A pass reads more than the orchestrator does, so it is the loop the setting
            # was written for; leaving it unwired would apply it only where it is needed
            # least.
            compact_above_tokens=int(self._setting("compact_history_above_tokens", 0)),
        )

    async def run(self) -> str:
        """The review as the model's final text, in the classic `/review` YAML schema."""
        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": (
                    "Review this pull request. Dispatch the passes this change calls for, "
                    "verify what they report against the code yourself, then answer with the "
                    "review YAML and nothing else."
                ),
            }
        ]
        result: LoopResult = await run_turn_loop(
            client=self.client,
            executor=self.executor,
            model=self.model,
            static_system=self._prompt("orchestrator_system", {"review_rules": self.review_rules}),
            messages=messages,
            context=self._context_block(),
            max_tokens=int(self._setting("max_tokens", 16000)),
            max_tool_iterations=int(self._setting("max_tool_iterations", 20)),
            max_tool_calls=int(self._setting("max_tool_calls", 120)),
            forced_first_tool=(
                LIST_CHANGED_FILES if self._setting("force_first_read", True) else None
            ),
            effort=str(self._setting("effort", "")),
            compact_above_tokens=int(self._setting("compact_history_above_tokens", 0)),
            usage=self.usage,
            cache_key=self.cache_key,
            label="orchestrator",
        )
        get_logger().info(
            f"agentic review finished provider={self.provider} "
            f"passes={sorted(self.executor.pass_results)} "
            f"rounds={result.rounds} tool_calls={result.tool_calls} usage={self.usage}"
        )
        return result.text

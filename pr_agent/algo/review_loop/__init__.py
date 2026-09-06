"""A code review loop on the Claude Messages API or the OpenAI Responses API.

The loop engineering here is adapted from `anthropics/commerce-agents`, whose design rule
is the one this package follows: an agent is defined once — prompt, tool contracts,
subagents, gates — and each runtime runs that one definition. The definition lives in
`pr_agent/settings/pr_agentic_reviewer_prompts.toml`, `pr_tools` and `delegation`; a
second runtime over it is a new caller, not a second copy.

Modules:

- ``fencing``          PR text sanitized and wrapped as data, never instruction.
- ``prompt_assembly``  where the cache breakpoints and the per-request block go.
- ``model_client``     the seam between the loop and a model API; the only provider code.
- ``turn``             accounting, compaction, conversation repair.
- ``execution``        the executor frame; one ``execute`` that never raises.
- ``pr_tools``         the PR read contracts over ``GitProvider``.
- ``delegation``       a review pass as an isolated, schema-validated subagent.
- ``runtime``          the turn loop itself.
- ``review_agent``     the orchestrator that dispatches passes and verifies them.
"""

from pr_agent.algo.review_loop.execution import InvalidArguments, ToolExecutor, ToolOutcome
from pr_agent.algo.review_loop.fencing import PR_CONTENT_FENCE, Fence
from pr_agent.algo.review_loop.model_client import (
    AnthropicClient,
    ModelClient,
    ModelResponse,
    OpenAIResponsesClient,
    ToolCall,
    build_client,
)
from pr_agent.algo.review_loop.pr_tools import PRToolExecutor, build_pr_tool_definitions
from pr_agent.algo.review_loop.review_agent import ReviewAgent
from pr_agent.algo.review_loop.runtime import LoopResult, run_turn_loop

__all__ = [
    "PR_CONTENT_FENCE",
    "AnthropicClient",
    "Fence",
    "InvalidArguments",
    "LoopResult",
    "ModelClient",
    "ModelResponse",
    "OpenAIResponsesClient",
    "PRToolExecutor",
    "ReviewAgent",
    "ToolCall",
    "ToolExecutor",
    "ToolOutcome",
    "build_client",
    "build_pr_tool_definitions",
    "run_turn_loop",
]

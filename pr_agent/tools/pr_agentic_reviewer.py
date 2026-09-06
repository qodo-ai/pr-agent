from functools import partial

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.algo.review_loop.review_agent import ReviewAgent
from pr_agent.log import get_logger
from pr_agent.tools.pr_reviewer import PRReviewer

# The model answers with the review YAML; some wrap it in a code fence anyway.
_FENCES = ("```yaml", "```yml", "```")


def strip_code_fence(text: str) -> str:
    """The YAML inside a fenced block, or ``text`` unchanged when it is not fenced."""
    body = text.strip()
    for fence in _FENCES:
        if body.startswith(fence):
            body = body[len(fence) :].lstrip("\n")
            break
    else:
        return body
    return body[: body.rindex("```")].rstrip() if body.rstrip().endswith("```") else body


class PRAgenticReviewer(PRReviewer):
    """`/review` with the prediction produced by the review loop.

    Only :meth:`_generate_prediction` differs: the parent's gates, YAML parsing, markdown
    rendering, inline key issues, labels and publishing all run unchanged, so a repository
    that switches to this command gets the same review comment from a different process.
    """

    def __init__(self, pr_url: str, is_answer: bool = False, is_auto: bool = False,
                 args: list = None, ai_handler: partial[BaseAiHandler,] = LiteLLMAIHandler):
        super().__init__(pr_url, is_answer=is_answer, is_auto=is_auto, args=args,
                         ai_handler=ai_handler)
        self.review_agent = None

    async def _generate_prediction(self) -> None:
        """Run the agentic review and store its YAML answer.

        No fallback-model retry: the loop is the expensive part of this command, and the
        model is `pr_agentic_reviewer.model`, not one of the litellm fallbacks, so
        retrying it would repeat the same run against the same model.
        """
        self.review_agent = ReviewAgent(self.git_provider, self.vars)
        get_logger().info(
            f"Agentic review starting: provider={self.review_agent.provider} "
            f"model={self.review_agent.model} aspects={self.review_agent.aspects}"
        )
        try:
            answer = await self.review_agent.run()
        finally:
            # A webhook server runs many reviews in one process; the agent built an HTTP
            # client for this one and nothing else will release it.
            await self.review_agent.aclose()
        if not answer.strip():
            get_logger().warning("Agentic review produced no answer")
            self.prediction = None
            return
        self.prediction = strip_code_fence(answer)
        get_logger().debug("Agentic review prediction", artifact=self.prediction)

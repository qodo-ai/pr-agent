import pytest

from pr_agent.algo.pr_processing import retry_with_fallback_models
from pr_agent.config_loader import get_settings
from pr_agent.tools.pr_help_message import PRHelpMessage
from tests.unittest._settings_helpers import restore_settings, snapshot_settings

_TRACKED_KEYS = (
    "config.model",
    "config.fallback_models",
    "openai.deployment_id",
    "openai.fallback_deployments",
)


class FakeAiHandler:
    def __init__(self, behavior_by_model: dict[str, tuple[str, str] | Exception]):
        self.behavior_by_model = behavior_by_model
        self.calls = []

    async def chat_completion(self, model: str, temperature: float, system: str, user: str):
        self.calls.append(model)
        outcome = self.behavior_by_model.get(model)
        if isinstance(outcome, Exception):
            raise outcome
        if outcome is None:
            raise RuntimeError(f"Unexpected model call: {model}")
        return outcome


def _build_pr_help_tool(fake_ai_handler: FakeAiHandler) -> PRHelpMessage:
    tool = PRHelpMessage.__new__(PRHelpMessage)
    tool.ai_handler = fake_ai_handler
    tool.question_str = "How do I configure PR-Agent?"
    tool.return_as_string = False
    tool.vars = {
        "question": tool.question_str,
        "snippets": "fake docs snippet",
    }
    return tool


@pytest.fixture
def fallback_settings():
    snapshot = snapshot_settings(_TRACKED_KEYS)
    get_settings().set("config.model", "primary-model")
    get_settings().set("config.fallback_models", ["fallback-model"])
    get_settings().set("openai.deployment_id", None)
    get_settings().set("openai.fallback_deployments", [])
    yield
    restore_settings(snapshot)


async def test_fallback_attempted_when_primary_model_fails(fallback_settings):
    fake_handler = FakeAiHandler({
        "primary-model": RuntimeError("primary model failed"),
        "fallback-model": ("fallback answer response", "stop"),
    })
    tool = _build_pr_help_tool(fake_handler)

    response = await retry_with_fallback_models(tool._prepare_prediction)

    assert response == "fallback answer response"
    assert fake_handler.calls == ["primary-model", "fallback-model"]


async def test_exception_propagates_when_all_models_fail(fallback_settings):
    primary_error = RuntimeError("primary model failed")
    fallback_error = ValueError("fallback model failed")
    fake_handler = FakeAiHandler({
        "primary-model": primary_error,
        "fallback-model": fallback_error,
    })
    tool = _build_pr_help_tool(fake_handler)

    with pytest.raises(Exception) as exc_info:
        await retry_with_fallback_models(tool._prepare_prediction)

    assert fake_handler.calls == ["primary-model", "fallback-model"]
    assert "Failed to generate prediction with any model" in str(exc_info.value)
    assert exc_info.value.__cause__ is fallback_error

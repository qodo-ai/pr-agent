"""Question-mode /help runs on the configured model, with or without an OpenAI key.

The question path loads the documentation corpus and calls the configured model
handler; it calculates no embeddings, so an absent ``openai.key`` must not stop
it for users running a non-OpenAI provider.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pr_agent.config_loader import get_settings
from pr_agent.tools.pr_help_message import PRHelpMessage
from tests.unittest._settings_helpers import SENTINEL, restore_settings, snapshot_settings

OPENAI_KEY_MARKER = "requires an OpenAI API key"

MODEL_ANSWER = """\
response: |
  Set `pr_reviewer` options in your configuration file.
relevant_sections:
- file_name: "usage-guide/automations_and_usage.md"
  relevant_section_header_string: "Configuration options"
"""


class StubProvider:
    def __init__(self):
        self.pr_url = "https://example.com/org/repo/pull/1"
        self.published = []

    def publish_comment(self, pr_comment: str, is_temporary: bool = False):
        self.published.append(pr_comment)


def _make_help_tool(provider) -> PRHelpMessage:
    tool = PRHelpMessage.__new__(PRHelpMessage)
    tool.git_provider = provider
    tool.question_str = "How do I configure automatic reviews?"
    tool.return_as_string = False
    tool.vars = {"question": tool.question_str, "snippets": ""}
    tool.token_handler = MagicMock()
    tool.token_handler.count_tokens.return_value = 100
    return tool


@pytest.fixture
def published_output_without_openai_key():
    snapshot = snapshot_settings(["config.publish_output", "openai.key"])
    get_settings().set("config.publish_output", True)
    # ``restore_settings`` removes a key whose value is SENTINEL; use it to
    # clear ``openai.key`` for the duration of the test.
    restore_settings({"openai.key": SENTINEL})
    yield
    restore_settings(snapshot)


@pytest.mark.asyncio
async def test_question_mode_reaches_the_model_without_an_openai_key(published_output_without_openai_key):
    provider = StubProvider()
    tool = _make_help_tool(provider)

    with patch("pr_agent.tools.pr_help_message.retry_with_fallback_models",
               new=AsyncMock(return_value=MODEL_ANSWER)) as model_call:
        await tool.run()

    assert model_call.await_count == 1, "the configured model handler must be invoked"
    assert len(provider.published) == 1
    assert OPENAI_KEY_MARKER not in provider.published[0]
    assert "Set `pr_reviewer` options" in provider.published[0]

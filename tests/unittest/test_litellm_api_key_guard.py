"""
Tests for the litellm.api_key guard in LiteLLMAIHandler.chat_completion.

Verifies:
  - Placeholder key (DUMMY_LITELLM_API_KEY) is never injected into the call.
  - None is not injected (e.g. when OpenAI key is set via litellm.openai_key).
  - Real provider keys (Groq, XAI, OpenRouter, Azure AD) ARE injected.
"""
from unittest.mock import AsyncMock, MagicMock, patch

import litellm
import pytest

import pr_agent.algo.ai_handlers.litellm_ai_handler as litellm_handler
from pr_agent.algo.ai_handlers.litellm_ai_handler import DUMMY_LITELLM_API_KEY, LiteLLMAIHandler


def _make_settings():
    """Minimal settings object that satisfies __init__ and chat_completion."""
    return type("Settings", (), {
        "config": type("Config", (), {
            "reasoning_effort": None,
            "ai_timeout": 30,
            "custom_reasoning_model": False,
            "max_model_tokens": 32000,
            "verbosity_level": 0,
            "seed": -1,
            "get": lambda self, key, default=None: default,
        })(),
        "litellm": type("LiteLLM", (), {
            "get": lambda self, key, default=None: default,
        })(),
        "get": lambda self, key, default=None: default,
    })()


def _mock_response():
    """Minimal acompletion response."""
    mock = MagicMock()
    mock.__getitem__ = lambda self, key: {
        "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]
    }[key]
    mock.dict.return_value = {"choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}]}
    return mock


@pytest.fixture(autouse=True)
def patch_settings(monkeypatch):
    monkeypatch.setattr(litellm_handler, "get_settings", lambda: _make_settings())


def _make_anthropic_settings():
    """Settings with ANTHROPIC.KEY configured, no OPENAI.KEY.

    This simulates the original bug scenario: ANTHROPIC.KEY is set,
    but OPENAI.KEY is not, so litellm.api_key falls back to DUMMY_LITELLM_API_KEY.
    """
    anthropic_key = "sk-ant-test-real-key"
    return type("Settings", (), {
        "config": type("Config", (), {
            "reasoning_effort": None,
            "ai_timeout": 30,
            "custom_reasoning_model": False,
            "max_model_tokens": 32000,
            "verbosity_level": 0,
            "seed": -1,
            "get": lambda self, key, default=None: default,
        })(),
        "litellm": type("LiteLLM", (), {
            "get": lambda self, key, default=None: default,
        })(),
        "anthropic": type("Anthropic", (), {
            "key": anthropic_key
        })(),
        # Return the Anthropic key when settings.get("ANTHROPIC.KEY") is called
        "get": lambda self, key, default=None: (
            anthropic_key if key == "ANTHROPIC.KEY" else default
        ),
    })()


class TestApiKeyGuard:

    @pytest.mark.asyncio
    async def test_dummy_key_not_forwarded(self, monkeypatch):
        """api_key must NOT appear in kwargs when litellm.api_key is the placeholder."""
        monkeypatch.setattr(litellm, "api_key", DUMMY_LITELLM_API_KEY)

        with patch("pr_agent.algo.ai_handlers.litellm_ai_handler.acompletion",
                   new_callable=AsyncMock) as mock_call:
            mock_call.return_value = _mock_response()
            handler = LiteLLMAIHandler()
            await handler.chat_completion(model="gpt-4o", system="sys", user="usr")

        assert "api_key" not in mock_call.call_args[1]

    @pytest.mark.asyncio
    async def test_none_api_key_not_forwarded(self, monkeypatch):
        """api_key must NOT appear in kwargs when litellm.api_key is None.

        This is the OpenAI-key path: OPENAI.KEY sets litellm.openai_key,
        leaving litellm.api_key at None.
        """
        monkeypatch.setattr(litellm, "api_key", None)

        with patch("pr_agent.algo.ai_handlers.litellm_ai_handler.acompletion",
                   new_callable=AsyncMock) as mock_call:
            mock_call.return_value = _mock_response()
            handler = LiteLLMAIHandler()
            await handler.chat_completion(model="gpt-4o", system="sys", user="usr")

        assert "api_key" not in mock_call.call_args[1]

    @pytest.mark.asyncio
    async def test_real_key_forwarded(self, monkeypatch):
        """api_key IS injected when a real provider key is in litellm.api_key (e.g. Groq, XAI).

        The key is set after __init__ to simulate a provider having stored its key there
        during initialization, without triggering the placeholder value in __init__.
        """
        real_key = "sk-test-real-provider-key"

        with patch("pr_agent.algo.ai_handlers.litellm_ai_handler.acompletion",
                   new_callable=AsyncMock) as mock_call:
            mock_call.return_value = _mock_response()
            handler = LiteLLMAIHandler()
            # Set after init so __init__'s own dummy-key assignment doesn't overwrite it
            monkeypatch.setattr(litellm, "api_key", real_key)
            await handler.chat_completion(model="gpt-4o", system="sys", user="usr")

        assert mock_call.call_args[1]["api_key"] == real_key

    @pytest.mark.asyncio
    async def test_anthropic_key_not_shadowed_by_dummy_key(self, monkeypatch):
        """Original bug scenario: ANTHROPIC.KEY configured without OPENAI.KEY.

        During __init__, litellm.api_key is set to DUMMY_LITELLM_API_KEY (fallback)
        because OPENAI.KEY is not configured. But litellm.anthropic_key is also set.
        The guard must prevent the dummy key from being passed to the call,
        allowing litellm to use anthropic_key internally.

        This test replicates the exact bug from GitHub issue #2042.
        """
        # Override settings to simulate Anthropic configured, OpenAI not configured
        monkeypatch.setattr(litellm_handler, "get_settings", _make_anthropic_settings)

        with patch("pr_agent.algo.ai_handlers.litellm_ai_handler.acompletion",
                   new_callable=AsyncMock) as mock_call:
            mock_call.return_value = _mock_response()
            handler = LiteLLMAIHandler()

            # After init: litellm.api_key should be the dummy (OpenAI fallback),
            # but litellm.anthropic_key is the real Anthropic key
            assert litellm.api_key == DUMMY_LITELLM_API_KEY

            # Call with Anthropic model
            await handler.chat_completion(
                model="claude-3-5-sonnet-20241022",
                system="sys",
                user="usr"
            )

            # Verify the dummy key was NOT passed to the call.
            # This allows litellm to use litellm.anthropic_key internally.
            assert "api_key" not in mock_call.call_args[1]

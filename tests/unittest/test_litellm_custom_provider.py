from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import pr_agent.algo.ai_handlers.litellm_ai_handler as litellm_handler
from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler


def create_mock_settings(custom_llm_provider=None):
    litellm_settings = type("", (), {"get": lambda self, key, default=None: default})()
    if custom_llm_provider is not None:
        litellm_settings.custom_llm_provider = custom_llm_provider

    def get_value(key, default=None):
        values = {
            "LITELLM.CUSTOM_LLM_PROVIDER": custom_llm_provider,
        }
        return values.get(key, default)

    return type("", (), {
        "config": type("", (), {
            "ai_timeout": 120,
            "custom_reasoning_model": False,
            "verbosity_level": 0,
            "get": lambda self, key, default=None: default,
        })(),
        "litellm": litellm_settings,
        "get": staticmethod(get_value),
    })()


def create_mock_acompletion_response():
    mock_response = MagicMock()
    mock_response.__getitem__ = lambda self, key: {
        "choices": [{"message": {"content": "test"}, "finish_reason": "stop"}]
    }[key]
    mock_response.dict.return_value = {"choices": [{"message": {"content": "test"}, "finish_reason": "stop"}]}
    return mock_response


@pytest.mark.asyncio
async def test_custom_llm_provider_is_forwarded_without_rewriting_model(monkeypatch):
    fake_settings = create_mock_settings("openai")
    monkeypatch.setattr(litellm_handler, "get_settings", lambda: fake_settings)

    with patch("pr_agent.algo.ai_handlers.litellm_ai_handler.acompletion", new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value = create_mock_acompletion_response()

        handler = LiteLLMAIHandler()
        await handler.chat_completion(
            model="claude-sonnet-4-5",
            system="test system",
            user="test user",
        )

        call_kwargs = mock_completion.call_args[1]
        assert call_kwargs["model"] == "claude-sonnet-4-5"
        assert call_kwargs["custom_llm_provider"] == "openai"


@pytest.mark.asyncio
async def test_custom_llm_provider_is_omitted_when_unset(monkeypatch):
    fake_settings = create_mock_settings()
    monkeypatch.setattr(litellm_handler, "get_settings", lambda: fake_settings)

    with patch("pr_agent.algo.ai_handlers.litellm_ai_handler.acompletion", new_callable=AsyncMock) as mock_completion:
        mock_completion.return_value = create_mock_acompletion_response()

        handler = LiteLLMAIHandler()
        await handler.chat_completion(
            model="claude-sonnet-4-5",
            system="test system",
            user="test user",
        )

        call_kwargs = mock_completion.call_args[1]
        assert "custom_llm_provider" not in call_kwargs

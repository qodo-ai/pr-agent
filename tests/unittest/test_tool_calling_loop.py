"""The tool-calling loop: answer, call, answer again, and always finish.

`chat_completion_with_tools` owns a conversation rather than a single request, so the parts that
matter are: tools are only offered when enabled, every call is executed and fed back, the loop
is bounded, and a spent budget still produces an answer.
"""
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from pr_agent.algo.ai_handlers.litellm_ai_handler import LiteLLMAIHandler
from pr_agent.algo.tool_registry import Tool, get_tool_registry
from pr_agent.config_loader import get_settings

ECHO = Tool(
    name="echo",
    description="Repeat the given text.",
    parameters={"type": "object", "properties": {"text": {"type": "string"}}, "required": ["text"]},
    handler=lambda text: f"echo: {text}",
)


def _response(message, finish_reason):
    """`_get_completion` answers with (content, finish_reason, raw response)."""
    raw = {"choices": [{"message": message, "finish_reason": finish_reason}]}
    return getattr(message, "content", None), finish_reason, raw


def _answer(content):
    return _response(
        SimpleNamespace(content=content, tool_calls=None, model_dump=lambda: {"role": "assistant"}),
        "stop")


def _tool_request(name="echo", arguments='{"text": "hi"}', call_id="call_1"):
    call = SimpleNamespace(id=call_id, function=SimpleNamespace(name=name, arguments=arguments))
    return _response(
        SimpleNamespace(content=None, tool_calls=[call],
                        model_dump=lambda: {"role": "assistant", "tool_calls": []}),
        "tool_calls")


@pytest.fixture
def handler(monkeypatch):
    monkeypatch.setattr(LiteLLMAIHandler, "__init__", lambda self: None)
    handler = LiteLLMAIHandler()
    return handler


@pytest.fixture
def tools_enabled(monkeypatch):
    registry = get_tool_registry()
    registry.register(ECHO)

    def _set(enabled=True, max_iterations=3):
        get_settings().set("tools.enabled", enabled)
        get_settings().set("tools.allowed", [])
        get_settings().set("tools.max_iterations", max_iterations)
    _set()
    yield _set
    registry.unregister("echo")
    get_settings().set("tools.enabled", False)


async def test_an_answer_without_a_tool_call_is_returned(handler, tools_enabled):
    handler._get_completion = AsyncMock(return_value=_answer("done"))

    text, finish_reason, calls = await handler.chat_completion_with_tools("gpt-4o", "sys", "usr")

    assert (text, finish_reason, calls) == ("done", "stop", [])


async def test_a_tool_call_is_executed_and_fed_back(handler, tools_enabled):
    handler._get_completion = AsyncMock(side_effect=[_tool_request(), _answer("done")])

    text, _finish_reason, calls = await handler.chat_completion_with_tools("gpt-4o", "sys", "usr")

    assert text == "done"
    assert calls == [{"name": "echo", "arguments": '{"text": "hi"}', "result": "echo: hi"}]
    second_call_messages = handler._get_completion.await_args_list[1].kwargs["messages"]
    assert second_call_messages[-1]["role"] == "tool"
    assert second_call_messages[-1]["content"] == "echo: hi"
    assert second_call_messages[-1]["tool_call_id"] == "call_1"


async def test_the_tools_are_offered_on_every_round(handler, tools_enabled):
    handler._get_completion = AsyncMock(side_effect=[_tool_request(), _answer("done")])

    await handler.chat_completion_with_tools("gpt-4o", "sys", "usr")

    for call in handler._get_completion.await_args_list:
        assert call.kwargs["tools"][0]["function"]["name"] == "echo"
        assert call.kwargs["tool_choice"] == "auto"
        assert call.kwargs["allow_tool_calls"] is True


async def test_no_tools_are_offered_when_the_feature_is_off(handler, tools_enabled, monkeypatch):
    """Control: with tools off this is the ordinary single-shot completion."""
    tools_enabled(enabled=False)
    handler.chat_completion = AsyncMock(return_value=("plain", "stop"))
    handler._get_completion = AsyncMock()

    text, finish_reason, calls = await handler.chat_completion_with_tools("gpt-4o", "sys", "usr")

    assert (text, finish_reason, calls) == ("plain", "stop", [])
    handler._get_completion.assert_not_awaited()


async def test_the_loop_is_bounded_and_still_answers(handler, tools_enabled):
    """A model that keeps calling tools is asked once more without them."""
    tools_enabled(max_iterations=2)
    handler._get_completion = AsyncMock(
        side_effect=[_tool_request(), _tool_request(call_id="call_2"), _answer("final")])

    text, _finish_reason, calls = await handler.chat_completion_with_tools("gpt-4o", "sys", "usr")

    assert text == "final"
    assert len(calls) == 2
    assert "tools" not in handler._get_completion.await_args_list[-1].kwargs


async def test_a_failing_tool_does_not_fail_the_answer(handler, tools_enabled):
    handler._get_completion = AsyncMock(
        side_effect=[_tool_request(arguments="{not json"), _answer("done anyway")])

    text, _finish_reason, calls = await handler.chat_completion_with_tools("gpt-4o", "sys", "usr")

    assert text == "done anyway"
    assert calls[0]["result"].startswith("Error: could not read the arguments")


async def test_an_unknown_tool_is_reported_to_the_model(handler, tools_enabled):
    handler._get_completion = AsyncMock(
        side_effect=[_tool_request(name="rm_rf", arguments="{}"), _answer("done")])

    _text, _finish_reason, calls = await handler.chat_completion_with_tools("gpt-4o", "sys", "usr")

    assert "not available" in calls[0]["result"]


async def test_several_calls_in_one_round_are_all_executed(handler, tools_enabled):
    first = SimpleNamespace(id="a", function=SimpleNamespace(name="echo", arguments=json.dumps({"text": "1"})))
    second = SimpleNamespace(id="b", function=SimpleNamespace(name="echo", arguments=json.dumps({"text": "2"})))
    both = _response(
        SimpleNamespace(content=None, tool_calls=[first, second],
                        model_dump=lambda: {"role": "assistant"}),
        "tool_calls")
    handler._get_completion = AsyncMock(side_effect=[both, _answer("done")])

    _text, _finish_reason, calls = await handler.chat_completion_with_tools("gpt-4o", "sys", "usr")

    assert [call["result"] for call in calls] == ["echo: 1", "echo: 2"]


async def test_a_zero_budget_asks_once_without_tools(handler, tools_enabled):
    tools_enabled(max_iterations=0)
    handler._get_completion = AsyncMock(return_value=_answer("straight answer"))

    text, _finish_reason, calls = await handler.chat_completion_with_tools("gpt-4o", "sys", "usr")

    assert (text, calls) == ("straight answer", [])
    assert "tools" not in handler._get_completion.await_args_list[0].kwargs

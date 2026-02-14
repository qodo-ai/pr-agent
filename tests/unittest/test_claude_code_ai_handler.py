import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from tenacity import RetryError

from pr_agent.algo.ai_handlers.claude_code_ai_handler import ClaudeCodeAIHandler


def create_mock_settings():
    """Create a fake settings object for ClaudeCodeAIHandler."""
    return type('', (), {
        'config': type('', (), {
            'verbosity_level': 0,
            'get': lambda self, key, default=None: default
        })(),
        'get': lambda self, key, default=None: {
            'claude_code.cli_path': 'claude',
            'claude_code.timeout': 120,
            'claude_code.model': '',
        }.get(key, default)
    })()


class TestStripModelPrefix:
    def test_strips_claude_code_prefix(self):
        assert ClaudeCodeAIHandler._strip_model_prefix("claude-code/claude-sonnet-4-5") == "claude-sonnet-4-5"

    def test_leaves_other_prefixes_unchanged(self):
        assert ClaudeCodeAIHandler._strip_model_prefix("anthropic/claude-sonnet-4-5") == "anthropic/claude-sonnet-4-5"

    def test_leaves_bare_model_unchanged(self):
        assert ClaudeCodeAIHandler._strip_model_prefix("claude-sonnet-4-5") == "claude-sonnet-4-5"


class TestExtractResponse:
    def test_extract_from_text_block_list(self):
        data = [
            {"type": "text", "text": "Hello"},
            {"type": "text", "text": "World"},
        ]
        assert ClaudeCodeAIHandler._extract_response(data) == "Hello\nWorld"

    def test_extract_from_dict_with_result(self):
        data = {"result": "some response text"}
        assert ClaudeCodeAIHandler._extract_response(data) == "some response text"

    def test_extract_from_dict_with_text(self):
        data = {"text": "some text"}
        assert ClaudeCodeAIHandler._extract_response(data) == "some text"

    def test_extract_from_dict_with_content_list(self):
        data = {"content": [{"type": "text", "text": "nested"}]}
        assert ClaudeCodeAIHandler._extract_response(data) == "nested"

    def test_fallback_to_str(self):
        data = {"unknown_field": 123}
        assert ClaudeCodeAIHandler._extract_response(data) == str(data)

    def test_list_without_text_blocks(self):
        data = [{"type": "image", "url": "http://example.com"}]
        result = ClaudeCodeAIHandler._extract_response(data)
        assert result == json.dumps(data)


@pytest.mark.asyncio
class TestChatCompletion:
    @patch('pr_agent.algo.ai_handlers.claude_code_ai_handler.get_settings')
    @patch('pr_agent.algo.ai_handlers.claude_code_ai_handler.asyncio')
    async def test_successful_response(self, mock_asyncio, mock_get_settings):
        mock_get_settings.return_value = create_mock_settings()

        response_data = [{"type": "text", "text": "AI response here"}]
        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(
            return_value=(json.dumps(response_data).encode(), b"")
        )
        mock_asyncio.create_subprocess_exec = AsyncMock(return_value=mock_proc)
        mock_asyncio.subprocess = MagicMock()
        mock_asyncio.subprocess.PIPE = -1
        mock_asyncio.wait_for = AsyncMock(
            return_value=(json.dumps(response_data).encode(), b"")
        )

        handler = ClaudeCodeAIHandler()
        resp, finish = await handler.chat_completion(
            model="claude-code/claude-sonnet-4-5",
            system="You are helpful",
            user="Hello",
        )
        assert resp == "AI response here"
        assert finish == "stop"

    @patch('pr_agent.algo.ai_handlers.claude_code_ai_handler.get_settings')
    @patch('pr_agent.algo.ai_handlers.claude_code_ai_handler.asyncio')
    async def test_cli_error_raises(self, mock_asyncio, mock_get_settings):
        mock_get_settings.return_value = create_mock_settings()

        mock_proc = AsyncMock()
        mock_proc.returncode = 1
        mock_proc.communicate = AsyncMock(return_value=(b"", b"CLI error"))
        mock_proc.kill = AsyncMock()
        mock_proc.wait = AsyncMock()
        mock_asyncio.create_subprocess_exec = AsyncMock(return_value=mock_proc)
        mock_asyncio.subprocess = MagicMock()
        mock_asyncio.subprocess.PIPE = -1
        mock_asyncio.wait_for = AsyncMock(return_value=(b"", b"CLI error"))

        handler = ClaudeCodeAIHandler()
        with pytest.raises(RetryError):
            await handler.chat_completion(
                model="claude-code/claude-sonnet-4-5",
                system="sys",
                user="usr",
            )

    @patch('pr_agent.algo.ai_handlers.claude_code_ai_handler.get_settings')
    @patch('pr_agent.algo.ai_handlers.claude_code_ai_handler.asyncio')
    async def test_timeout_raises(self, mock_asyncio, mock_get_settings):
        import asyncio as real_asyncio
        mock_get_settings.return_value = create_mock_settings()

        mock_proc = AsyncMock()
        mock_proc.kill = AsyncMock()
        mock_proc.wait = AsyncMock()
        mock_asyncio.create_subprocess_exec = AsyncMock(return_value=mock_proc)
        mock_asyncio.subprocess = MagicMock()
        mock_asyncio.subprocess.PIPE = -1
        mock_asyncio.wait_for = AsyncMock(side_effect=real_asyncio.TimeoutError)
        mock_asyncio.TimeoutError = real_asyncio.TimeoutError

        handler = ClaudeCodeAIHandler()
        with pytest.raises(RetryError):
            await handler.chat_completion(
                model="claude-code/claude-sonnet-4-5",
                system="sys",
                user="usr",
            )

    @patch('pr_agent.algo.ai_handlers.claude_code_ai_handler.get_settings')
    @patch('pr_agent.algo.ai_handlers.claude_code_ai_handler.asyncio')
    async def test_non_json_output_returned_as_raw(self, mock_asyncio, mock_get_settings):
        mock_get_settings.return_value = create_mock_settings()

        mock_proc = AsyncMock()
        mock_proc.returncode = 0
        mock_proc.communicate = AsyncMock(
            return_value=(b"plain text response", b"")
        )
        mock_asyncio.create_subprocess_exec = AsyncMock(return_value=mock_proc)
        mock_asyncio.subprocess = MagicMock()
        mock_asyncio.subprocess.PIPE = -1
        mock_asyncio.wait_for = AsyncMock(
            return_value=(b"plain text response", b"")
        )

        handler = ClaudeCodeAIHandler()
        resp, finish = await handler.chat_completion(
            model="claude-code/claude-sonnet-4-5",
            system="sys",
            user="usr",
        )
        assert resp == "plain text response"
        assert finish == "stop"


class TestDeploymentId:
    @patch('pr_agent.algo.ai_handlers.claude_code_ai_handler.get_settings')
    def test_deployment_id_is_none(self, mock_get_settings):
        mock_get_settings.return_value = create_mock_settings()
        handler = ClaudeCodeAIHandler()
        assert handler.deployment_id is None

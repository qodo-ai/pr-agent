import asyncio
import json
import os
import subprocess

import httpx
import openai
from tenacity import retry, retry_if_exception_type, retry_if_not_exception_type, stop_after_attempt

from pr_agent.algo.ai_handlers.base_ai_handler import BaseAiHandler
from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger

MODEL_RETRIES = 2
_DUMMY_REQUEST = httpx.Request("POST", "https://claude-code-cli/v1/chat")


class ClaudeCodeAIHandler(BaseAiHandler):
    """
    AI handler that invokes the Claude Code CLI (claude) as a subprocess.
    Users with Claude Code installed can use this handler without needing
    separate API keys.

    Authentication:
        Set the CLAUDE_CODE_TOKEN environment variable for headless/CI usage.
        The token is obtained by running `claude setup-token` locally
        (requires a Claude subscription).
    """

    _token_setup_done = False

    def __init__(self):
        self.cli_path = get_settings().get("claude_code.cli_path", "claude")
        self.timeout = get_settings().get("claude_code.timeout", 120)
        self.model_override = get_settings().get("claude_code.model", "")
        self._ensure_token_setup()

    @classmethod
    def _ensure_token_setup(cls):
        """Run `claude setup-token` if CLAUDE_CODE_TOKEN env var is set."""
        if cls._token_setup_done:
            return
        token = os.environ.get("CLAUDE_CODE_TOKEN")
        if not token:
            return
        try:
            cli_path = get_settings().get("claude_code.cli_path", "claude")
            result = subprocess.run(
                [cli_path, "setup-token"],
                input=token,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                get_logger().info("Claude Code token configured successfully")
            else:
                get_logger().warning(f"claude setup-token failed: {result.stderr.strip()}")
        except Exception as e:
            get_logger().warning(f"Failed to configure Claude Code token: {e}")
        cls._token_setup_done = True

    @property
    def deployment_id(self):
        return None

    @staticmethod
    def _strip_model_prefix(model: str) -> str:
        """Strip the 'claude-code/' prefix from model names."""
        if model.startswith("claude-code/"):
            return model[len("claude-code/"):]
        return model

    @retry(
        retry=retry_if_exception_type(openai.APIError) & retry_if_not_exception_type(openai.RateLimitError),
        stop=stop_after_attempt(MODEL_RETRIES),
    )
    async def chat_completion(self, model: str, system: str, user: str,
                              temperature: float = 0.2, img_path: str = None):
        try:
            # Determine which model to use
            effective_model = self.model_override or self._strip_model_prefix(model)

            cmd = [
                self.cli_path,
                "-p",
                "--output-format", "json",
            ]

            if effective_model:
                cmd.extend(["--model", effective_model])

            if system:
                cmd.extend(["--system-prompt", system])

            get_logger().debug(f"Running Claude Code CLI: {' '.join(cmd[:6])}...")
            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"\nSystem prompt:\n{system}")
                get_logger().info(f"\nUser prompt:\n{user}")

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(input=user.encode("utf-8")),
                    timeout=self.timeout,
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                raise openai.APIError(
                    f"Claude Code CLI timed out after {self.timeout}s",
                    request=_DUMMY_REQUEST, body=None,
                )

            if proc.returncode != 0:
                error_text = stderr.decode("utf-8", errors="replace").strip()
                raise openai.APIError(
                    f"Claude Code CLI exited with code {proc.returncode}: {error_text}",
                    request=_DUMMY_REQUEST, body=None,
                )

            raw_output = stdout.decode("utf-8", errors="replace").strip()

            # Parse JSON output
            try:
                response_data = json.loads(raw_output)
            except json.JSONDecodeError:
                # If not valid JSON, use raw output as the response text
                resp = raw_output
                get_logger().debug("Claude Code CLI returned non-JSON output, using raw text")
                return resp, "stop"

            # Extract response text from JSON output
            resp = self._extract_response(response_data)

            get_logger().debug(f"\nAI response:\n{resp}")
            if get_settings().config.verbosity_level >= 2:
                get_logger().info(f"\nAI response:\n{resp}")

            return resp, "stop"

        except openai.APIError:
            raise
        except Exception as e:
            get_logger().warning(f"Error during Claude Code CLI inference: {e}")
            raise openai.APIError(
                f"Claude Code CLI error: {e}",
                request=_DUMMY_REQUEST, body=None,
            ) from e

    @staticmethod
    def _extract_response(response_data) -> str:
        """Extract text content from Claude Code JSON output."""
        # Handle the case where the response is a list of message blocks
        if isinstance(response_data, list):
            text_parts = []
            for block in response_data:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
            if text_parts:
                return "\n".join(text_parts)
            # Fallback: return the entire JSON as a string
            return json.dumps(response_data)

        # Handle dict response with a "result" or "text" field
        if isinstance(response_data, dict):
            if "result" in response_data:
                result = response_data["result"]
                if isinstance(result, str):
                    return result
                # result might be a list of blocks
                return ClaudeCodeAIHandler._extract_response(result)
            if "text" in response_data:
                return response_data["text"]
            if "content" in response_data:
                return ClaudeCodeAIHandler._extract_response(response_data["content"])

        # Fallback
        return str(response_data)

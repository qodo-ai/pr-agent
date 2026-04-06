import asyncio
import json
import os
import re
from typing import Union, Dict, Any

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.config_loader import get_settings
from pr_agent.git_providers.utils import apply_repo_settings
from pr_agent.log import get_logger
from pr_agent.tools.pr_code_suggestions import PRCodeSuggestions
from pr_agent.tools.pr_description import PRDescription
from pr_agent.tools.pr_reviewer import PRReviewer


def is_true(value: Union[str, bool]) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return False


def get_setting_or_env(key: str, default: Union[str, bool] = None) -> Union[str, bool]:
    try:
        value = get_settings().get(key, default)
    except AttributeError:
        value = (
            os.getenv(key, None)
            or os.getenv(key.upper(), None)
            or os.getenv(key.lower(), None)
            or default
        )
    return value


def normalize_url(url: str) -> str:
    if not url:
        return url
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url.rstrip("/")


def should_process_pr_logic(body: Dict[str, Any]) -> bool:
    """Advanced rule-based filtering: skip specific PRs that do not require review."""
    try:
        pull_request = body.get("pull_request", {})
        title = pull_request.get("title", "")
        sender = body.get("sender", {}).get("login")
        source_branch = pull_request.get("head", {}).get("ref", "")
        target_branch = pull_request.get("base", {}).get("ref", "")

        # 1. Ignore specific users
        ignore_pr_users = get_settings().get("CONFIG.IGNORE_PR_AUTHORS", [])
        if ignore_pr_users and sender:
            if any(re.search(regex, sender) for regex in ignore_pr_users):
                get_logger().info(f"Skipped: ignoring PR from user '{sender}'")
                return False

        # 2. Ignore specific titles
        if title:
            ignore_pr_title_re = get_settings().get("CONFIG.IGNORE_PR_TITLE", [])
            if not isinstance(ignore_pr_title_re, list):
                ignore_pr_title_re = [ignore_pr_title_re]
            if ignore_pr_title_re and any(re.search(regex, title) for regex in ignore_pr_title_re):
                get_logger().info(f"Skipped: ignoring PR with matching title '{title}'")
                return False

        # 3. Ignore specific source branches
        ignore_pr_source_branches = get_settings().get("CONFIG.IGNORE_PR_SOURCE_BRANCHES", [])
        if ignore_pr_source_branches and source_branch:
            if any(re.search(regex, source_branch) for regex in ignore_pr_source_branches):
                get_logger().info(f"Skipped: ignoring PR from source branch '{source_branch}'")
                return False

        # 4. Ignore specific target branches
        ignore_pr_target_branches = get_settings().get("CONFIG.IGNORE_PR_TARGET_BRANCHES", [])
        if ignore_pr_target_branches and target_branch:
            if any(re.search(regex, target_branch) for regex in ignore_pr_target_branches):
                get_logger().info(f"Skipped: ignoring PR targeting branch '{target_branch}'")
                return False
    except Exception as e:
        get_logger().error(f"Failed to execute should_process_pr_logic: {e}")
    return True


async def run_action():
    # 1. Read environment variables
    EVENT_NAME = os.environ.get("GITEA_EVENT_NAME") or os.environ.get("GITHUB_EVENT_NAME")
    EVENT_PATH = os.environ.get("GITEA_EVENT_PATH") or os.environ.get("GITHUB_EVENT_PATH")
    TOKEN = os.environ.get("GITEA_TOKEN") or os.environ.get("GITHUB_TOKEN")
    OPENAI_KEY = os.environ.get("OPENAI_KEY") or os.environ.get("OPENAI.KEY")
    OPENAI_ORG = os.environ.get("OPENAI_ORG") or os.environ.get("OPENAI.ORG")
    DEVSTAR_URL = os.environ.get("DEVSTAR_URL")
    GITEA_URL = os.environ.get("GITEA_URL")
    FINAL_GITEA_URL = normalize_url(DEVSTAR_URL or GITEA_URL or "https://gitea.com")

    if not EVENT_NAME or not EVENT_PATH or not TOKEN:
        get_logger().error(
            "Container startup failed: missing required environment variables (EVENT_NAME, EVENT_PATH, TOKEN)."
        )
        return

    # 2. Configure Git provider identity and self-hosted address
    get_settings().set("config.git_provider", "gitea")
    get_settings().set("gitea.personal_access_token", TOKEN)

    if OPENAI_KEY:
        get_settings().set("OPENAI.KEY", OPENAI_KEY)
    else:
        print("OPENAI_KEY not set")

    if OPENAI_ORG:
        get_settings().set("OPENAI.ORG", OPENAI_ORG)

    get_settings().set("gitea.url", FINAL_GITEA_URL)
    get_settings().set("gitea.api_url", f"{FINAL_GITEA_URL}/api/v1")

    if DEVSTAR_URL:
        get_logger().info(f"Resolved Gitea URL from DEVSTAR_URL: {FINAL_GITEA_URL}")
    elif GITEA_URL:
        get_logger().info(f"Resolved Gitea URL from GITEA_URL: {FINAL_GITEA_URL}")  
    else:
        get_logger().info(f"No URL configuration detected, using default:{FINAL_GITEA_URL}")

    get_settings().set("GITHUB.USER_TOKEN", TOKEN)
    get_settings().set("GITHUB.DEPLOYMENT_TYPE", "user")

    # 3. Read the local payload JSON
    try:
        with open(EVENT_PATH, "r") as f:
            event_payload = json.load(f)
    except Exception as e:
        get_logger().error(f"Failed to parse payload JSON: {e}")
        return

    # 4. Extract the PR URL
    pr_url = None
    if EVENT_NAME in ["pull_request", "pull_request_target"]:
        pr_url = event_payload.get("pull_request", {}).get("html_url")
    elif EVENT_NAME == "issue_comment":
        issue_data = event_payload.get("issue", {})
        if "pull_request" in issue_data:
            pr_url = issue_data.get("pull_request", {}).get("html_url") or issue_data.get("html_url")

    if not pr_url:
        get_logger().warning("No valid PR URL found in the payload. Exiting.")
        return

    # 5. Apply repository-level configuration (.pr_agent.toml)
    try:
        apply_repo_settings(pr_url)
    except Exception as e:
        get_logger().warning(f"Failed to apply repository settings: {e}")

    if os.path.exists(".pr_agent.toml"):
        get_logger().info("Loaded local .pr_agent.toml")
        get_settings().load_file(".pr_agent.toml")
    elif os.path.exists("/workspace/.pr_agent.toml"):
        get_settings().load_file("/workspace/.pr_agent.toml")
        get_logger().info("Loaded local .pr_agent.toml")

    # 6. Inject multilingual instruction prompts
    try:
        response_language = get_settings().config.get("response_language", "en-us")
        if response_language.lower() != "en-us":
            get_logger().info(f"Custom response language detected: {response_language}")
            lang_instruction_text = (
                f"Your response MUST be written in the language corresponding to locale code: "
                f"'{response_language}'. This is crucial."
            )
            separator_text = "\n======\n\nIn addition, "

            for key in get_settings():
                setting = get_settings().get(key)
                if str(type(setting)) == "<class 'dynaconf.utils.boxing.DynaBox'>":
                    if key.lower() in ["pr_description", "pr_code_suggestions", "pr_reviewer"]:
                        if hasattr(setting, "extra_instructions"):
                            extra_instructions = setting.extra_instructions
                            if lang_instruction_text not in str(extra_instructions):
                                updated_instructions = (
                                    str(extra_instructions) + separator_text + lang_instruction_text
                                    if extra_instructions
                                    else lang_instruction_text
                                )
                                setting.extra_instructions = updated_instructions
    except Exception as e:
        get_logger().warning(f"Instruction injection failed: {e}")

    # 7. Core event routing and execution
    if EVENT_NAME in ["pull_request", "pull_request_target"]:
        if not should_process_pr_logic(event_payload):
            return

        action = event_payload.get("action")
        if action in ["opened", "reopened", "ready_for_review", "synchronize", "synchronized"]:
            get_settings().config.is_auto_command = True
            get_logger().info(f"Triggered automated review action: {action}")

            auto_describe = get_setting_or_env("GITHUB_ACTION_CONFIG.AUTO_DESCRIBE", True)
            auto_review = get_setting_or_env("GITHUB_ACTION_CONFIG.AUTO_REVIEW", True)
            auto_improve = get_setting_or_env("GITHUB_ACTION_CONFIG.AUTO_IMPROVE", True)

            if is_true(auto_describe) and action not in ["synchronize", "synchronized"]:
                await PRDescription(pr_url).run()
            if is_true(auto_review):
                await PRReviewer(pr_url).run()
            if is_true(auto_improve):
                await PRCodeSuggestions(pr_url).run()
        else:
            get_logger().info(f"Ignoring unconfigured PR action: {action}")

    elif EVENT_NAME == "issue_comment":
        action = event_payload.get("action")
        if action in ["created", "edited"]:
            comment_body = event_payload.get("comment", {}).get("body", "").strip()
            if comment_body.startswith("/"):
                get_logger().info(f"Received user command: {comment_body}")
                await PRAgent().handle_request(pr_url, comment_body)

if __name__ == "__main__":
    asyncio.run(run_action())
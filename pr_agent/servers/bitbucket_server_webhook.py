import ast
import json
import os
from typing import List

import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi.encoders import jsonable_encoder
from fastapi.responses import RedirectResponse
from starlette import status
from starlette.background import BackgroundTasks
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette_context.middleware import RawContextMiddleware

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.algo.utils import update_settings_from_args
from pr_agent.config_loader import get_settings
from pr_agent.git_providers.utils import apply_repo_settings
from pr_agent.git_providers import get_git_provider
from pr_agent.log import LoggingFormat, get_logger, setup_logger
from pr_agent.servers.utils import verify_signature

setup_logger(fmt=LoggingFormat.JSON, level=get_settings().get("CONFIG.LOG_LEVEL", "DEBUG"))
router = APIRouter()


def handle_request(
    background_tasks: BackgroundTasks, url: str, body: str, log_context: dict
):
    log_context["action"] = body
    log_context["api_url"] = url

    async def inner():
        try:
            with get_logger().contextualize(**log_context):
                await PRAgent().handle_request(url, body)
        except Exception as e:
            get_logger().error(f"Failed to handle webhook: {e}")

    background_tasks.add_task(inner)

@router.post("/")
async def redirect_to_webhook():
    return RedirectResponse(url="/webhook")

@router.post("/webhook")
async def handle_webhook(background_tasks: BackgroundTasks, request: Request):
    log_context = {"server_type": "bitbucket_server"}
    data = await request.json()
    get_logger().info(json.dumps(data))

    webhook_secret = get_settings().get("BITBUCKET_SERVER.WEBHOOK_SECRET", None)
    if webhook_secret:
        body_bytes = await request.body()
        if body_bytes.decode('utf-8') == '{"test": true}':
            return JSONResponse(
                status_code=status.HTTP_200_OK, content=jsonable_encoder({"message": "connection test successful"})
            )
        signature_header = request.headers.get("x-hub-signature", None)
        verify_signature(body_bytes, webhook_secret, signature_header)

    commands_to_run = []
    pr_urls = []

    if data["eventKey"] in ["pr:opened", "pr:comment:added"]:
        pr_id = data["pullRequest"]["id"]
        repository_name = data["pullRequest"]["toRef"]["repository"]["slug"]
        project_name = data["pullRequest"]["toRef"]["repository"]["project"]["key"]
        bitbucket_server = get_settings().get("BITBUCKET_SERVER.URL")
        pr_url = f"{bitbucket_server}/projects/{project_name}/repos/{repository_name}/pull-requests/{pr_id}"
        pr_urls.append(pr_url)

        log_context["api_url"] = pr_url
        log_context["event"] = "pull_request"

        if data["eventKey"] == "pr:opened":
            apply_repo_settings(pr_url)
            if get_settings().config.disable_auto_feedback:  # auto commands for PR, and auto feedback is disabled
                get_logger().info(f"Auto feedback is disabled, skipping auto commands for PR {pr_url}", **log_context)
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content=json.dumps({"message": "Auto feedback is disabled, skipping auto commands for PR"}),
                )
            get_settings().set("config.is_auto_command", True)
            commands_to_run.extend(_get_commands_list_from_settings('BITBUCKET_SERVER.PR_COMMANDS'))
        else:
            commands_to_run.append(data["comment"]["text"])
    elif data["eventKey"] == "repo:refs_changed":
        log_context["event"] = "repo_refs_changed"

        repository_name = data["repository"]["slug"]
        project_name = data["repository"]["project"]["key"]
        bitbucket_server = get_settings().get("BITBUCKET_SERVER.URL")

        # Get commit id
        commit_id = data["changes"][0]["toHash"]

        git_provider = get_git_provider()(bitbucket_server_url=bitbucket_server, workspace_slug=project_name, repo_slug=repository_name)
        if not git_provider:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=json.dumps({"message": "Failed to get git provider"}),
            )
        pr_ids = git_provider.get_pr_nums_from_commit(commit_id)

        # If no PRs are found, return an error
        if not pr_ids:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=json.dumps({"message": "No PRs found for the given commit. Skipping commands."}),
            )
        
        base_url = f"{bitbucket_server}/projects/{project_name}/repos/{repository_name}"
        for pr_id in pr_ids:
            pr_url = f"{base_url}/pull-requests/{pr_id}"
            pr_urls.append(pr_url)
        
        apply_repo_settings(pr_urls[0])
        if get_settings().config.disable_auto_feedback:  # auto commands for PR, and auto feedback is disabled
            get_logger().info(f"Auto feedback is disabled, skipping auto commands for PR {pr_urls[0]}", **log_context)
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content=json.dumps({"message": "Auto feedback is disabled, skipping auto commands for PR"}),
            )
        get_settings().set("config.is_auto_command", True)

        commands_to_run.extend(_get_commands_list_from_settings('BITBUCKET_SERVER.PR_COMMANDS'))
    else:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=json.dumps({"message": "Unsupported event"}),
        )

    async def inner(pr_url):
        try:
            await _run_commands_sequentially(commands_to_run, pr_url, log_context)
        except Exception as e:
            get_logger().error(f"Failed to handle webhook: {e}")

    for pr_url in pr_urls:
        background_tasks.add_task(inner, pr_url)

    return JSONResponse(
        status_code=status.HTTP_200_OK, content=jsonable_encoder({"message": "success"})
    )


async def _run_commands_sequentially(commands: List[str], url: str, log_context: dict):
    get_logger().info(f"Running commands sequentially: {commands}")
    if commands is None:
        return

    for command in commands:
        try:
            body = _process_command(command, url)

            log_context["action"] = body
            log_context["api_url"] = url

            with get_logger().contextualize(**log_context):
                await PRAgent().handle_request(url, body)
        except Exception as e:
            get_logger().error(f"Failed to handle command: {command} , error: {e}")

def _process_command(command: str, url) -> str:
    # don't think we need this
    apply_repo_settings(url)
    # Process the command string
    split_command = command.split(" ")
    command = split_command[0]
    args = split_command[1:]
    # do I need this? if yes, shouldn't this be done in PRAgent?
    other_args = update_settings_from_args(args)
    new_command = ' '.join([command] + other_args)
    return new_command


def _to_list(command_string: str) -> list:
    try:
        # Use ast.literal_eval to safely parse the string into a list
        commands = ast.literal_eval(command_string)
        # Check if the parsed object is a list of strings
        if isinstance(commands, list) and all(isinstance(cmd, str) for cmd in commands):
            return commands
        else:
            raise ValueError("Parsed data is not a list of strings.")
    except (SyntaxError, ValueError, TypeError) as e:
        raise ValueError(f"Invalid command string: {e}")


def _get_commands_list_from_settings(setting_key:str ) -> list:
    try:
        return get_settings().get(setting_key, [])
    except ValueError as e:
        get_logger().error(f"Failed to get commands list from settings {setting_key}: {e}")


@router.get("/")
async def root():
    return {"status": "ok"}


def start():
    app = FastAPI(middleware=[Middleware(RawContextMiddleware)])
    app.include_router(router)
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "3000")))


if __name__ == "__main__":
    start()

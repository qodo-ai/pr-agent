import asyncio
import copy
import os
from typing import Any, Dict

from fastapi import APIRouter, FastAPI, HTTPException, Request, Response
from starlette.background import BackgroundTasks
from starlette.middleware import Middleware
from starlette_context import context
from starlette_context.middleware import RawContextMiddleware

from pr_agent.agent.pr_agent import PRAgent
from pr_agent.config_loader import get_settings, global_settings
from pr_agent.log import LoggingFormat, get_logger, setup_logger
from pr_agent.servers.utils import verify_signature

# Setup logging and router
setup_logger(fmt=LoggingFormat.JSON, level=get_settings().get("CONFIG.LOG_LEVEL", "DEBUG"))
router = APIRouter()

@router.post("/api/v1/gitea_webhooks")
async def handle_gitea_webhooks(background_tasks: BackgroundTasks, request: Request, response: Response):
    """Handle incoming Gitea webhook requests"""
    get_logger().debug("Received a Gitea webhook")

    body = await get_body(request)

    # Set context for the request
    context["settings"] = copy.deepcopy(global_settings)
    context["git_provider"] = {}

    # Handle the webhook in background
    background_tasks.add_task(handle_request, body, event=request.headers.get("X-Gitea-Event", None))
    return {}

async def get_body(request: Request):
    """Parse and verify webhook request body"""
    try:
        body = await request.json()
    except Exception as e:
        get_logger().error("Error parsing request body", artifact={'error': e})
        raise HTTPException(status_code=400, detail="Error parsing request body") from e


    # Verify webhook signature
    webhook_secret = getattr(get_settings().gitea, 'webhook_secret', None)
    if webhook_secret:
        body_bytes = await request.body()
        signature_header = request.headers.get('x-gitea-signature', None)
        if not signature_header:
            get_logger().error("Missing signature header")
            raise HTTPException(status_code=400, detail="Missing signature header")
        
        try:
            verify_signature(body_bytes, webhook_secret, f"sha256={signature_header}")
        except Exception as ex:
            get_logger().error(f"Invalid signature: {ex}")
            raise HTTPException(status_code=401, detail="Invalid signature")

    return body

async def handle_request(body: Dict[str, Any], event: str):
    """Process Gitea webhook events"""
    action = body.get("action")
    if not action:
        get_logger().debug("No action found in request body")
        return {}

    agent = PRAgent()

    # Handle different event types
    if event == "pull_request":
        if action in ["opened", "reopened", "synchronized"]:
            await handle_pr_event(body, event, action, agent)
    elif event == "issue_comment":
        if action == "created":
            await handle_comment_event(body, event, action, agent)

    return {}

async def handle_pr_event(body: Dict[str, Any], event: str, action: str, agent: PRAgent):
    """Handle pull request events"""
    pr = body.get("pull_request", {})
    if not pr:
        return

    api_url = pr.get("url")
    if not api_url:
        return

    # Handle PR based on action
    if action in ["opened", "reopened"]:
        commands = get_settings().get("gitea.pr_commands", [])
        for command in commands:
            await agent.handle_request(api_url, command)
    elif action == "synchronized":
        # Handle push to PR
        await agent.handle_request(api_url, "/review --incremental")

async def handle_comment_event(body: Dict[str, Any], event: str, action: str, agent: PRAgent):
    """Handle comment events"""
    comment = body.get("comment", {})
    if not comment:
        return

    comment_body = comment.get("body", "")
    if not comment_body or not comment_body.startswith("/"):
        return

    pr_url = body.get("pull_request", {}).get("url")
    if not pr_url:
        return

    await agent.handle_request(pr_url, comment_body)

# FastAPI app setup
middleware = [Middleware(RawContextMiddleware)]
app = FastAPI(middleware=middleware)
app.include_router(router)

def start():
    """Start the Gitea webhook server"""
    port = int(os.environ.get("PORT", "3000"))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    start()

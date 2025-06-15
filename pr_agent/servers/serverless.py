from fastapi import FastAPI
from mangum import Mangum
from starlette.middleware import Middleware
from starlette_context.middleware import RawContextMiddleware

try:
    from pr_agent.config_loader import apply_secrets_manager_config
    apply_secrets_manager_config()
except Exception as e:
    try:
        from pr_agent.log import get_logger
        get_logger().debug(f"AWS Secrets Manager initialization failed, falling back to environment variables: {e}")
    except:
        # Fail completely silently if log module is not available
        pass

def _create_handler(router):
    middleware = [Middleware(RawContextMiddleware)]
    app = FastAPI(middleware=middleware)
    app.include_router(router)
    return Mangum(app, lifespan="off")

def serverless_github(event, context):
    from pr_agent.servers.github_app import router
    handler = _create_handler(router)
    return handler(event, context)

def serverless_gitlab(event, context):
    from pr_agent.servers.gitlab_webhook import router
    handler = _create_handler(router)
    return handler(event, context)

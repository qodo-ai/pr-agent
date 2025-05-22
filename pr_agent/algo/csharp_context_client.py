# pr_agent/algo/csharp_context_client.py
import httpx
from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger

import ssl # Import the ssl module

async def _login_and_get_service_token(client: httpx.AsyncClient, service_settings: dict) -> str | None:
    """
    Logs into the C# context service and returns an API token.
    """
    login_url = service_settings.base_url.rstrip('/') + "/api/auth/login"
    username = service_settings.get("username")
    password = service_settings.get("password")

    if not username or not password:
        get_logger().error("C# context service username or password not configured in settings.")
        return None

    login_payload = {"username": username, "password": password}
    
    get_logger().info(f"Attempting login to C# context service at: {login_url} for user: {username}")
    try:
        response = await client.post(login_url, json=login_payload)
        response.raise_for_status() # Will raise an exception for 4xx/5xx errors
        token_data = response.json()
        service_token = token_data.get("token")
        if not service_token:
            get_logger().error("Token not found in C# context service login response.", artifact=token_data)
            return None
        get_logger().info("Successfully logged into C# context service and obtained token.")
        return service_token
    except httpx.HTTPStatusError as e:
        get_logger().error(f"Login to C# context service failed: {e.response.status_code} - {e.response.text}")
        return None
    except Exception as e:
        get_logger().error(f"Exception during C# context service login: {e}", exc_info=True)
        return None
    
async def get_csharp_minimal_context(owner: str, repo_name: str, pr_number: int, github_token_for_repo_access: str) -> dict | None:
    service_settings = get_settings().csharp_code_context_service
    if not service_settings.get("enabled", False):
        get_logger().debug("C# context service is disabled in configuration.")
        return None

    base_url = service_settings.base_url.rstrip('/')
    analyze_endpoint = f"{base_url}/api/analyze"

    if not github_token_for_repo_access: # This is the GitHub token for your service to access the repo
        get_logger().error("GitHub token (for repo access by C# service) is not available.")
        return None

    # For local development with self-signed certificates
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with httpx.AsyncClient(timeout=service_settings.timeout, verify=ssl_context) as client:
        # Login to get the service API token
        service_api_token = await _login_and_get_service_token(client, service_settings)
        if not service_api_token:
            get_logger().error("Failed to obtain API token from C# context service. Cannot proceed with analysis.")
            return None

        headers = {"Authorization": f"Bearer {service_api_token}"}

        payload_for_analysis = {
            "token": github_token_for_repo_access, # GitHub token for the service to use for repo access
            "owner": owner,
            "repo": repo_name,
            "prNumber": pr_number,
            "depth": service_settings.default_depth,
            "mode": service_settings.default_mode
        }

        log_payload_safe = payload_for_analysis.copy()
        log_payload_safe["token"] = "****" # Mask GitHub token for logging
        get_logger().info(f"Calling C# Context Service for analysis: {analyze_endpoint} with payload: {log_payload_safe}, auth header keys: {list(headers.keys())}")

        try:
            response = await client.post(analyze_endpoint, json=payload_for_analysis, headers=headers)
            response.raise_for_status()

            api_response_data = response.json()
            logs = api_response_data.get("logs", [])
            for log_entry in logs:
                get_logger().info(f"[CodeContextServiceAPI] {log_entry}")

            analysis_result = api_response_data.get("result", None)

            if isinstance(analysis_result, dict):
                get_logger().info(f"Successfully received context for {len(analysis_result)} C# file(s) from service.")
                return analysis_result
            elif analysis_result is None:
                get_logger().info("C# context service returned no result data for analysis.")
                return {}
            else:
                get_logger().warning(f"C# CodeContextService API (analysis) returned unexpected format for 'result'. Expected dict, got {type(analysis_result)}. Raw: {analysis_result}")
                return None

        except httpx.HTTPStatusError as e:
            get_logger().error(f"HTTP error from C# CodeContextService (analysis): {e.response.status_code} - {e.response.text}")
            return None
        except httpx.RequestError as e:
            get_logger().error(f"Request error calling C# CodeContextService (analysis): {e}")
            return None
        except Exception as e:
            get_logger().error(f"Error processing C# CodeContextService (analysis) response: {e}", exc_info=True)
            return None
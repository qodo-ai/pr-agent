"""
Configuration loader from .env files or Google Cloud Secret Manager.
Python equivalent of @workiz/config-loader

If .env.<environment> exists in the root directory, loads variables from that file.
Otherwise, loads from Google Cloud Secret Manager.

Secret naming convention: <environment>-<service-name>
Examples: staging-pr-agent, prod-pr-agent
"""

import asyncio
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

SERVICE_NAME = "pr-agent"


def _parse_env_content(content: str) -> dict[str, str]:
    """Parse .env file content into a dictionary."""
    config = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' in line:
            key, _, value = line.partition('=')
            key = key.strip()
            value = value.strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            elif value.startswith("'") and value.endswith("'"):
                value = value[1:-1]
            config[key] = value
    return config


def _get_env_file_path(service_root: Path) -> Path:
    """Get the path to the environment-specific .env file."""
    env_name = os.environ.get('NODE_ENV', 'development')
    return service_root / f'.env.{env_name}'


class ConfigLoadError(Exception):
    """Raised when configuration cannot be loaded."""
    pass


def _get_dotenv_config(env_file_path: Path) -> dict[str, str]:
    """Load configuration from a .env file.
    
    Raises:
        ConfigLoadError: If the file cannot be read.
    """
    try:
        content = env_file_path.read_text()
        return _parse_env_content(content)
    except PermissionError as e:
        raise ConfigLoadError(f"Permission denied reading config file: {env_file_path}") from e
    except IOError as e:
        raise ConfigLoadError(f"Failed to read config file {env_file_path}: {e}") from e


SECRET_MANAGER_TIMEOUT_SECONDS = float(os.environ.get('SECRET_MANAGER_TIMEOUT', '30'))


def _get_secret_manager_config(
    project_id: str,
    service_name: str,
    env_name_override: str | None = None
) -> dict[str, str]:
    """Load configuration from Google Cloud Secret Manager.
    
    Timeout is configurable via SECRET_MANAGER_TIMEOUT env var (default: 30s).
    
    Raises:
        ConfigLoadError: If secrets cannot be fetched (auth, network, not found).
    """
    try:
        from google.api_core import retry
        from google.api_core.exceptions import GoogleAPIError, NotFound, PermissionDenied
        from google.cloud import secretmanager
    except ImportError as e:
        raise ConfigLoadError(
            "google-cloud-secret-manager package not installed. "
            "Install with: pip install google-cloud-secret-manager"
        ) from e

    try:
        client = secretmanager.SecretManagerServiceClient()
    except Exception as e:
        raise ConfigLoadError(
            f"Failed to create Secret Manager client. Check GCP credentials: {e}"
        ) from e

    node_env = os.environ.get('NODE_ENV', 'development')
    env_name = env_name_override if env_name_override else ('prod' if node_env == 'production' else node_env)

    secrets_name = f'{env_name}-{service_name}'

    staging_namespace = os.environ.get('STAGING_ENV_NAMESPACE')
    temp_cloud_env_secret = f'{staging_namespace}-{service_name}' if staging_namespace else None

    def fetch_secrets(name: str) -> dict[str, str]:
        secret_path = f'projects/{project_id}/secrets/{name}/versions/latest'
        try:
            response = client.access_secret_version(
                request={'name': secret_path},
                timeout=SECRET_MANAGER_TIMEOUT_SECONDS,
                retry=retry.Retry(
                    initial=1.0,
                    maximum=10.0,
                    multiplier=2.0,
                    deadline=SECRET_MANAGER_TIMEOUT_SECONDS,
                ),
            )
        except NotFound:
            raise ConfigLoadError(
                f"Secret not found: {name}. "
                f"Create it in GCP project '{project_id}' or check the secret name."
            )
        except PermissionDenied as e:
            raise ConfigLoadError(
                f"Permission denied accessing secret '{name}'. "
                f"Check service account permissions: {e}"
            )
        except GoogleAPIError as e:
            raise ConfigLoadError(f"Failed to fetch secret '{name}': {e}")
        except Exception as e:
            raise ConfigLoadError(
                f"Unexpected error fetching secret '{name}': {type(e).__name__}: {e}"
            )

        if not response.payload or not response.payload.data:
            raise ConfigLoadError(f'Secret exists but has no data: {name}')

        content = response.payload.data.decode('UTF-8')
        return _parse_env_content(content)

    config = fetch_secrets(secrets_name)

    if temp_cloud_env_secret:
        try:
            cloud_env_config = fetch_secrets(temp_cloud_env_secret)
            config = {**config, **cloud_env_config}
        except ConfigLoadError:
            logger.debug(f"Optional namespace secret not found: {temp_cloud_env_secret}")

    return config


def load_config_sync(
    project_id: str,
    service_name: str = SERVICE_NAME,
    env_name_override: str | None = None,
    service_root: Path | None = None,
    update_environ: bool = True
) -> dict[str, str]:
    """
    Load configuration from .env file or Google Cloud Secret Manager (synchronous).
    
    This is the primary config loading function. Use this at application startup
    before the async event loop is running.
    
    SIDE EFFECT: By default, this updates os.environ with loaded values.
    Existing environment variables with the same keys WILL BE OVERWRITTEN.
    Set update_environ=False to disable this behavior.
    
    Args:
        project_id: Google Cloud project ID
        service_name: Name of the service (defaults to 'pr-agent')
        env_name_override: Optional override for the environment name
        service_root: Root directory of the service (defaults to project root)
        update_environ: If True (default), updates os.environ with loaded config.
                       Set to False to only return the config dict without side effects.
    
    Returns:
        Dictionary of configuration values
    """
    if service_root is None:
        service_root = Path(__file__).parent.parent.parent

    env_file_path = _get_env_file_path(service_root)

    if env_file_path.exists():
        logger.info("Loading config from file", extra={"context": {"path": str(env_file_path)}})
        config = _get_dotenv_config(env_file_path)
    else:
        secret_name = f'{os.environ.get("NODE_ENV", "development")}-{service_name}'
        logger.info("Loading config from Secret Manager", extra={"context": {"secret": secret_name}})
        config = _get_secret_manager_config(project_id, service_name, env_name_override)

    if update_environ:
        overwritten_keys = [k for k in config if k in os.environ and os.environ[k] != config[k]]
        if overwritten_keys:
            logger.warning(
                "Config loading will overwrite existing environment variables",
                extra={"context": {"overwritten_keys": overwritten_keys}}
            )
        os.environ.update(config)
        logger.debug("Config loaded and applied to os.environ", extra={"context": {"keys_count": len(config)}})
    else:
        logger.debug("Config loaded (os.environ not modified)", extra={"context": {"keys_count": len(config)}})

    return config


async def load_config(
    project_id: str,
    service_name: str = SERVICE_NAME,
    env_name_override: str | None = None,
    service_root: Path | None = None,
    update_environ: bool = True
) -> dict[str, str]:
    """
    Load configuration from .env file or Google Cloud Secret Manager (async).
    
    Runs the synchronous config loading in a thread pool to avoid blocking
    the event loop. Use this when you need to reload config during runtime.
    
    For startup, prefer load_config_sync() before the event loop starts.
    
    SIDE EFFECT: By default, this updates os.environ with loaded values.
    Set update_environ=False to disable this behavior.
    
    Args:
        project_id: Google Cloud project ID
        service_name: Name of the service (defaults to 'pr-agent')
        env_name_override: Optional override for the environment name
        service_root: Root directory of the service (defaults to project root)
        update_environ: If True (default), updates os.environ with loaded config.
    
    Returns:
        Dictionary of configuration values
    
    Usage:
        config = await load_config('workiz-development')
        config = await load_config('workiz-development', update_environ=False)  # No side effects
    """
    return await asyncio.to_thread(
        load_config_sync,
        project_id,
        service_name,
        env_name_override,
        service_root,
        update_environ
    )


def load_local_env(update_environ: bool = True) -> dict[str, str]:
    """
    Load configuration from .env file only (for local development).
    Does not fall back to Secret Manager.
    
    SIDE EFFECT: By default, this updates os.environ with loaded values.
    Set update_environ=False to disable this behavior.
    
    Args:
        update_environ: If True (default), updates os.environ with loaded config.
    
    Returns:
        Dictionary of configuration values
    """
    service_root = Path(__file__).parent.parent.parent
    env_file = service_root / '.env'
    
    if env_file.exists():
        logger.info("Loading config from local .env", extra={"context": {"path": str(env_file)}})
        config = _parse_env_content(env_file.read_text())
        if update_environ:
            os.environ.update(config)
        return config
    
    logger.info("No .env file found, using existing environment variables")
    return {}


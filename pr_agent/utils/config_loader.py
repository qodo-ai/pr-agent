"""
Configuration loader from .env files or Google Cloud Secret Manager.
Python equivalent of @workiz/config-loader

If .env.<environment> exists in the root directory, loads variables from that file.
Otherwise, loads from Google Cloud Secret Manager.

Secret naming convention: <environment>-<service-name>
Examples: staging-pr-agent, prod-pr-agent
"""

import os
from pathlib import Path

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


def _get_dotenv_config(env_file_path: Path) -> dict[str, str]:
    """Load configuration from a .env file."""
    content = env_file_path.read_text()
    return _parse_env_content(content)


def _get_secret_manager_config(
    project_id: str,
    service_name: str,
    env_name_override: str | None = None
) -> dict[str, str]:
    """Load configuration from Google Cloud Secret Manager."""
    from google.cloud import secretmanager

    client = secretmanager.SecretManagerServiceClient()

    node_env = os.environ.get('NODE_ENV', 'development')
    env_name = env_name_override if env_name_override else ('prod' if node_env == 'production' else node_env)

    secrets_name = f'{env_name}-{service_name}'

    staging_namespace = os.environ.get('STAGING_ENV_NAMESPACE')
    temp_cloud_env_secret = f'{staging_namespace}-{service_name}' if staging_namespace else None

    def fetch_secrets(name: str) -> dict[str, str]:
        secret_path = f'projects/{project_id}/secrets/{name}/versions/latest'
        response = client.access_secret_version(request={'name': secret_path})

        if not response.payload or not response.payload.data:
            raise ValueError(f'No data loaded from Google Secrets: {name}')

        content = response.payload.data.decode('UTF-8')
        return _parse_env_content(content)

    config = fetch_secrets(secrets_name)

    if temp_cloud_env_secret:
        cloud_env_config = fetch_secrets(temp_cloud_env_secret)
        config = {**config, **cloud_env_config}

    return config


async def load_config(
    project_id: str,
    service_name: str = SERVICE_NAME,
    env_name_override: str | None = None,
    service_root: Path | None = None
) -> dict[str, str]:
    """
    Load configuration from .env file or Google Cloud Secret Manager.
    
    Args:
        project_id: Google Cloud project ID
        service_name: Name of the service (defaults to 'pr-agent')
        env_name_override: Optional override for the environment name
        service_root: Root directory of the service (defaults to project root)
    
    Returns:
        Dictionary of configuration values
    
    Usage:
        await load_config('workiz-development')
    """
    if service_root is None:
        service_root = Path(__file__).parent.parent.parent

    env_file_path = _get_env_file_path(service_root)

    if env_file_path.exists():
        print(f'Loading config from {env_file_path}')
        config = _get_dotenv_config(env_file_path)
    else:
        print(f'Loading config from Google Secret Manager: {os.environ.get("NODE_ENV", "development")}-{service_name}')
        config = _get_secret_manager_config(project_id, service_name, env_name_override)

    os.environ.update(config)

    return config


def load_config_sync(
    project_id: str,
    service_name: str = SERVICE_NAME,
    env_name_override: str | None = None,
    service_root: Path | None = None
) -> dict[str, str]:
    """
    Synchronous version of load_config.
    
    Args:
        project_id: Google Cloud project ID
        service_name: Name of the service (defaults to 'pr-agent')
        env_name_override: Optional override for the environment name
        service_root: Root directory of the service (defaults to project root)
    
    Returns:
        Dictionary of configuration values
    """
    if service_root is None:
        service_root = Path(__file__).parent.parent.parent

    env_file_path = _get_env_file_path(service_root)

    if env_file_path.exists():
        print(f'Loading config from {env_file_path}')
        config = _get_dotenv_config(env_file_path)
    else:
        print(f'Loading config from Google Secret Manager: {os.environ.get("NODE_ENV", "development")}-{service_name}')
        config = _get_secret_manager_config(project_id, service_name, env_name_override)

    os.environ.update(config)

    return config


def load_local_env() -> dict[str, str]:
    """
    Load configuration from .env file only (for local development).
    Does not fall back to Secret Manager.
    """
    service_root = Path(__file__).parent.parent.parent
    env_file = service_root / '.env'
    
    if env_file.exists():
        print(f'Loading config from {env_file}')
        config = _parse_env_content(env_file.read_text())
        os.environ.update(config)
        return config
    
    print('No .env file found, using existing environment variables')
    return {}


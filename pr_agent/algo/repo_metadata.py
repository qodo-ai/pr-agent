from __future__ import annotations

from typing import TYPE_CHECKING

from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger

if TYPE_CHECKING:
    from pr_agent.git_providers.git_provider import GitProvider


_DEFAULT_FILE_LIST = [
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".github/copilot-instructions.md",
    "best_practices.md",
]


def _get_config() -> dict:
    cfg = get_settings().config
    enabled = cfg.get("add_repo_metadata", False)
    file_list = cfg.get("add_repo_metadata_file_list", _DEFAULT_FILE_LIST)
    max_chars_per_file = int(cfg.get("repo_metadata_max_chars_per_file", 4000))
    max_files = int(cfg.get("repo_metadata_max_files", 20))
    max_total_chars = int(cfg.get("repo_metadata_max_total_chars", 20000))
    return {
        "enabled": enabled,
        "file_list": file_list,
        "max_chars_per_file": max_chars_per_file,
        "max_files": max_files,
        "max_total_chars": max_total_chars,
    }


def _read_file(git_provider: "GitProvider", file_path: str, branch: str) -> str | None:
    try:
        content = git_provider.get_pr_file_content(file_path, branch)
        return content if content else None
    except Exception as e:
        get_logger().debug(
            f"Failed to read repo metadata file '{file_path}' from branch '{branch}'",
            artifact={"error": str(e)},
        )
        return None


def load_repo_metadata(git_provider: "GitProvider") -> str:
    cfg = _get_config()
    if not cfg["enabled"]:
        return ""

    if not hasattr(git_provider, "get_pr_base_branch_name"):
        get_logger().debug(
            "Git provider does not support get_pr_base_branch_name; skipping repo metadata"
        )
        return ""

    base_branch = git_provider.get_pr_base_branch_name()
    if not base_branch:
        get_logger().debug("No base branch available; skipping repo metadata")
        return ""

    if not hasattr(git_provider, "get_pr_file_content"):
        get_logger().debug(
            "Git provider does not support get_pr_file_content; skipping repo metadata"
        )
        return ""

    file_list = cfg["file_list"]
    max_chars_per_file = cfg["max_chars_per_file"]
    max_files = cfg["max_files"]
    max_total_chars = cfg["max_total_chars"]

    parts: list[str] = []
    loaded_count = 0

    for file_path in file_list:
        if loaded_count >= max_files:
            get_logger().debug(f"Reached max_files limit ({max_files}); stopping metadata loading")
            break

        try:
            content = _read_file(git_provider, file_path, base_branch)
        except Exception as e:
            get_logger().warning(
                f"Unexpected error reading metadata file '{file_path}'",
                artifact={"error": str(e)},
            )
            continue

        if content is None:
            continue

        if len(content) > max_chars_per_file:
            content = content[:max_chars_per_file]

        loaded_count += 1
        parts.append(f"### File: `{file_path}`\n\n```markdown\n{content}\n```")

    if not parts:
        get_logger().debug("No repo metadata files found")
        return ""

    result = "\n\n".join(parts)

    if len(result) > max_total_chars:
        result = result[:max_total_chars]
        get_logger().debug(
            f"Repo metadata truncated to {max_total_chars} total characters"
        )

    get_logger().info(
        f"Loaded repo metadata: {loaded_count} file(s), {len(result)} characters total"
    )
    return result

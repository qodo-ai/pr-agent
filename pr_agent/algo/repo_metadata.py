from __future__ import annotations

import posixpath
import urllib.parse
from typing import TYPE_CHECKING

from pr_agent.config_loader import get_settings
from pr_agent.log import get_logger

if TYPE_CHECKING:
    from pr_agent.git_providers.git_provider import GitProvider


_DEFAULT_FILE_LIST = [
    "AGENTS.md",
    "QODO.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".github/copilot-instructions.md",
    "best_practices.md",
]


def _is_safe_repo_file_path(file_path: str) -> bool:
    """Reject absolute paths, ``..`` traversal, backslashes, and percent-encoded bypasses."""
    if not file_path or not file_path.strip():
        return False

    file_path = urllib.parse.unquote(file_path)
    if "%" in file_path:
        return False

    if file_path.startswith(("/", "\\")) or posixpath.isabs(file_path):
        return False
    if len(file_path) >= 2 and file_path[1] == ":":
        return False
    if "\\" in file_path:
        return False

    segments = file_path.replace("\\", "/").split("/")
    if ".." in segments:
        return False

    normalized = posixpath.normpath(file_path)
    if normalized.startswith("..") or "/.." in normalized:
        return False

    return True


def _get_config() -> dict:
    cfg = get_settings().config
    enabled = cfg.get("add_repo_metadata", False)
    file_list = cfg.get("add_repo_metadata_file_list", _DEFAULT_FILE_LIST) or _DEFAULT_FILE_LIST
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


def _truncate_at_newline(content: str, max_chars: int) -> str:
    if len(content) <= max_chars:
        return content
    truncated = content[:max_chars]
    last_newline = truncated.rfind("\n")
    return truncated[:last_newline] if last_newline != -1 else truncated


def load_repo_metadata(git_provider: "GitProvider") -> str:
    if hasattr(git_provider, "_repo_metadata"):
        return git_provider._repo_metadata

    cfg = _get_config()
    if not cfg["enabled"]:
        git_provider._repo_metadata = ""
        return ""

    if not hasattr(git_provider, "get_pr_base_branch_name"):
        get_logger().debug(
            "Git provider does not support get_pr_base_branch_name; skipping repo metadata"
        )
        git_provider._repo_metadata = ""
        return ""

    base_branch = git_provider.get_pr_base_branch_name()
    if not base_branch:
        get_logger().debug("No base branch available; skipping repo metadata")
        git_provider._repo_metadata = ""
        return ""

    if not hasattr(git_provider, "get_pr_file_content"):
        get_logger().debug(
            "Git provider does not support get_pr_file_content; skipping repo metadata"
        )
        git_provider._repo_metadata = ""
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

        if not _is_safe_repo_file_path(file_path):
            get_logger().warning(f"Skipping unsafe metadata file path: '{file_path}'")
            continue

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
            content = _truncate_at_newline(content, max_chars_per_file)

        loaded_count += 1
        parts.append(f"### File: `{file_path}`\n\n```markdown\n{content}\n```")

    if not parts:
        get_logger().debug("No repo metadata files found")
        git_provider._repo_metadata = ""
        return ""

    result = "\n\n".join(parts)

    if len(result) > max_total_chars:
        result = _truncate_at_newline(result, max_total_chars)
        get_logger().debug(
            f"Repo metadata truncated to {max_total_chars} total characters"
        )

    git_provider._repo_metadata = result
    get_logger().info(
        f"Loaded repo metadata: {loaded_count} file(s), {len(result)} characters total"
    )
    return result

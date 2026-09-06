"""The PR read tools: one definition of the contracts and one implementation of the
behavior, shared by every runtime that reviews a pull request.

The tools are backed by the ``GitProvider`` API rather than a checkout, so a review runs
in the same server model as the rest of PR-Agent and needs no clone. Provider calls are
blocking network I/O, so each runs in a worker thread; a round's calls therefore overlap
instead of queueing.

Everything these tools return is written by the PR's author, so every result goes out
through :data:`~pr_agent.algo.review_loop.fencing.PR_CONTENT_FENCE`.
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from pydantic import Field

from pr_agent.algo.file_filter import filter_ignored
from pr_agent.algo.review_loop.execution import (
    ArgumentModel,
    Handler,
    ToolExecutor,
    ToolOutcome,
    parse_argument,
)
from pr_agent.algo.review_loop.fencing import MAX_FENCED_CHARS, PR_CONTENT_FENCE
from pr_agent.log import get_logger


def _is_ignored(file_path: str) -> bool:
    """Whether the operator's `[ignore]` patterns exclude this path.

    `filter_ignored` is the single source of that truth -- it assembles the regex and glob
    settings and the generated-code lists -- and it filters objects with a `filename`, so
    the path is wrapped in one rather than reimplementing the matching here.
    """

    class _Named:
        filename = file_path

    candidate = _Named()
    return not filter_ignored([candidate], "github")


LIST_CHANGED_FILES = "list_changed_files"
GET_FILE_DIFF = "get_file_diff"
READ_FILE = "read_file"

# ``read_file`` without a range reads this many lines; a range may span up to MAX.
DEFAULT_READ_LINES = 400
MAX_READ_LINES = 2000
# A pull request can touch thousands of files. The listing names this many and says how
# many it left out, so the model asks for a narrower view rather than reading a truncated
# list as the whole change.
MAX_LISTED_FILES = 300


class _FilePath(ArgumentModel):
    file_path: str = Field(min_length=1, max_length=500)


class _ReadFileArgs(ArgumentModel):
    file_path: str = Field(min_length=1, max_length=500)
    start_line: Optional[int] = Field(default=None, ge=1)
    end_line: Optional[int] = Field(default=None, ge=1)


def build_pr_tool_definitions() -> list[dict[str, Any]]:
    """The three read contracts, in the order a review uses them."""
    return [
        {
            "name": LIST_CHANGED_FILES,
            "description": (
                "List the files this pull request changes, with how each was changed and "
                "how many lines it added and removed. Call this first: it is the map of "
                "the change, and every other tool takes a path from it."
            ),
            "input_schema": {"type": "object", "properties": {}, "required": []},
        },
        {
            "name": GET_FILE_DIFF,
            "description": (
                "The diff hunks for one changed file, with line numbers. This is what the "
                "pull request actually changed in that file, and it is what a finding must "
                "be grounded in. Use it on every file you intend to say anything about."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": f"A path exactly as {LIST_CHANGED_FILES} reported it.",
                    }
                },
                "required": ["file_path"],
            },
        },
        {
            "name": READ_FILE,
            "description": (
                "Numbered lines of a file as it stands after this pull request. Use it when "
                "the diff alone cannot settle a question — what a caller passes, whether a "
                "name is defined elsewhere in the file, what the function around a hunk "
                "does. Files the pull request did not change can be read too, at the base "
                "revision, which is enough to check a caller or an existing helper."
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Repository-relative path."},
                    "start_line": {
                        "type": "integer",
                        "description": f"First line, 1-based; defaults to 1. At most "
                        f"{MAX_READ_LINES} lines come back in one call.",
                    },
                    "end_line": {"type": "integer", "description": "Last line, inclusive."},
                },
                "required": ["file_path"],
            },
        },
    ]


class PRToolExecutor(ToolExecutor):
    """The three read tools over one ``GitProvider``.

    ``get_diff_files`` is fetched once and reused: a review calls it on nearly every
    round, the provider re-fetches on every call, and the diff of a pull request does not
    move while one review runs. Only a successful fetch is cached, so a transient outage
    does not pin an empty file list for the rest of the review.
    """

    fence = PR_CONTENT_FENCE

    def __init__(self, git_provider: Any, *, max_fenced_chars: int = MAX_FENCED_CHARS) -> None:
        super().__init__(max_fenced_chars=max_fenced_chars)
        self._git_provider = git_provider
        self._diff_files: list[Any] | None = None
        self._file_bodies: dict[str, list[str] | None] = {}

    def handlers(self) -> dict[str, Handler]:
        return {
            LIST_CHANGED_FILES: self._list_changed_files,
            GET_FILE_DIFF: self._get_file_diff,
            READ_FILE: self._read_file,
        }

    def tool_definitions(self) -> list[dict[str, Any]]:
        return build_pr_tool_definitions()

    async def dispatch(self, name: str, tool_input: dict[str, Any]) -> ToolOutcome:
        handler = self.handlers().get(name)
        if handler is None:
            known = ", ".join(self.handlers())
            return ToolOutcome.error(f"Unknown tool: {name}. The tools here are: {known}.")
        return await handler(tool_input)

    # -- provider reads ---------------------------------------------------------------

    async def _diffs(self) -> list[Any]:
        if self._diff_files is None:
            self._diff_files = list(await asyncio.to_thread(self._git_provider.get_diff_files) or [])
        return self._diff_files

    async def _find(self, file_path: str) -> Any | None:
        # `removeprefix`, not `lstrip("./")`: as a strip set that would eat every leading
        # dot and slash, turning `.github/workflows/ci.yml` into `github/workflows/ci.yml`
        # and making every dotfile in the pull request unfindable.
        wanted = file_path.strip().removeprefix("./")
        for patch in await self._diffs():
            if (patch.filename or "").strip() == wanted:
                return patch
        return None

    async def _not_found(self, file_path: str) -> ToolOutcome:
        names = [patch.filename for patch in await self._diffs()][:20]
        listed = ", ".join(names) or "none"
        return ToolOutcome.error(
            f"'{file_path}' is not one of the files this pull request changes. "
            f"Call {LIST_CHANGED_FILES} for the paths; some of them are: {listed}."
        )

    # -- handlers ---------------------------------------------------------------------

    async def _list_changed_files(self, _args: dict[str, Any]) -> ToolOutcome:
        diffs = await self._diffs()
        files = [
            {
                "file_path": patch.filename,
                "change": getattr(patch.edit_type, "name", str(patch.edit_type)).lower(),
                "added_lines": patch.num_plus_lines,
                "deleted_lines": patch.num_minus_lines,
                "language": patch.language or "",
                "previous_path": patch.old_filename or "",
                "full_content_available": bool(patch.head_file) and patch.head_file_is_complete,
            }
            for patch in diffs[:MAX_LISTED_FILES]
        ]
        payload: dict[str, Any] = {"changed_files": files, "total_changed_files": len(diffs)}
        if len(diffs) > MAX_LISTED_FILES:
            payload["note"] = (
                f"{len(diffs) - MAX_LISTED_FILES} more files are not listed. Review the ones "
                "here and say in your answer that the pull request is larger than one review "
                "can cover."
            )
        return self._fenced(payload)

    async def _get_file_diff(self, args: dict[str, Any]) -> ToolOutcome:
        file_path = parse_argument(_FilePath, args).file_path
        patch = await self._find(file_path)
        if patch is None:
            return await self._not_found(file_path)
        if not patch.patch:
            return ToolOutcome(
                f"{file_path} has no textual diff — it is binary, empty, or a pure rename."
            )
        return self._fenced({"file_path": patch.filename, "diff": patch.patch})

    async def _body(self, file_path: str) -> list[str] | None:
        """The file's lines at head when the pull request changed it, else at the base
        revision; None when neither is available. Cached per review, misses included, so
        a model that asks twice for a file that does not exist pays one provider call."""
        if file_path in self._file_bodies:
            return self._file_bodies[file_path]
        patch = await self._find(file_path)
        text: str | None = None
        if patch is not None and patch.head_file and patch.head_file_is_complete:
            text = patch.head_file
        elif _is_ignored(file_path):
            # The changed-file list is already `[ignore]`-filtered by the provider, but the
            # fallback below fetches any path in the repository. Without this check a model
            # could read `.env`, a vendored secret, or anything else the operator excluded,
            # simply by naming it -- the one hole in the filter the rest of the tool honors.
            get_logger().info(f"read_file refused an ignored path: {file_path}")
            text = None
        else:
            try:
                text = await asyncio.to_thread(self._git_provider.get_repo_file_content, file_path)
            except Exception as error:  # an unreadable file is a result, not an outage
                get_logger().warning(f"read_file could not fetch {file_path}: {error}")
                text = None
        lines = text.splitlines() if text else None
        self._file_bodies[file_path] = lines
        return lines

    async def _read_file(self, args: dict[str, Any]) -> ToolOutcome:
        parsed = parse_argument(_ReadFileArgs, args)
        lines = await self._body(parsed.file_path)
        if not lines:
            return ToolOutcome.error(
                f"'{parsed.file_path}' could not be read: it does not exist at this revision, "
                "is binary, or the provider returned no content."
            )
        start = parsed.start_line or 1
        if start > len(lines):
            return ToolOutcome.error(
                f"{parsed.file_path} has {len(lines)} lines; line {start} is past the end."
            )
        end = parsed.end_line or start + DEFAULT_READ_LINES - 1
        end = min(max(end, start), len(lines), start + MAX_READ_LINES - 1)
        numbered = "\n".join(f"{n}: {lines[n - 1]}" for n in range(start, end + 1))
        payload = {
            "file_path": parsed.file_path,
            "lines": f"{start}-{end} of {len(lines)}",
            "content": numbered,
        }
        return self._fenced(payload)

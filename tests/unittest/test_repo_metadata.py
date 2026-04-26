from __future__ import annotations

from pr_agent.algo.repo_metadata import (
    _DEFAULT_FILE_LIST,
    _get_config,
    _is_safe_repo_file_path,
    _read_file,
    load_repo_metadata,
)
from pr_agent.config_loader import global_settings


class TestGetConfig:
    def test_default_file_list(self):
        assert _DEFAULT_FILE_LIST == [
            "AGENTS.md",
            "QODO.md",
            "CLAUDE.md",
            "GEMINI.md",
            ".github/copilot-instructions.md",
            "best_practices.md",
        ]

    def test_config_disabled_by_default(self, monkeypatch):
        monkeypatch.setattr(global_settings.config, "add_repo_metadata", False)
        cfg = _get_config()
        assert cfg["enabled"] is False

    def test_config_enabled(self, monkeypatch):
        monkeypatch.setattr(global_settings.config, "add_repo_metadata", True)
        cfg = _get_config()
        assert cfg["enabled"] is True

    def test_null_file_list_fallback(self, monkeypatch):
        monkeypatch.setattr(global_settings.config, "add_repo_metadata_file_list", None)
        cfg = _get_config()
        assert cfg["file_list"] == _DEFAULT_FILE_LIST

    def test_custom_file_list(self, monkeypatch):
        custom = ["CUSTOM.md"]
        monkeypatch.setattr(global_settings.config, "add_repo_metadata_file_list", custom)
        cfg = _get_config()
        assert cfg["file_list"] == custom

    def test_custom_max_chars(self, monkeypatch):
        monkeypatch.setattr(global_settings.config, "repo_metadata_max_chars_per_file", 8000)
        monkeypatch.setattr(global_settings.config, "repo_metadata_max_files", 50)
        monkeypatch.setattr(global_settings.config, "repo_metadata_max_total_chars", 40000)
        cfg = _get_config()
        assert cfg["max_chars_per_file"] == 8000
        assert cfg["max_files"] == 50
        assert cfg["max_total_chars"] == 40000


class TestReadFile:
    def test_returns_content(self):
        mock_gp = type("MockGP", (), {"get_pr_file_content": lambda self, fp, br: "hello world"})()
        assert _read_file(mock_gp, "AGENTS.md", "main") == "hello world"

    def test_returns_none_on_empty(self):
        mock_gp = type("MockGP", (), {"get_pr_file_content": lambda self, fp, br: ""})()
        assert _read_file(mock_gp, "AGENTS.md", "main") is None

    def test_returns_none_on_exception(self):
        mock_gp = type("MockGP", (), {"get_pr_file_content": lambda self, fp, br: (_ for _ in ()).throw(RuntimeError("fail"))})()
        assert _read_file(mock_gp, "AGENTS.md", "main") is None


class TestLoadRepoMetadata:
    def _make_mock_provider(self, files: dict[str, str]) -> object:
        mp = type("MockGP", (), {})()
        mp.get_pr_base_branch_name = lambda: "main"
        mp.get_pr_file_content = lambda fp, br: files.get(fp, "")
        return mp

    def test_disabled_returns_empty(self, monkeypatch):
        monkeypatch.setattr(global_settings.config, "add_repo_metadata", False)
        gp = self._make_mock_provider({"AGENTS.md": "content"})
        assert load_repo_metadata(gp) == ""

    def test_no_base_branch_returns_empty(self, monkeypatch):
        monkeypatch.setattr(global_settings.config, "add_repo_metadata", True)
        mock_gp = type("MockGP", (), {})()
        mock_gp.get_pr_base_branch_name = lambda: ""
        assert load_repo_metadata(mock_gp) == ""

    def test_missing_provider_method_returns_empty(self, monkeypatch):
        monkeypatch.setattr(global_settings.config, "add_repo_metadata", True)
        mock_gp = type("MockGP", (), {})()
        mock_gp.get_pr_base_branch_name = lambda: "main"
        assert load_repo_metadata(mock_gp) == ""

    def test_no_files_found(self, monkeypatch):
        monkeypatch.setattr(global_settings.config, "add_repo_metadata", True)
        gp = self._make_mock_provider({})
        assert load_repo_metadata(gp) == ""

    def test_single_file_loaded(self, monkeypatch):
        monkeypatch.setattr(global_settings.config, "add_repo_metadata", True)
        monkeypatch.setattr(
            global_settings.config,
            "add_repo_metadata_file_list",
            ["AGENTS.md"],
        )
        gp = self._make_mock_provider({"AGENTS.md": "be awesome"})
        result = load_repo_metadata(gp)
        assert "AGENTS.md" in result
        assert "be awesome" in result

    def test_multiple_files_loaded(self, monkeypatch):
        monkeypatch.setattr(global_settings.config, "add_repo_metadata", True)
        monkeypatch.setattr(
            global_settings.config,
            "add_repo_metadata_file_list",
            ["AGENTS.md", "CLAUDE.md"],
        )
        gp = self._make_mock_provider({
            "AGENTS.md": "be awesome",
            "CLAUDE.md": "be kind",
        })
        result = load_repo_metadata(gp)
        assert "AGENTS.md" in result
        assert "be awesome" in result
        assert "CLAUDE.md" in result
        assert "be kind" in result

    def test_per_file_truncation(self, monkeypatch):
        monkeypatch.setattr(global_settings.config, "add_repo_metadata", True)
        monkeypatch.setattr(
            global_settings.config,
            "add_repo_metadata_file_list",
            ["AGENTS.md"],
        )
        monkeypatch.setattr(global_settings.config, "repo_metadata_max_chars_per_file", 10)
        gp = self._make_mock_provider({"AGENTS.md": "a" * 100})
        result = load_repo_metadata(gp)
        content_chunk = result.split("```markdown\n")[1].split("\n```")[0]
        assert len(content_chunk) == 10

    def test_per_file_truncation_at_newline(self, monkeypatch):
        monkeypatch.setattr(global_settings.config, "add_repo_metadata", True)
        monkeypatch.setattr(
            global_settings.config,
            "add_repo_metadata_file_list",
            ["AGENTS.md"],
        )
        monkeypatch.setattr(global_settings.config, "repo_metadata_max_chars_per_file", 10)
        gp = self._make_mock_provider({"AGENTS.md": "line one\nline two\nline three"})
        result = load_repo_metadata(gp)
        content_chunk = result.split("```markdown\n")[1].split("\n```")[0]
        assert content_chunk == "line one"
        assert "\n" not in content_chunk
        assert len(content_chunk) <= 10

    def test_max_files_limit(self, monkeypatch):
        monkeypatch.setattr(global_settings.config, "add_repo_metadata", True)
        monkeypatch.setattr(
            global_settings.config,
            "add_repo_metadata_file_list",
            ["AGENTS.md", "CLAUDE.md", "GEMINI.md"],
        )
        monkeypatch.setattr(global_settings.config, "repo_metadata_max_files", 2)
        gp = self._make_mock_provider({
            "AGENTS.md": "a",
            "CLAUDE.md": "b",
            "GEMINI.md": "c",
        })
        result = load_repo_metadata(gp)
        assert "AGENTS.md" in result
        assert "CLAUDE.md" in result
        assert "GEMINI.md" not in result

    def test_total_chars_truncation(self, monkeypatch):
        monkeypatch.setattr(global_settings.config, "add_repo_metadata", True)
        monkeypatch.setattr(
            global_settings.config,
            "add_repo_metadata_file_list",
            ["AGENTS.md", "CLAUDE.md"],
        )
        monkeypatch.setattr(global_settings.config, "repo_metadata_max_total_chars", 50)
        gp = self._make_mock_provider({
            "AGENTS.md": "x" * 100,
            "CLAUDE.md": "y" * 100,
        })
        result = load_repo_metadata(gp)
        assert len(result) <= 50

    def test_total_chars_truncation_at_newline(self, monkeypatch):
        monkeypatch.setattr(global_settings.config, "add_repo_metadata", True)
        monkeypatch.setattr(
            global_settings.config,
            "add_repo_metadata_file_list",
            ["AGENTS.md"],
        )
        monkeypatch.setattr(global_settings.config, "repo_metadata_max_total_chars", 30)
        gp = self._make_mock_provider({"AGENTS.md": "first line\nsecond line\nthird line"})
        result = load_repo_metadata(gp)
        assert len(result) <= 30
        assert result.endswith("\n")

    def test_one_bad_file_doesnt_break_others(self, monkeypatch):
        monkeypatch.setattr(global_settings.config, "add_repo_metadata", True)
        monkeypatch.setattr(
            global_settings.config,
            "add_repo_metadata_file_list",
            ["AGENTS.md", "CLAUDE.md", "GEMINI.md"],
        )
        gp = self._make_mock_provider({})

        original = gp.get_pr_file_content

        def faulty(fp, br):
            if fp == "CLAUDE.md":
                raise RuntimeError("corrupt")
            return original(fp, br)

        gp.get_pr_file_content = faulty
        result = load_repo_metadata(gp)
        assert result == ""


class TestPathValidation:
    def test_safe_paths_accepted(self):
        assert _is_safe_repo_file_path("AGENTS.md") is True
        assert _is_safe_repo_file_path("CLAUDE.md") is True
        assert _is_safe_repo_file_path("docs/QODO.md") is True
        assert _is_safe_repo_file_path(".github/copilot-instructions.md") is True
        assert _is_safe_repo_file_path("some-file.txt") is True

    def test_traversal_rejected(self):
        assert _is_safe_repo_file_path("../etc/passwd") is False
        assert _is_safe_repo_file_path("../../secrets.txt") is False
        assert _is_safe_repo_file_path("foo/../../etc/shadow") is False

    def test_absolute_paths_rejected(self):
        assert _is_safe_repo_file_path("/etc/passwd") is False
        assert _is_safe_repo_file_path("/absolute/path.md") is False
        assert _is_safe_repo_file_path("C:\\Windows\\system32\\config") is False
        assert _is_safe_repo_file_path("\\leading-backslash") is False

    def test_percent_encoded_rejected(self):
        assert _is_safe_repo_file_path("%2e%2e/etc/passwd") is False
        assert _is_safe_repo_file_path("%2e%2e%2fetc%2fpasswd") is False
        assert _is_safe_repo_file_path("foo/%2e%2e/%2e%2e/etc/shadow") is False
        assert _is_safe_repo_file_path("%2F etc/passwd") is False
        assert _is_safe_repo_file_path("%252e%252e/secrets") is False

    def test_empty_and_whitespace_rejected(self):
        assert _is_safe_repo_file_path("") is False
        assert _is_safe_repo_file_path("   ") is False

    def test_unsafe_path_not_loaded(self, monkeypatch):
        """A traversal path in file list must not reach get_pr_file_content."""
        calls: list[str] = []

        def spy(fp, br):
            calls.append(fp)
            return "should not be used"

        gp = type("MockGP", (), {})()
        gp.get_pr_base_branch_name = lambda: "main"
        gp.get_pr_file_content = spy

        monkeypatch.setattr(global_settings.config, "add_repo_metadata", True)
        monkeypatch.setattr(
            global_settings.config,
            "add_repo_metadata_file_list",
            ["../secrets.txt", "/etc/passwd"],
        )

        result = load_repo_metadata(gp)
        assert calls == []
        assert result == ""

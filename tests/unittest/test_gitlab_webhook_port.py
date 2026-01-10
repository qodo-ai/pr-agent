import importlib
import os
from unittest import mock


def _load_module():
    import pr_agent.servers.gitlab_webhook as gitlab_webhook

    return importlib.reload(gitlab_webhook)


def test_start_uses_port_env(monkeypatch):
    monkeypatch.setenv("GITLAB__URL", "https://gitlab.example.com")
    monkeypatch.setenv("PORT", "4567")
    module = _load_module()

    with mock.patch.object(module.uvicorn, "run") as mock_run:
        module.start()

    args, kwargs = mock_run.call_args
    assert kwargs["port"] == 4567
    assert kwargs["host"] == "0.0.0.0"

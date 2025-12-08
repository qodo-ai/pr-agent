# PR-Agent UI (single-page)

This is a minimal single-page UI for the PR-Agent repository. It lists the repository (current workspace) and shows details when you click the repo.

Quick start (macOS / zsh):

```bash
cd /path/to/pr-agent
python3 -m venv .venv-ui
source .venv-ui/bin/activate
pip install -r ui/requirements-ui.txt
python ui/app.py
```

Then open `http://127.0.0.1:8080/` in your browser.

Notes:
- This is intentionally minimal: it reads Git information by running `git` in the repository root.
- The app locates the repo root by walking up from the current working directory until it finds a `.git` folder.
- It is safe to run locally and intended as a starting point — you can extend it to call the CLI for review/describe actions and show results inline.

Next steps you may want:
- Add endpoints that call the internal CLI (e.g., trigger `python cli.py --pr_url=... review`) and stream results back to the browser.
- Add authentication for multi-user environments.
- Use GitPython instead of shelling out to `git` for richer information.

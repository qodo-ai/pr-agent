# PR-Agent — Quick Capabilities Summary

**Overview:**
- PR-Agent is a CLI and integration tool that automates pull request (PR) review tasks using LLMs. It provides automated PR reviews, descriptions, code suggestions, documentation helpers, and related workflows for multiple Git providers.

**Core Capabilities:**
- **/review (PR review):** Generate a reviewer-style audit of a PR including security, tests, effort, and best-practice suggestions.
- **/describe (PR description):** Produce a clear PR description and changelog updates from the diff and user notes.
- **/improve (Code suggestions):** Suggest code improvements, refactorings, and non-functional improvements (style, tests, docs).
- **/add_docs (Docs generation):** Create or update documentation for changed code or new APIs.
- **/custom_prompt:** Run a custom prompt against the PR context.
- **/ask (Interactive questions):** Ask follow-up questions about a PR and receive focused answers.
- **CLI:** `pr-agent` command-line tool to run review/describe/improve locally or in CI.
- **GitHub Actions & App:** Integrations for automated runs in workflows and as a GitHub App.

**Integration / Providers:**
- **Git providers:** GitHub, GitLab, Gitea, Bitbucket, Bitbucket Server, Gerrit, local git.
- **LLM Providers via LiteLLM:** OpenAI-compatible endpoints (including Blackbox.ai via `OPENAI_API_BASE`), Anthropic, Cohere, HuggingFace, and others supported by LiteLLM. Configuration uses provider-prefixed model strings (e.g., `openai/gpt-4o`).
- **Secret providers:** AWS Secrets Manager and Google Cloud Storage secret provider are supported for secure secret management.

**Configuration & Secrets:**
- Settings are managed with `dynaconf` and loaded from `pr_agent/settings/*` and optional repository-level `pyproject.toml` under `tool.pr-agent`.
- Local secret file: `pr_agent/settings/.secrets.toml` (DO NOT commit real tokens). The template is `pr_agent/settings/.secrets_template.toml`.
- Key settings:
  - `openai.key` and `openai.api_base` for OpenAI-compatible endpoints.
  - `config.model` controls default model (use provider-prefixed strings LiteLLM expects).

**Extensibility:**
- The codebase provides modular AI handler layers (`algo/ai_handlers`) so new providers/adapters can be added.
- Token handling and patch generation are pluggable to tune prompt size and chunking.

**Development / Quick Start:**
- Create a Python virtualenv and install:

  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -e .
  ```

- Provide secrets locally in `pr_agent/settings/.secrets.toml` or export env vars (preferred for CI):

  ```bash
  export OPENAI_API_KEY="<YOUR_KEY>"
  export OPENAI_API_BASE="https://api.blackbox.ai"  # if using Blackbox
  ```

- Example local run (review):

  ```bash
  python cli.py --pr_url="https://github.com/<org>/<repo>/pull/123" review
  ```

**Security & Best Practices:**
- Never commit API keys or `.secrets.toml` to version control.
- If secrets are accidentally pushed, rotate and remove from history (BFG or git filter-repo) immediately.
- Use a secrets manager for CI and production deployments.

**Where to get help / docs:**
- Project docs are under `docs/` and `pr_agent/settings/*.toml` contain configuration docs and prompts.
- For LiteLLM provider formats, see: https://docs.litellm.ai/docs/providers

**Files of interest:**
- `pr_agent/cli.py` — CLI entrypoint.
- `pr_agent/config_loader.py` — dynaconf initialization and settings loading.
- `pr_agent/settings/` — configuration and prompt files.
- `pr_agent/algo/` — core logic: token handling, prompt preparation, AI handlers.
- `pr_agent/git_providers/` — adapters for Git hosting providers.

If you want, I can:
- Add this content into the main `README.md` replacing or merging with the existing one.
- Generate a one-page `CONTRIBUTING` snippet for local development and secret handling.
- Commit the new README file and create a small PR with the change.

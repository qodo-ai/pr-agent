"""Shared configuration boundaries for repository-provided settings."""

# Sections that touch host-level capabilities cannot be fully configured from
# a repository's settings file. The same allowlist is used by repo settings
# application and CLI argument validation so the two entry points cannot drift.
# For each section listed here, only the keys in its allowlist may be set from a
# repository; every other key is dropped with a warning.
#
# skills: `enabled` and `max_skills_tokens` are safe per-repo preferences (a repo can opt in to, or
# size, the host's admin-curated skill library). `paths` is NOT overridable: it points at the
# PR-Agent host's filesystem, so letting a repo set it would allow a malicious repo to read
# sensitive host files (e.g. ~/.ssh/*) into the LLM prompt. `paths` therefore stays host-only.
#
# push_outputs: routes review data to operator-controlled sinks (webhook/slack/file). Letting a
# repo set any of these would let a malicious repo exfiltrate review data to an arbitrary host,
# reach internal endpoints (SSRF), or append to arbitrary host files. The whole section is
# therefore host-only (empty allowlist -> every key dropped).
#
# prompt_fragments: contains Jinja source rendered by the host before it is inserted into tool
# prompts. Keep the whole section host-only so repository settings and comment arguments cannot
# supply executable template expressions.
#
# pr_agentic_reviewer: unlike every other tool section, its keys multiply the *number* of model
# calls the host pays for rather than the size of one call -- `max_delegate_calls` times
# `pass_max_tool_iterations` is a nested loop, and `provider`/`model` choose which of the host's
# API keys is spent. A commenter who could set those could bill the host for an unbounded run.
# Only the two keys that shape what a review looks at, not how much of it there is, are
# overridable: `aspects` (bounded to the aspects the code defines) and `max_findings_per_pass`
# (bounded by the pass's own output budget).
REPO_OVERRIDABLE_KEYS_BY_HOST_SECTION = {
    "skills": frozenset({"enabled", "max_skills_tokens"}),
    "push_outputs": frozenset(),
    "prompt_fragments": frozenset(),
    "pr_agentic_reviewer": frozenset({"aspects", "max_findings_per_pass"}),
}

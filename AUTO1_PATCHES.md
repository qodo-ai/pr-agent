# AUTO1 Patch Ledger

This file records all local changes carried on top of the upstream PR-Agent codebase.
Keep this list minimal to ease upstream rebases.

## Upstream baseline

- Upstream repo: qodo-ai/pr-agent
- Upstream tag: v0.31
- Upstream commit: d36ad319f7fb0049205017405a71275c41599587
- Synced on: 2026-02-16

## Local patches

| Patch ID | Ticket | Type | Files | Why | Upstream status | Removal criteria |
| --- | --- | --- | --- | --- | --- | --- |
| azure-annotations | OPS-24074 | Fix | pr_agent/git_providers/azuredevops_provider.py | Avoid import-time NameError when optional Azure DevOps dependencies are missing; this crash happens even when git_provider=github. | Not upstreamed yet. | Remove once upstream includes the fix and we rebase to a tag containing it. |
| pyjwt-pin | OPS-24074 | Fix | requirements.txt | GitHub App JWT expects integer iss, but PyJWT >= 2.9 requires string; pin to a compatible PyJWT range to avoid auth failures. | Not upstreamed yet. | Remove once upstream pins PyJWT compatibly or updates auth logic. |

## Rebase checklist

1) Fetch upstream tag and reset local baseline.
2) Cherry-pick patch commits listed above (or re-apply manually).
3) Verify container boots without Azure DevOps deps installed.
4) Run a canary PR comment to confirm GitHub App workflow.

## Notes

- Keep patches isolated in small, focused commits.
- If a patch is upstreamed, delete its row and drop the commit on the next rebase.

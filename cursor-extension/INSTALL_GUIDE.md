# 🔧 Fix in Cursor - Installation Guide for Workiz Employees

## Quick Install (30 seconds)

### Prerequisites
- [GitHub CLI](https://cli.github.com/) installed: `brew install gh`
- Authenticated with GitHub: `gh auth login` (choose GitHub.com, HTTPS, browser auth)
- Access to the `Workiz/workiz-pr-agent` private repository

### Install the Extension

**Option A: One-liner**
```bash
gh release download --repo Workiz/workiz-pr-agent --pattern "workiz-pr-agent-fix.vsix" && cursor --install-extension workiz-pr-agent-fix.vsix && rm workiz-pr-agent-fix.vsix
```

**Option B: Step by step**
```bash
# 1. Download the extension
gh release download --repo Workiz/workiz-pr-agent --pattern "workiz-pr-agent-fix.vsix"

# 2. Install in Cursor
cursor --install-extension workiz-pr-agent-fix.vsix

# 3. Cleanup
rm workiz-pr-agent-fix.vsix

# 4. Restart Cursor
```

**Option C: Manual download**
1. Go to https://github.com/Workiz/workiz-pr-agent/releases
2. Find the latest `cursor-ext-v*` release
3. Download `workiz-pr-agent-fix.vsix`
4. In Cursor: `Cmd+Shift+P` → "Extensions: Install from VSIX..."
5. Select the downloaded file
6. Restart Cursor

---

## How to Use

When Workiz PR Agent posts inline comments on your PRs, each comment includes a **"🔧 Fix in Cursor"** button.

### With the Extension Installed ✅
1. Click "Fix in Cursor" on any PR comment
2. Cursor opens the file at the exact line
3. AI chat opens with the fix prompt pre-filled!
4. Just press Enter to have the AI fix the issue

### Without the Extension ❌
1. Click "Fix in Cursor"
2. A webpage opens showing the prompt
3. You must manually copy the prompt
4. Paste into Cursor's AI chat

---

## Verify Installation

In Cursor, press `Cmd+Shift+X` to open Extensions. Search for "Workiz" - you should see:

```
Workiz PR Agent - Fix in Cursor
workiz.workiz-pr-agent-fix
v1.0.0
```

---

## Updating

When a new version is released, repeat the install steps - it will update automatically.

Or set up notifications:
```bash
gh api repos/Workiz/workiz-pr-agent/releases/latest --jq '.tag_name'
```

---

## Troubleshooting

### "command not found: cursor"
Cursor CLI not installed. In Cursor: `Cmd+Shift+P` → "Shell Command: Install 'cursor' command in PATH"

### "command not found: gh"
Install GitHub CLI: `brew install gh`

### "HTTP 404: Not Found"
You don't have access to the repo. Contact DevOps to get added.

### "Extension host terminated unexpectedly"
Restart Cursor completely (quit and reopen).

---

## Questions?
Contact DevOps in #devops Slack channel.

# Workiz PR Agent - Fix in Cursor Extension

This Cursor/VS Code extension enables the "Fix in Cursor" functionality from Workiz PR Agent code reviews.

> **🔒 Internal Use Only** - This extension is distributed privately via GitHub Releases.

## How It Works

When you click "Fix in Cursor" on a PR comment:

1. **Opens the file** at the exact line where the issue was found
2. **Opens the AI chat** with a pre-filled prompt containing:
   - Issue description
   - Suggested fix
   - File path and line number
   - Instructions for the AI

## Installation

### Option 1: Quick Install Script (Recommended)

```bash
# Make sure you're authenticated with GitHub CLI
gh auth login

# Run the installer
curl -sSL https://raw.githubusercontent.com/Workiz/workiz-pr-agent/main/cursor-extension/scripts/install.sh | bash
```

### Option 2: Download from GitHub Releases

1. Go to [Releases](https://github.com/Workiz/workiz-pr-agent/releases)
2. Download `workiz-pr-agent-fix.vsix` from the latest `cursor-ext-v*` release
3. In Cursor: `Cmd+Shift+P` → "Extensions: Install from VSIX..."
4. Select the downloaded `.vsix` file
5. Restart Cursor

### Option 3: Install via CLI

```bash
# Download latest release
gh release download --repo Workiz/workiz-pr-agent --pattern "workiz-pr-agent-fix.vsix"

# Install in Cursor
cursor --install-extension workiz-pr-agent-fix.vsix

# Or in VS Code
code --install-extension workiz-pr-agent-fix.vsix
```

### Development (Building from Source)

1. Open the `cursor-extension` folder in Cursor/VS Code
2. Run `npm install`
3. Run `npm run compile`
4. Press F5 to start debugging (launches Extension Development Host)

### Build VSIX Manually

```bash
cd cursor-extension
npm install
npm run compile
npx @vscode/vsce package --out workiz-pr-agent-fix.vsix
```

## URI Format

The extension handles URIs in this format:

```
cursor://workiz.workiz-pr-agent-fix/fix?prompt={encoded}&file={path}&line={num}
```

| Parameter | Description |
|-----------|-------------|
| `prompt` | URL-encoded prompt text for the AI |
| `file` | Relative path to the file in the repo |
| `line` | Line number where the issue is located |

## How Workiz PR Agent Uses This

1. PR Agent posts inline comments with "Fix in Cursor" links
2. Links point to our redirect service: `https://server.com/api/v1/cursor-redirect?...`
3. Redirect service serves an HTML page that:
   - Attempts to open `cursor://workiz.workiz-pr-agent-fix/fix?...`
   - Falls back to showing the prompt for copy/paste

## Cursor Commands

The extension registers:

| Command | Description |
|---------|-------------|
| `workiz-pr-agent-fix.openFix` | Manually enter a fix prompt |

## Requirements

- Cursor IDE or VS Code 1.74.0+
- The workspace must have the relevant repository open

## Troubleshooting

### "File not found"
Make sure the repository is open in Cursor before clicking the link.

### "Could not open AI chat"
The extension tries multiple methods to open the AI chat. If automatic opening fails, it will copy the prompt to your clipboard so you can paste it manually.

### Link doesn't open Cursor
1. Make sure the extension is installed and enabled
2. Try opening Cursor first, then clicking the link
3. Check that `cursor://` protocol is registered on your system

## Development

```bash
# Install dependencies
npm install

# Compile TypeScript
npm run compile

# Watch for changes
npm run watch

# Package for distribution
npx vsce package
```

## License

MIT

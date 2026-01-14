#!/bin/bash
# Workiz PR Agent - Cursor Extension Installer
# Downloads the latest .vsix from GitHub releases and installs it

set -e

REPO="Workiz/workiz-pr-agent"
ASSET_NAME="workiz-pr-agent-fix.vsix"
TEMP_DIR=$(mktemp -d)

echo "🔧 Workiz PR Agent - Cursor Extension Installer"
echo "================================================"
echo ""

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is required but not installed."
    echo ""
    echo "Install it with:"
    echo "  brew install gh"
    echo ""
    echo "Or download manually from:"
    echo "  https://github.com/$REPO/releases/latest"
    exit 1
fi

# Check if user is authenticated
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub CLI."
    echo ""
    echo "Run: gh auth login"
    exit 1
fi

echo "📥 Downloading latest extension from GitHub releases..."
cd "$TEMP_DIR"

# Download the latest release asset
gh release download --repo "$REPO" --pattern "$ASSET_NAME" || {
    echo "❌ Failed to download extension."
    echo "Make sure you have access to the $REPO repository."
    exit 1
}

echo "📦 Installing extension in Cursor..."

# Try to install in Cursor (or VS Code as fallback)
if command -v cursor &> /dev/null; then
    cursor --install-extension "$ASSET_NAME"
    echo ""
    echo "✅ Extension installed in Cursor!"
elif command -v code &> /dev/null; then
    code --install-extension "$ASSET_NAME"
    echo ""
    echo "✅ Extension installed in VS Code!"
else
    echo ""
    echo "⚠️  Could not find Cursor or VS Code CLI."
    echo ""
    echo "The extension was downloaded to: $TEMP_DIR/$ASSET_NAME"
    echo ""
    echo "Install manually:"
    echo "  1. Open Cursor"
    echo "  2. Cmd+Shift+P → 'Extensions: Install from VSIX...'"
    echo "  3. Select: $TEMP_DIR/$ASSET_NAME"
    exit 0
fi

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "🎉 Done! Restart Cursor to activate the extension."
echo ""
echo "The 'Fix in Cursor' buttons in PR comments will now:"
echo "  1. Open the file at the correct line"
echo "  2. Pre-fill the AI chat with the fix prompt"

import * as vscode from 'vscode';
import * as path from 'path';
import * as https from 'https';

const GITHUB_REPO = 'Workiz/workiz-pr-agent';
const CURRENT_VERSION = '1.0.5';

/**
 * Workiz PR Agent - Fix in Cursor Extension
 * 
 * This extension handles "Fix in Cursor" links from Workiz PR Agent code reviews.
 * When a user clicks a "Fix in Cursor" link, this extension:
 * 1. Opens the specified file at the correct line
 * 2. Opens the AI chat (Composer) with a pre-filled prompt
 * 
 * URI Format:
 * cursor://workiz.workiz-pr-agent-fix/fix?prompt=<encoded>&file=<path>&line=<num>
 */

export function activate(context: vscode.ExtensionContext) {
    console.log('Workiz PR Agent Fix extension activated');

    // Check for updates on activation
    checkForUpdates(context);

    // Register the URI handler
    const uriHandler = vscode.window.registerUriHandler({
        handleUri(uri: vscode.Uri): vscode.ProviderResult<void> {
            console.log('Received URI:', uri.toString());
            
            if (uri.path === '/fix') {
                handleFixUri(uri);
            } else {
                vscode.window.showWarningMessage(`Unknown path: ${uri.path}`);
            }
        }
    });

    // Register the manual command
    const command = vscode.commands.registerCommand('workiz-pr-agent-fix.openFix', async () => {
        const prompt = await vscode.window.showInputBox({
            prompt: 'Enter the fix prompt',
            placeHolder: 'Fix the following code review issue...'
        });
        
        if (prompt) {
            await openAiChatWithPrompt(prompt);
        }
    });

    // Register the check for updates command
    const updateCommand = vscode.commands.registerCommand('workiz-pr-agent-fix.checkForUpdates', async () => {
        await checkForUpdates(context, true);
    });

    context.subscriptions.push(uriHandler, command, updateCommand);
}

/**
 * Handle the /fix URI path
 */
async function handleFixUri(uri: vscode.Uri): Promise<void> {
    const params = new URLSearchParams(uri.query);
    
    const prompt = params.get('prompt') || '';
    const filePath = params.get('file') || '';
    const lineStr = params.get('line') || '1';
    const line = parseInt(lineStr, 10) || 1;

    console.log('Fix request:', { filePath, line, promptLength: prompt.length });

    // Step 1: Open the file at the correct line
    if (filePath) {
        await openFileAtLine(filePath, line);
    }

    // Step 2: Open AI chat with the prompt
    if (prompt) {
        // Small delay to ensure file is open first
        await new Promise(resolve => setTimeout(resolve, 500));
        await openAiChatWithPrompt(prompt);
    }

    vscode.window.showInformationMessage('Fix loaded! Review the AI suggestion.');
}

/**
 * Open a file at a specific line number
 */
async function openFileAtLine(filePath: string, line: number): Promise<void> {
    try {
        // Try to find the file in the workspace
        const workspaceFolders = vscode.workspace.workspaceFolders;
        
        if (!workspaceFolders || workspaceFolders.length === 0) {
            vscode.window.showWarningMessage('No workspace folder open. Please open the project first.');
            return;
        }

        // Try each workspace folder
        for (const folder of workspaceFolders) {
            const fullPath = path.join(folder.uri.fsPath, filePath);
            const fileUri = vscode.Uri.file(fullPath);

            try {
                // Check if file exists
                await vscode.workspace.fs.stat(fileUri);

                // Open the file
                const document = await vscode.workspace.openTextDocument(fileUri);
                const editor = await vscode.window.showTextDocument(document);

                // Go to the line (1-indexed in UI, 0-indexed in API)
                const lineIndex = Math.max(0, line - 1);
                const position = new vscode.Position(lineIndex, 0);
                const range = new vscode.Range(position, position);
                
                editor.selection = new vscode.Selection(position, position);
                editor.revealRange(range, vscode.TextEditorRevealType.InCenter);

                console.log(`Opened file: ${fullPath} at line ${line}`);
                return;
            } catch {
                // File not found in this workspace folder, try next
                continue;
            }
        }

        // File not found in any workspace folder
        vscode.window.showWarningMessage(`File not found: ${filePath}`);
    } catch (error) {
        console.error('Error opening file:', error);
        vscode.window.showErrorMessage(`Failed to open file: ${filePath}`);
    }
}

/**
 * Open the AI chat (Composer) with a pre-filled prompt
 * 
 * Cursor's AI chat can be opened with various commands.
 * We try multiple methods to ensure compatibility across versions.
 */
async function openAiChatWithPrompt(prompt: string): Promise<void> {
    try {
        // First, copy the prompt to clipboard as a reliable fallback
        await vscode.env.clipboard.writeText(prompt);
        console.log('Prompt copied to clipboard');

        // Method 1: Try aichat.newchataction with text parameter (Cursor's main command)
        try {
            await vscode.commands.executeCommand('aichat.newchataction', prompt);
            console.log('Opened AI chat with aichat.newchataction');
            return;
        } catch (e) {
            console.log('aichat.newchataction failed:', e);
        }

        // Method 2: Try composerMode.agent.startFromSelection with prompt
        try {
            await vscode.commands.executeCommand('composerMode.agent.startFromSelection', { prompt });
            console.log('Opened agent mode with prompt');
            return;
        } catch (e) {
            console.log('composerMode.agent.startFromSelection failed:', e);
        }

        // Method 3: Try composer.startComposerPrompt
        try {
            await vscode.commands.executeCommand('composer.startComposerPrompt', prompt);
            console.log('Opened composer with startComposerPrompt');
            return;
        } catch (e) {
            console.log('composer.startComposerPrompt failed:', e);
        }

        // Method 4: Try opening chat and simulate paste
        try {
            // Open a new agent chat
            await vscode.commands.executeCommand('aichat.newagentchat');
            console.log('Opened new agent chat');
            
            // Small delay then simulate paste
            await new Promise(resolve => setTimeout(resolve, 300));
            await vscode.commands.executeCommand('editor.action.clipboardPasteAction');
            console.log('Pasted from clipboard');
            return;
        } catch (e) {
            console.log('aichat.newagentchat + paste failed:', e);
        }

        // Method 5: Try workbench.action.chat.newChat
        try {
            await vscode.commands.executeCommand('workbench.action.chat.newChat');
            console.log('Opened chat with workbench.action.chat.newChat');
            
            // Delay and paste
            await new Promise(resolve => setTimeout(resolve, 300));
            await vscode.commands.executeCommand('editor.action.clipboardPasteAction');
            return;
        } catch (e) {
            console.log('workbench.action.chat.newChat failed:', e);
        }

        // Fallback: Show message that prompt is in clipboard
        vscode.window.showInformationMessage(
            '📋 Prompt copied to clipboard! Press Cmd+V (Mac) or Ctrl+V (Win) in the chat to paste.',
            'OK'
        );
    } catch (error) {
        console.error('Error opening AI chat:', error);
        vscode.window.showErrorMessage('Failed to open AI chat. Prompt is in clipboard - paste with Cmd+V.');
    }
}

/**
 * Check for updates from GitHub releases
 */
async function checkForUpdates(context: vscode.ExtensionContext, manual: boolean = false): Promise<void> {
    const lastCheck = context.globalState.get<number>('lastUpdateCheck', 0);
    const now = Date.now();
    const oneDay = 24 * 60 * 60 * 1000;

    // Skip if checked within the last day (unless manual check)
    if (!manual && (now - lastCheck) < oneDay) {
        console.log('Skipping update check - checked recently');
        return;
    }

    try {
        const latestRelease = await fetchLatestRelease();
        
        if (!latestRelease) {
            if (manual) {
                vscode.window.showInformationMessage('Could not check for updates. Please try again later.');
            }
            return;
        }

        // Save check time
        await context.globalState.update('lastUpdateCheck', now);

        const latestVersion = latestRelease.tag_name.replace(/^v/, '');
        console.log(`Current version: ${CURRENT_VERSION}, Latest version: ${latestVersion}`);

        if (isNewerVersion(latestVersion, CURRENT_VERSION)) {
            const action = await vscode.window.showInformationMessage(
                `🚀 Workiz PR Agent extension update available: v${latestVersion} (current: v${CURRENT_VERSION})`,
                'Update Now',
                'View Release',
                'Later'
            );

            if (action === 'Update Now') {
                await installUpdate(latestRelease);
            } else if (action === 'View Release') {
                vscode.env.openExternal(vscode.Uri.parse(latestRelease.html_url));
            }
        } else if (manual) {
            vscode.window.showInformationMessage(`✅ You're running the latest version (v${CURRENT_VERSION})`);
        }
    } catch (error) {
        console.error('Error checking for updates:', error);
        if (manual) {
            vscode.window.showErrorMessage('Failed to check for updates. Please try again later.');
        }
    }
}

/**
 * Fetch the latest release from GitHub
 */
function fetchLatestRelease(): Promise<GitHubRelease | null> {
    return new Promise((resolve) => {
        const options = {
            hostname: 'api.github.com',
            path: `/repos/${GITHUB_REPO}/releases/latest`,
            method: 'GET',
            headers: {
                'User-Agent': 'Workiz-PR-Agent-Extension',
                'Accept': 'application/vnd.github.v3+json'
            }
        };

        const req = https.request(options, (res) => {
            let data = '';

            res.on('data', (chunk) => {
                data += chunk;
            });

            res.on('end', () => {
                try {
                    if (res.statusCode === 200) {
                        resolve(JSON.parse(data));
                    } else {
                        console.log(`GitHub API returned status ${res.statusCode}`);
                        resolve(null);
                    }
                } catch {
                    resolve(null);
                }
            });
        });

        req.on('error', (error) => {
            console.error('Error fetching release:', error);
            resolve(null);
        });

        req.setTimeout(10000, () => {
            req.destroy();
            resolve(null);
        });

        req.end();
    });
}

/**
 * Compare version strings (semver-like)
 */
function isNewerVersion(latest: string, current: string): boolean {
    const latestParts = latest.split('.').map(Number);
    const currentParts = current.split('.').map(Number);

    for (let i = 0; i < Math.max(latestParts.length, currentParts.length); i++) {
        const l = latestParts[i] || 0;
        const c = currentParts[i] || 0;
        
        if (l > c) return true;
        if (l < c) return false;
    }
    
    return false;
}

/**
 * Install the update by downloading and installing the .vsix
 */
async function installUpdate(release: GitHubRelease): Promise<void> {
    const vsixAsset = release.assets.find(asset => asset.name.endsWith('.vsix'));
    
    if (!vsixAsset) {
        vscode.window.showErrorMessage('No .vsix file found in the release. Please update manually.');
        vscode.env.openExternal(vscode.Uri.parse(release.html_url));
        return;
    }

    // Copy the install command to clipboard for easy installation
    const installCommand = `gh release download --repo ${GITHUB_REPO} --pattern "${vsixAsset.name}" --clobber && cursor --install-extension ${vsixAsset.name} && rm ${vsixAsset.name}`;
    
    await vscode.env.clipboard.writeText(installCommand);
    
    const action = await vscode.window.showInformationMessage(
        '📋 Install command copied to clipboard! Paste it in your terminal to update.',
        'Open Terminal',
        'Download Manually'
    );

    if (action === 'Open Terminal') {
        const terminal = vscode.window.createTerminal('Update Extension');
        terminal.show();
        terminal.sendText(installCommand);
    } else if (action === 'Download Manually') {
        vscode.env.openExternal(vscode.Uri.parse(vsixAsset.browser_download_url));
    }
}

interface GitHubRelease {
    tag_name: string;
    html_url: string;
    assets: Array<{
        name: string;
        browser_download_url: string;
    }>;
}

export function deactivate() {
    console.log('Workiz PR Agent Fix extension deactivated');
}

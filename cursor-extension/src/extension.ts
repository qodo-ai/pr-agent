import * as vscode from 'vscode';
import * as path from 'path';

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

    context.subscriptions.push(uriHandler, command);
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

export function deactivate() {
    console.log('Workiz PR Agent Fix extension deactivated');
}

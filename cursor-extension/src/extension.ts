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
 * In Cursor, this uses the 'composer.openComposer' or 'aichat.open' command
 * to open the AI chat and set the input text.
 */
async function openAiChatWithPrompt(prompt: string): Promise<void> {
    try {
        // Method 1: Try Cursor's Composer (newer versions)
        // The 'composer.open' command with initialPrompt parameter
        try {
            await vscode.commands.executeCommand('composer.open', { initialPrompt: prompt });
            console.log('Opened Composer with prompt');
            return;
        } catch {
            console.log('composer.open not available, trying alternatives');
        }

        // Method 2: Try opening the AI chat panel and setting clipboard
        // This is a fallback for versions without direct prompt injection
        try {
            // Copy prompt to clipboard first
            await vscode.env.clipboard.writeText(prompt);
            
            // Try various AI chat commands that might exist in Cursor
            const commands = [
                'aichat.open',
                'cursorai.openChat',
                'cursor.newChat',
                'workbench.action.chat.open'
            ];

            for (const cmd of commands) {
                try {
                    await vscode.commands.executeCommand(cmd);
                    vscode.window.showInformationMessage('Prompt copied to clipboard. Press Ctrl+V to paste.');
                    console.log(`Opened AI chat with command: ${cmd}`);
                    return;
                } catch {
                    continue;
                }
            }
        } catch (error) {
            console.log('Failed to open AI chat:', error);
        }

        // Method 3: Fallback - just show the prompt
        const action = await vscode.window.showInformationMessage(
            'Could not open AI chat automatically. Copy the prompt?',
            'Copy Prompt'
        );

        if (action === 'Copy Prompt') {
            await vscode.env.clipboard.writeText(prompt);
            vscode.window.showInformationMessage('Prompt copied to clipboard!');
        }
    } catch (error) {
        console.error('Error opening AI chat:', error);
        vscode.window.showErrorMessage('Failed to open AI chat. Please open it manually.');
    }
}

export function deactivate() {
    console.log('Workiz PR Agent Fix extension deactivated');
}

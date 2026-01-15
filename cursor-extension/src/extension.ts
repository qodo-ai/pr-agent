import * as vscode from 'vscode';
import * as path from 'path';
import * as https from 'https';

const GITHUB_REPO = 'Workiz/workiz-pr-agent';
const CURRENT_VERSION = '1.0.6';

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

  checkForUpdates(context);

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

  const command = vscode.commands.registerCommand('workiz-pr-agent-fix.openFix', async () => {
    const prompt = await vscode.window.showInputBox({
      prompt: 'Enter the fix prompt',
      placeHolder: 'Fix the following code review issue...'
    });
    
    if (prompt) {
      await openAiChatWithPrompt(prompt);
    }
  });

  const updateCommand = vscode.commands.registerCommand('workiz-pr-agent-fix.checkForUpdates', async () => {
    await checkForUpdates(context, true);
  });

  context.subscriptions.push(uriHandler, command, updateCommand);
}

async function handleFixUri(uri: vscode.Uri): Promise<void> {
  const params = new URLSearchParams(uri.query);
  
  const prompt = params.get('prompt') || '';
  const filePath = params.get('file') || '';
  const lineStr = params.get('line') || '1';
  const line = parseInt(lineStr, 10) || 1;

  console.log('Fix request:', { filePath, line, promptLength: prompt.length });

  if (filePath) {
    await openFileAtLine(filePath, line);
  }

  if (prompt) {
    await new Promise(resolve => setTimeout(resolve, 500));
    await openAiChatWithPrompt(prompt);
  }

  vscode.window.showInformationMessage('Fix loaded! Review the AI suggestion.');
}

async function openFileAtLine(filePath: string, line: number): Promise<void> {
  try {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    
    if (!workspaceFolders || workspaceFolders.length === 0) {
      vscode.window.showWarningMessage('No workspace folder open. Please open the project first.');
      return;
    }

    for (const folder of workspaceFolders) {
      const fullPath = path.join(folder.uri.fsPath, filePath);
      const fileUri = vscode.Uri.file(fullPath);

      try {
        await vscode.workspace.fs.stat(fileUri);

        const document = await vscode.workspace.openTextDocument(fileUri);
        const editor = await vscode.window.showTextDocument(document);

        const lineIndex = Math.max(0, line - 1);
        const position = new vscode.Position(lineIndex, 0);
        const range = new vscode.Range(position, position);
        
        editor.selection = new vscode.Selection(position, position);
        editor.revealRange(range, vscode.TextEditorRevealType.InCenter);

        console.log(`Opened file: ${fullPath} at line ${line}`);
        return;
      } catch {
        continue;
      }
    }

    vscode.window.showWarningMessage(`File not found: ${filePath}`);
  } catch (error) {
    console.error('Error opening file:', error);
    vscode.window.showErrorMessage(`Failed to open file: ${filePath}`);
  }
}

async function openAiChatWithPrompt(prompt: string): Promise<void> {
  try {
    await vscode.env.clipboard.writeText(prompt);
    console.log('Prompt copied to clipboard');

    const allCommands = await vscode.commands.getCommands(true);
    console.log('Available AI commands:', allCommands.filter(cmd => 
      cmd.includes('chat') || cmd.includes('composer') || cmd.includes('ai') || cmd.includes('Composer')
    ));

    const chatCommands = [
      { name: 'aichat.newchataction', args: [prompt] },
      { name: 'composer.startComposerPrompt', args: [prompt] },
      { name: 'cursorComposer.startComposer', args: [{ prompt }] },
      { name: 'composerMode.agent.startFromSelection', args: [{ prompt }] },
      { name: 'aichat.newagentchat', args: [] },
      { name: 'workbench.action.chat.newChat', args: [] },
    ];

    for (const cmd of chatCommands) {
      if (allCommands.includes(cmd.name)) {
        try {
          console.log(`Trying command: ${cmd.name}`);
          await vscode.commands.executeCommand(cmd.name, ...cmd.args);
          console.log(`Command ${cmd.name} executed successfully`);
          
          if (cmd.args.length === 0) {
            await new Promise(resolve => setTimeout(resolve, 500));
            try {
              await vscode.commands.executeCommand('editor.action.clipboardPasteAction');
              console.log('Pasted prompt from clipboard');
            } catch (pasteError) {
              console.log('Paste failed, prompt is in clipboard');
            }
          }
          
          return;
        } catch (e) {
          console.log(`Command ${cmd.name} failed:`, e);
        }
      }
    }

    vscode.window.showInformationMessage(
      '📋 Prompt copied to clipboard! Open AI chat (Cmd+L) and paste with Cmd+V.',
      'OK'
    );
  } catch (error) {
    console.error('Error opening AI chat:', error);
    vscode.window.showErrorMessage('Failed to open AI chat. Prompt is in clipboard - paste with Cmd+V.');
  }
}

async function checkForUpdates(context: vscode.ExtensionContext, manual: boolean = false): Promise<void> {
  const lastCheck = context.globalState.get<number>('lastUpdateCheck', 0);
  const now = Date.now();
  const oneDay = 24 * 60 * 60 * 1000;

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

async function installUpdate(release: GitHubRelease): Promise<void> {
  const vsixAsset = release.assets.find(asset => asset.name.endsWith('.vsix'));
  
  if (!vsixAsset) {
    vscode.window.showErrorMessage('No .vsix file found in the release. Please update manually.');
    vscode.env.openExternal(vscode.Uri.parse(release.html_url));
    return;
  }

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

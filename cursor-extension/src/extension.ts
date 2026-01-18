import * as vscode from 'vscode';
import * as path from 'path';
import * as https from 'https';

const GITHUB_REPO = 'Workiz/workiz-pr-agent';
const CURRENT_VERSION = '1.0.17';

let outputChannel: vscode.OutputChannel;

function log(message: string, data?: unknown): void {
  const timestamp = new Date().toISOString();
  const logLine = data 
    ? `[${timestamp}] ${message}: ${JSON.stringify(data, null, 2)}`
    : `[${timestamp}] ${message}`;
  console.log(logLine);
  outputChannel?.appendLine(logLine);
}

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
  outputChannel = vscode.window.createOutputChannel('Workiz PR Agent');
  outputChannel.show(true);
  
  log('Extension activated', { version: CURRENT_VERSION });

  checkForUpdates(context);

  const uriHandler = vscode.window.registerUriHandler({
    handleUri(uri: vscode.Uri): vscode.ProviderResult<void> {
      log('Received URI', uri.toString());
      
      if (uri.path === '/fix') {
        handleFixUri(uri);
      } else {
        log('Unknown path', uri.path);
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
  log('handleFixUri called', uri.query);
  const params = new URLSearchParams(uri.query);
  
  let prompt = params.get('prompt') || '';
  const promptId = params.get('id') || '';
  const baseUrl = params.get('baseUrl') || '';
  const filePath = params.get('file') || '';
  const lineStr = params.get('line') || '1';
  const line = parseInt(lineStr, 10) || 1;

  if (promptId && baseUrl && !prompt) {
    log('Fetching prompt from server', { promptId, baseUrl });
    const fetchedData = await fetchPromptFromServer(baseUrl, promptId);
    if (fetchedData) {
      prompt = fetchedData.prompt;
      log('Prompt fetched successfully', { promptLength: prompt.length });
    } else {
      log('Failed to fetch prompt from server');
      vscode.window.showErrorMessage('Failed to fetch prompt from server. It may have expired.');
      return;
    }
  }

  log('Parsed fix request', { filePath, line, promptLength: prompt.length, promptPreview: prompt.substring(0, 100) });

  if (filePath) {
    log('Opening file', { filePath, line });
    await openFileAtLine(filePath, line);
    log('File opened');
  }

  if (prompt) {
    log('Waiting before opening AI chat...');
    await new Promise(resolve => setTimeout(resolve, 500));
    log('Opening AI chat with prompt');
    await openAiChatWithPrompt(prompt);
    log('AI chat function completed');
  }

  vscode.window.showInformationMessage('Fix loaded! Check Output panel for logs.');
}

async function fetchPromptFromServer(baseUrl: string, promptId: string): Promise<{prompt: string, file?: string, line?: number} | null> {
  const url = `${baseUrl}/api/v1/prompt/${promptId}`;
  log('Fetching from URL', url);
  
  const https = await import('https');
  const http = await import('http');
  
  return new Promise((resolve) => {
    const protocol = url.startsWith('https') ? https : http;
    const request = protocol.get(url, (response) => {
      let data = '';
      response.on('data', (chunk) => { data += chunk; });
      response.on('end', () => {
        try {
          if (response.statusCode === 200) {
            const parsed = JSON.parse(data);
            log('Server response', { promptLength: parsed.prompt?.length });
            resolve(parsed);
          } else {
            log('Server returned error', { status: response.statusCode, data });
            resolve(null);
          }
        } catch (e) {
          log('Failed to parse server response', String(e));
          resolve(null);
        }
      });
    });
    
    request.on('error', (e) => {
      log('Request failed', String(e));
      resolve(null);
    });
    
    request.setTimeout(10000, () => {
      log('Request timed out');
      request.destroy();
      resolve(null);
    });
  });
}

async function openFileAtLine(filePath: string, line: number): Promise<void> {
  try {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    log('Workspace folders', workspaceFolders?.map(f => f.uri.fsPath));
    
    if (!workspaceFolders || workspaceFolders.length === 0) {
      log('No workspace folders found');
      vscode.window.showWarningMessage('No workspace folder open. Please open the project first.');
      return;
    }

    for (const folder of workspaceFolders) {
      const fullPath = path.join(folder.uri.fsPath, filePath);
      const fileUri = vscode.Uri.file(fullPath);
      log('Trying path', fullPath);

      try {
        await vscode.workspace.fs.stat(fileUri);
        log('File exists', fullPath);

        const document = await vscode.workspace.openTextDocument(fileUri);
        const editor = await vscode.window.showTextDocument(document);

        const lineIndex = Math.max(0, line - 1);
        const position = new vscode.Position(lineIndex, 0);
        const range = new vscode.Range(position, position);
        
        editor.selection = new vscode.Selection(position, position);
        editor.revealRange(range, vscode.TextEditorRevealType.InCenter);

        log('File opened successfully', { fullPath, line });
        return;
      } catch (e) {
        log('File not found in folder', { folder: folder.uri.fsPath, error: String(e) });
        continue;
      }
    }

    log('File not found in any workspace folder', filePath);
    vscode.window.showWarningMessage(`File not found: ${filePath}`);
  } catch (error) {
    log('Error opening file', { filePath, error: String(error) });
    vscode.window.showErrorMessage(`Failed to open file: ${filePath}`);
  }
}

async function openAiChatWithPrompt(prompt: string): Promise<void> {
  log('openAiChatWithPrompt called', { promptLength: prompt.length });
  
  await vscode.env.clipboard.writeText(prompt);
  log('Prompt copied to clipboard');

  log('Opening new agent chat');
  await vscode.commands.executeCommand('composer.newAgentChat');
  
  log('Waiting 1.5 seconds for chat to fully initialize');
  await new Promise(resolve => setTimeout(resolve, 1500));
  
  log('Focusing composer input');
  await vscode.commands.executeCommand('composer.focusComposer');
  
  log('Waiting 500ms for focus');
  await new Promise(resolve => setTimeout(resolve, 500));
  
  const clipboardCheck = await vscode.env.clipboard.readText();
  log('Clipboard verification', { 
    length: clipboardCheck.length, 
    promptLength: prompt.length,
    match: clipboardCheck.length === prompt.length
  });
  
  log('Executing paste');
  await vscode.commands.executeCommand('editor.action.clipboardPasteAction');
  
  log('Waiting 500ms after paste');
  await new Promise(resolve => setTimeout(resolve, 500));
  
  log('Paste complete - prompt is in clipboard if not fully pasted, press Cmd+V');
}

async function checkForUpdates(context: vscode.ExtensionContext, manual: boolean = false): Promise<void> {
  const lastCheck = context.globalState.get<number>('lastUpdateCheck', 0);
  const now = Date.now();
  const oneDay = 24 * 60 * 60 * 1000;

  if (!manual && (now - lastCheck) < oneDay) {
    log('Skipping update check - checked recently');
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
    log('Version check', { current: CURRENT_VERSION, latest: latestVersion });

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
    log('Error checking for updates', String(error));
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
            log('GitHub API returned status', res.statusCode);
            resolve(null);
          }
        } catch {
          resolve(null);
        }
      });
    });

    req.on('error', (error) => {
      log('Error fetching release', String(error));
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
  log('Extension deactivated');
}

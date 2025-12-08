from flask import Flask, jsonify, render_template, request, Response
from pathlib import Path
import subprocess
import json

# GitPython
from git import Repo, InvalidGitRepositoryError

app = Flask(__name__, template_folder='templates', static_folder='static')


def find_repo_root(start: Path) -> Path:
    root = start.resolve()
    while root != root.parent:
        if (root / '.git').exists():
            return root
        root = root.parent
    return start.resolve()


def get_repo_info(path: Path):
    repo = {}
    repo['name'] = path.name
    repo['path'] = str(path)
    try:
        r = Repo(path)
        remotes = []
        for remote in r.remotes:
            for url in remote.urls:
                remotes.append(f"{remote.name}\t{url}")
        repo['remotes'] = remotes

        branches = [b.name for b in r.branches]
        # add remote heads names
        branches += [h.name for h in r.remotes]
        repo['branches'] = branches

        commit = r.head.commit
        repo['last_commit'] = f"{commit.hexsha[:7]} - {commit.message.splitlines()[0]} ({commit.committed_datetime.isoformat()}) <{commit.author.name}>"

        files = [p.name for p in path.iterdir() if p.is_file()]
        repo['files'] = files
    except InvalidGitRepositoryError:
        repo['remotes'] = []
        repo['branches'] = []
        repo['last_commit'] = ''
        repo['files'] = [p.name for p in path.iterdir() if p.is_file()]
    except Exception as e:
        repo['remotes'] = [str(e)]
        repo['branches'] = []
        repo['last_commit'] = ''
        repo['files'] = []
    return repo


def _parse_github_remote_url(url: str):
    # support formats: git@github.com:owner/repo.git or https://github.com/owner/repo.git
    try:
        if url.startswith('git@'):
            # git@github.com:owner/repo.git
            _, path = url.split(':', 1)
            owner_repo = path
            if owner_repo.endswith('.git'):
                owner_repo = owner_repo[:-4]
            owner, repo = owner_repo.split('/', 1)
            return owner, repo

        # handle https:// or http://
        if url.startswith('http'):
            # strip possible trailing .git
            if url.endswith('.git'):
                url = url[:-4]
            parts = url.rstrip('/').split('/')
            # expect .../owner/repo
            if len(parts) >= 2:
                owner = parts[-2]
                repo = parts[-1]
                return owner, repo
    except Exception:
        return None, None
    return None, None


def get_open_prs(path: Path):
    # Determine owner/repo from remotes (prefer origin)
    try:
        r = Repo(path)
        origin = None
        for remote in r.remotes:
            if remote.name == 'origin':
                origin = next(iter(remote.urls), None)
                break
        if origin is None and r.remotes:
            origin = next(iter(r.remotes[0].urls), None)
    except Exception:
        origin = None

    if not origin:
        return {'error': 'no git remote found', 'prs': []}

    owner, repo = _parse_github_remote_url(origin)
    if not owner or not repo:
        return {'error': 'unable to parse remote url', 'prs': []}

    # Get token via helper (env or pr_agent/settings/.secrets.toml in repo root)
    gh_token = _get_github_token()
    headers = {'Accept': 'application/vnd.github+json'}
    if gh_token:
        headers['Authorization'] = f'token {gh_token}'

    import requests
    api = f'https://api.github.com/repos/{owner}/{repo}/pulls?state=open'
    try:
        r = requests.get(api, headers=headers, timeout=10)
        if r.status_code != 200:
            # include response text to aid debugging (e.g., 404 for wrong owner/repo)
            text = r.text
            return {'error': f'GitHub API status {r.status_code}: {text}', 'prs': []}
        items = r.json()
        prs = []
        for it in items:
            prs.append({
                'number': it.get('number'),
                'title': it.get('title'),
                'user': it.get('user', {}).get('login'),
                'html_url': it.get('html_url'),
                'created_at': it.get('created_at')
            })
        return {'error': None, 'prs': prs}
    except Exception as e:
        return {'error': str(e), 'prs': []}


def _get_github_token():
    import os
    gh_token = os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN')
    if gh_token:
        return gh_token
    # fallback to local secrets file located relative to the repository root
    try:
        import toml
        repo_root = find_repo_root(Path.cwd())
        sec_path = repo_root / 'pr_agent' / 'settings' / '.secrets.toml'
        if sec_path.is_file():
            data = toml.load(sec_path)
            gh = data.get('github') or {}
            gh_token = gh.get('user_token') or gh.get('user-token') or gh.get('token')
            return gh_token
    except Exception:
        return None
    return None


@app.route('/api/github/repos')
def github_repos():
    """List repositories accessible by the configured GitHub token.
    Falls back to public repos if no token is provided.
    """
    import requests
    token = _get_github_token()
    headers = {'Accept': 'application/vnd.github+json'}
    if token:
        headers['Authorization'] = f'token {token}'

    repos = []
    try:
        # user repos (includes org repos the user has access to)
        url = 'https://api.github.com/user/repos?per_page=100&type=all'
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return jsonify({'error': f'GitHub API status {r.status_code}: {r.text}', 'repos': []}), 200
        items = r.json()
        for it in items:
            repos.append({
                'full_name': it.get('full_name'),
                'name': it.get('name'),
                'owner': it.get('owner', {}).get('login'),
                'private': it.get('private'),
                'html_url': it.get('html_url')
            })
        return jsonify({'error': None, 'repos': repos})
    except Exception as e:
        return jsonify({'error': str(e), 'repos': []}), 200


@app.route('/api/github/repos/<owner>/<repo>/prs')
def github_repo_prs(owner, repo):
    import requests
    token = _get_github_token()
    headers = {'Accept': 'application/vnd.github+json'}
    if token:
        headers['Authorization'] = f'token {token}'
    api = f'https://api.github.com/repos/{owner}/{repo}/pulls?state=open&per_page=100'
    try:
        r = requests.get(api, headers=headers, timeout=10)
        if r.status_code != 200:
            return jsonify({'error': f'GitHub API status {r.status_code}: {r.text}', 'prs': []}), 200
        items = r.json()
        prs = []
        for it in items:
            prs.append({
                'number': it.get('number'),
                'title': it.get('title'),
                'user': it.get('user', {}).get('login'),
                'html_url': it.get('html_url'),
                'created_at': it.get('created_at')
            })
        return jsonify({'error': None, 'prs': prs}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'prs': []}), 200


@app.route('/api/github/repos/<owner>/<repo>/setup-automation', methods=['POST'])
def setup_repo_automation(owner, repo):
    """Setup GitHub Actions workflow for automated PR review, describe, and improve."""
    import requests
    import base64
    
    token = _get_github_token()
    if not token:
        return jsonify({'error': 'GitHub token not configured', 'success': False}), 200
    
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'token {token}'
    }
    
    # Workflow content
    workflow_content = """name: PR-Agent Automation

on:
  pull_request:
    types: [opened, reopened, synchronize]
  issue_comment:
    types: [created]

permissions:
  issues: write
  pull-requests: write
  contents: read

jobs:
  pr_agent_job:
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request' || (github.event_name == 'issue_comment' && github.event.issue.pull_request)
    name: Run PR-Agent
    steps:
      - name: PR Agent action step
        id: pragent
        uses: Codium-ai/pr-agent@main
        env:
          OPENAI_KEY: ${{ secrets.OPENAI_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_ACTION_CONFIG.AUTO_DESCRIBE: true
          GITHUB_ACTION_CONFIG.AUTO_REVIEW: true
          GITHUB_ACTION_CONFIG.AUTO_IMPROVE: true
"""
    
    try:
        # Check if workflow already exists
        workflow_path = '.github/workflows/pr-agent-automation.yml'
        check_url = f'https://api.github.com/repos/{owner}/{repo}/contents/{workflow_path}'
        check_response = requests.get(check_url, headers=headers, timeout=10)
        
        encoded_content = base64.b64encode(workflow_content.encode()).decode()
        
        if check_response.status_code == 200:
            # File exists, update it
            existing_data = check_response.json()
            sha = existing_data.get('sha')
            
            update_data = {
                'message': 'Update PR-Agent automation workflow',
                'content': encoded_content,
                'sha': sha
            }
            
            update_response = requests.put(check_url, headers=headers, json=update_data, timeout=10)
            
            if update_response.status_code in [200, 201]:
                return jsonify({
                    'success': True,
                    'message': 'Workflow updated successfully',
                    'action': 'updated'
                }), 200
            else:
                return jsonify({
                    'error': f'Failed to update workflow: {update_response.text}',
                    'success': False
                }), 200
        
        elif check_response.status_code == 404:
            # File doesn't exist, create it
            create_data = {
                'message': 'Add PR-Agent automation workflow',
                'content': encoded_content
            }
            
            create_response = requests.put(check_url, headers=headers, json=create_data, timeout=10)
            
            if create_response.status_code in [200, 201]:
                return jsonify({
                    'success': True,
                    'message': 'Workflow created successfully',
                    'action': 'created'
                }), 200
            else:
                return jsonify({
                    'error': f'Failed to create workflow: {create_response.text}',
                    'success': False
                }), 200
        
        else:
            return jsonify({
                'error': f'Failed to check workflow existence: {check_response.text}',
                'success': False
            }), 200
    
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 200


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/repos')
def repos():
    cwd = Path.cwd()
    root = find_repo_root(cwd)
    repo = get_repo_info(root)
    return jsonify([repo])


@app.route('/api/repos/<name>')
def repo_details(name):
    cwd = Path.cwd()
    root = find_repo_root(cwd)
    repo = get_repo_info(root)
    if repo['name'] != name:
        return jsonify({'error': 'repo not found'}), 404
    return jsonify(repo)


@app.route('/api/repos/<name>/prs')
def repo_prs(name):
    cwd = Path.cwd()
    root = find_repo_root(cwd)
    repo = get_repo_info(root)
    if repo['name'] != name:
        return jsonify({'error': 'repo not found'}), 404
    prs = get_open_prs(root)
    return jsonify(prs)


def stream_subprocess(cmd_list, cwd=None):
    process = subprocess.Popen(cmd_list, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    try:
        for line in iter(process.stdout.readline, ''):
            if line:
                yield line
        process.stdout.close()
        rc = process.wait()
        yield f"\nProcess exited with code {rc}\n"
    except GeneratorExit:
        try:
            process.kill()
        except Exception:
            pass


@app.route('/api/run', methods=['POST'])
def run_action():
    data = request.get_json() or {}
    action = data.get('action')
    pr_url = data.get('pr_url')
    repo = data.get('repo')
    if action not in ('review', 'describe', 'improve'):
        return jsonify({'error': 'invalid action'}), 400

    cwd = find_repo_root(Path.cwd())
    # command: run CLI in pr_agent folder; pass repo if provided via --repo
    cli_cwd = cwd / 'pr_agent'
    cmd = ['python3', 'cli.py']
    if pr_url:
        cmd.append(f'--pr_url={pr_url}')
    cmd.append(action)
    return Response(stream_subprocess(cmd, cwd=str(cli_cwd)), mimetype='text/plain')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)

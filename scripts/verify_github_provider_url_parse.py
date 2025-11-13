import sys
from urllib.parse import urlparse


def parse_pr_url(pr_url: str):
    parsed_url = urlparse(pr_url)

    # Normalize GitHub Enterprise API v3 URLs
    if parsed_url.path.startswith('/api/v3'):
        parsed_url = urlparse(pr_url.replace('/api/v3', ''))

    path_parts = parsed_url.path.strip('/').split('/')

    # GitHub REST API form: https://api.github.com/repos/<owner>/<repo>/pulls/<number>
    if 'api.github.com' in parsed_url.netloc or '/api/v3' in pr_url:
        if len(path_parts) < 5 or path_parts[3] != 'pulls':
            return None, None
        repo_name = '/'.join(path_parts[1:3])
        try:
            pr_number = int(path_parts[4])
        except ValueError:
            return None, None
        return repo_name, pr_number

    # GitHub HTML form: https://github.com/<owner>/<repo>/pull/<number>[...] 
    if len(path_parts) < 4 or path_parts[2] != 'pull':
        return None, None

    repo_name = '/'.join(path_parts[:2])
    try:
        pr_number = int(path_parts[3])
    except ValueError:
        return None, None

    return repo_name, pr_number


if __name__ == '__main__':
    urls = sys.argv[1:] or [
        'https://github.com/Codium-ai/pr-agent/pull/123',
        'https://api.github.com/repos/Codium-ai/pr-agent/pulls/123',
        'https://ghe.example.com/api/v3/repos/org/repo/pulls/123',
        'https://github.com/org/repo/pull/123/files',
    ]
    for u in urls:
        repo, num = parse_pr_url(u)
        print(f'{u} -> repo={repo!r}, pr_number={num!r}')
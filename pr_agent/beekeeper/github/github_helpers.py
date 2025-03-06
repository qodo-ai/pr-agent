from github import Github
from loguru import logger


def get_github_repo(repo_url, token):
    github = Github(token)
    return github.get_repo(repo_url)


def get_github_repo_contents(repo, target_folder='', branch='master'):
    start_path = target_folder
    try:
        return repo.get_contents(start_path, ref=branch)
    except Exception as e:
        logger.error(f"Error accessing path '{start_path}': {str(e)}")
        return {}



def get_all_files_of_type_in_repo_recursive(token, repo_url, target_folder, branch='master', file_type='.md'):
    repo = get_github_repo(repo_url, token)
    contents = get_github_repo_contents(repo, target_folder, branch)
    files = []
    while contents:
        content_file = contents.pop(0)
        if content_file.type == "dir":
            contents.extend(repo.get_contents(content_file.path, ref=branch))
        elif content_file.path.endswith(file_type):
            files.append(content_file)
    return files
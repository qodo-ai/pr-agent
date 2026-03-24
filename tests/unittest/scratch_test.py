import sys
import os
import re
from unittest.mock import MagicMock, patch

# Add CWD to sys.path
sys.path.insert(0, os.getcwd())

# Mock settings before importing GitLabProvider
with patch('pr_agent.git_providers.gitlab_provider.gitlab.Gitlab'), \
     patch('pr_agent.git_providers.gitlab_provider.get_settings') as mock_settings:
    mock_settings.return_value.get.side_effect = lambda key, default=None: {
        "GITLAB.URL": "https://gitlab.com",
        "GITLAB.PERSONAL_ACCESS_TOKEN": "fake_token"
    }.get(key, default)
    
    from pr_agent.git_providers.gitlab_provider import GitLabProvider

def test_extract_toml():
    provider = GitLabProvider("https://gitlab.com/test/repo/-/merge_requests/1")
    content = "Some description\n\n```toml\nkey = \"value\"\n```\nMore text"
    extracted = provider._extract_toml_from_markdown(content)
    print(f"Extracted toml: {extracted}")
    assert extracted == 'key = "value"'

    content_ini = "Some description\n\n```ini\nkey = \"value_ini\"\n```\nMore text"
    extracted_ini = provider._extract_toml_from_markdown(content_ini)
    print(f"Extracted ini: {extracted_ini}")
    assert extracted_ini == 'key = "value_ini"'

def test_wiki_fallback():
    mock_gitlab_client = MagicMock()
    mock_project = MagicMock()
    mock_gitlab_client.projects.get.return_value = mock_project
    
    with patch('pr_agent.git_providers.gitlab_provider.get_settings') as mock_settings:
        mock_settings.return_value.get.side_effect = lambda key, default=None: {
            "GITLAB.URL": "https://gitlab.com",
            "GITLAB.PERSONAL_ACCESS_TOKEN": "fake_token"
        }.get(key, default)
        
        mock_settings.return_value.config.get.side_effect = lambda key, default=None: {
            "use_wiki_settings_file": True
        }.get(key, default)

        provider = GitLabProvider("https://gitlab.com/test/repo/-/merge_requests/1")
        provider.gl = mock_gitlab_client
        
        # Mock main repo file fail
        mock_project.files.get.side_effect = Exception("404")
        
        # Mock wiki page success
        mock_wiki_page = MagicMock()
        mock_wiki_page.content = 'key = "wiki_value"'
        mock_project.wikis.get.return_value = mock_wiki_page
        
        settings = provider.get_repo_settings()
        print(f"Settings from wiki: {settings}")
        assert settings == b'key = "wiki_value"'
        assert isinstance(settings, bytes)

if __name__ == "__main__":
    try:
        test_extract_toml()
        test_wiki_fallback()
        print("All manual tests passed!")
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

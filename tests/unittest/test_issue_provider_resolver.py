from pr_agent.issue_providers.resolver import resolve_issue_provider_name


def test_resolve_issue_provider_defaults_to_git_provider():
    assert resolve_issue_provider_name("auto", "gitlab") == "gitlab"
    assert resolve_issue_provider_name("auto", "github") == "github"


def test_resolve_issue_provider_explicit_choice():
    assert resolve_issue_provider_name("jira", "gitlab") == "jira"


def test_resolve_issue_provider_handles_callable_git_provider():
    def provider_name():
        return "CodeCommit"

    assert resolve_issue_provider_name("auto", provider_name) == "codecommit"

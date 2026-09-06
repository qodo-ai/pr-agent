"""How far a bare `#123` reference is followed is a per-repository decision.

A bare number is as likely to be an error code as an issue, so the default bound stays at
four digits. Repositories whose issue numbers have outgrown that raise the bound instead of
losing ticket compliance for every `Fixes #12345`.
"""
import pytest

from pr_agent.config_loader import get_settings
from pr_agent.tools.ticket_pr_compliance_check import (
    DEFAULT_MAX_SHORTHAND_ISSUE_DIGITS,
    extract_ticket_links_from_pr_description,
    get_max_shorthand_issue_digits,
)

REPO = "org/repo"
BASE = "https://github.com"


def _links(description):
    return extract_ticket_links_from_pr_description(description, REPO, BASE)


@pytest.fixture
def max_digits(monkeypatch):
    def _set(value):
        monkeypatch.setattr(get_settings().config, "max_shorthand_issue_digits", value, raising=False)
    return _set


@pytest.mark.parametrize("number", ["1", "42", "999", "1234"])
def test_a_short_reference_is_extracted_by_default(number):
    assert _links(f"Fixes #{number}") == [f"{BASE}/{REPO}/issues/{number}"]


@pytest.mark.parametrize("number", ["12345", "123456"])
def test_a_long_reference_is_ignored_by_default(number):
    """Control: the shipped bound is unchanged, so nothing new is followed."""
    assert _links(f"Fixes #{number}") == []


@pytest.mark.parametrize("number", ["12345", "123456", "1234567"])
def test_a_long_reference_is_extracted_once_the_bound_is_raised(max_digits, number):
    max_digits(7)

    assert _links(f"Fixes #{number}") == [f"{BASE}/{REPO}/issues/{number}"]


def test_the_bound_still_applies_once_raised(max_digits):
    max_digits(5)

    assert _links("Fixes #12345") == [f"{BASE}/{REPO}/issues/12345"]
    assert _links("Fixes #123456") == []


@pytest.mark.parametrize("value", ["not a number", None, "", 0, -3])
def test_an_unusable_bound_falls_back_to_the_default(max_digits, value):
    max_digits(value)

    assert get_max_shorthand_issue_digits() == DEFAULT_MAX_SHORTHAND_ISSUE_DIGITS
    assert _links("Fixes #1234") == [f"{BASE}/{REPO}/issues/1234"]
    assert _links("Fixes #12345") == []


def test_a_numeric_string_bound_is_accepted(max_digits):
    """Environment overrides arrive as strings."""
    max_digits("6")

    assert _links("Fixes #123456") == [f"{BASE}/{REPO}/issues/123456"]


def test_a_full_url_is_not_bounded():
    """Control: an explicit URL is unambiguous, so it never had a length bound."""
    url = f"{BASE}/{REPO}/issues/1234567"

    assert _links(f"Fixes {url}") == [url]


def test_a_cross_repo_shorthand_is_not_bounded():
    """Control: owner/repo#123 names its repository, so it is unambiguous too."""
    assert _links("Fixes other/project#12345") == [f"{BASE}/other/project/issues/12345"]

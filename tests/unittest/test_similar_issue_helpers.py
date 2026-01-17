from unittest.mock import MagicMock

from pr_agent.algo.ticket_utils import find_jira_keys
from pr_agent.tools.pr_similar_issue import PRSimilarIssue


def test_build_query_from_mr_includes_title_and_description():
    tool = PRSimilarIssue.__new__(PRSimilarIssue)
    mr = MagicMock()
    mr.title = "Sample MR"
    mr.description = "Some description"

    query = tool._build_query_from_mr(mr)

    assert query == 'MR Title: "Sample MR"\n\nMR Description:\nSome description'


def test_get_issue_number_prefers_iid():
    tool = PRSimilarIssue.__new__(PRSimilarIssue)
    issue = MagicMock()
    issue.iid = "42"

    assert tool._get_issue_number(issue) == 42


def test_get_qdrant_vector_size_from_object():
    tool = PRSimilarIssue.__new__(PRSimilarIssue)
    tool.index_name = "issues"
    tool.qdrant = MagicMock()

    vectors = MagicMock()
    vectors.size = 1024
    info = MagicMock()
    info.config.params.vectors = vectors
    tool.qdrant.get_collection.return_value = info

    assert tool._get_qdrant_vector_size() == 1024


def test_extract_issue_iid_from_text():
    tool = PRSimilarIssue.__new__(PRSimilarIssue)

    assert tool._extract_issue_iid_from_text("Relates to #12 and #3") == 12
    assert tool._extract_issue_iid_from_text("No references here") is None


def test_find_jira_keys_extracts_unique():
    keys = find_jira_keys("Fixes ABC-123 and https://jira.example.com/browse/ABC-123")
    assert keys == ["ABC-123"]

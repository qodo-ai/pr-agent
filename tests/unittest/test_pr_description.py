import pytest
import yaml
from unittest.mock import MagicMock, patch
from pr_agent.tools.pr_description import PRDescription

KEYS_FIX = ["filename:", "language:", "changes_summary:", "changes_title:", "description:", "title:"]

def _make_instance(prediction_yaml: str):
    """Create a PRDescription instance, bypassing __init__."""
    with patch.object(PRDescription, '__init__', lambda self, *a, **kw: None):
        obj = PRDescription.__new__(PRDescription)
    obj.prediction = prediction_yaml
    obj.keys_fix = KEYS_FIX
    obj.user_description = ""
    return obj


def _mock_settings():
    """Mock get_settings used by _prepare_data."""
    settings = MagicMock()
    settings.pr_description.add_original_user_description = False
    return settings


def _prediction_with_diagram(diagram_value: str) -> str:
    """Build a minimal YAML prediction string that includes changes_diagram."""
    return yaml.dump({
        'title': 'test',
        'description': 'test',
        'changes_diagram': diagram_value,
    })


class TestPRDescriptionDiagram:

    @patch('pr_agent.tools.pr_description.get_settings')
    def test_diagram_not_starting_with_fence_is_removed(self, mock_get_settings):
        mock_get_settings.return_value = _mock_settings()
        obj = _make_instance(_prediction_with_diagram('graph LR\nA --> B'))
        obj._prepare_data()
        assert 'changes_diagram' not in obj.data

    @patch('pr_agent.tools.pr_description.get_settings')
    def test_diagram_missing_closing_fence_is_appended(self, mock_get_settings):
        mock_get_settings.return_value = _mock_settings()
        obj = _make_instance(_prediction_with_diagram('```mermaid\ngraph LR\nA --> B'))
        obj._prepare_data()
        assert obj.data['changes_diagram'] == '\n```mermaid\ngraph LR\nA --> B\n```'

    @patch('pr_agent.tools.pr_description.get_settings')
    def test_backticks_inside_label_are_removed(self, mock_get_settings):
        mock_get_settings.return_value = _mock_settings()
        obj = _make_instance(_prediction_with_diagram('```mermaid\ngraph LR\nA["`file`"] --> B\n```'))
        obj._prepare_data()
        assert obj.data['changes_diagram'] == '\n```mermaid\ngraph LR\nA["file"] --> B\n```'

    @patch('pr_agent.tools.pr_description.get_settings')
    def test_backticks_outside_label_are_kept(self, mock_get_settings):
        mock_get_settings.return_value = _mock_settings()
        obj = _make_instance(_prediction_with_diagram('```mermaid\ngraph LR\nA["`file`"] -->|`edge`| B\n```'))
        obj._prepare_data()
        assert obj.data['changes_diagram'] == '\n```mermaid\ngraph LR\nA["file"] -->|`edge`| B\n```'

    @patch('pr_agent.tools.pr_description.get_settings')
    def test_normal_diagram_only_adds_newline(self, mock_get_settings):
        mock_get_settings.return_value = _mock_settings()
        obj = _make_instance(_prediction_with_diagram('```mermaid\ngraph LR\nA["file.py"] --> B["output"]\n```'))
        obj._prepare_data()
        assert obj.data['changes_diagram'] == '\n```mermaid\ngraph LR\nA["file.py"] --> B["output"]\n```'

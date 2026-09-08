import importlib.util
import re
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[2] / "scripts"
CONFIG_TOML = SCRIPTS_DIR.parent / "pr_agent/settings/configuration.toml"
OUTPUT_PAGE = SCRIPTS_DIR.parent / "docs/docs/usage-guide/configuration_reference.md"

_GENERATOR = "generate_config_reference"
_spec = importlib.util.spec_from_file_location(_GENERATOR, SCRIPTS_DIR / f"{_GENERATOR}.py")
_script = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_script)
load_sections = _script.load_sections


def test_config_reference_covers_every_active_key():
    text = CONFIG_TOML.read_text(encoding="utf-8")
    sections = load_sections(text)
    rendered_keys = sum(len(section["keys"]) for section in sections)
    expected_keys = len(re.findall(r"^[a-zA-Z0-9_]+\s*=", text, re.M))
    assert rendered_keys == expected_keys
    assert rendered_keys == 292

    all_keys = {key["key"] for section in sections for key in section["keys"]}
    assert {"model", "enable_auto_approval", "reaction_on_start", "reaction_on_failure"} <= all_keys
    assert {"force_streaming_custom_llm_provider", "cache_control_injection_points"} <= all_keys


def test_config_reference_page_lists_every_active_key():
    toml_keys = {key["key"] for section in load_sections(CONFIG_TOML.read_text(encoding="utf-8")) for key in section["keys"]}
    documented = {
        row.group(1)
        for line in OUTPUT_PAGE.read_text(encoding="utf-8").splitlines()
        if line.startswith("| ")
        for row in [re.match(r"\| `([^`]+)` \|", line)]
        if row
    }
    assert documented == toml_keys, (
        "docs/docs/usage-guide/configuration_reference.md is out of date; "
        "run scripts/generate_config_reference.py"
    )

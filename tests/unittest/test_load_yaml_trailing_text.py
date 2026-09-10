"""Drop a sign-off the model added after the wrapper's closing fence."""
from pr_agent.algo.utils import load_yaml

SIGN_OFF = "\n\nI reviewed the diff and found nothing else worth flagging."

# The prompts ask for YAML "and nothing else", but 8 of the 12 user prompts end
# with a dangling open ```yaml, so a reply carries either both fences or, more
# often, a closing one only.
WRAPPED = "```yaml\ncode_suggestions: []\n```"
PRIMED = "code_suggestions: []\n```"


def test_a_wrapped_mapping_survives_a_sign_off():
    """The snippet fallback cannot recover this: its pattern requires the
    closing fence to end the response."""
    assert load_yaml(WRAPPED + SIGN_OFF, first_key="code_suggestions",
                     last_key="label") == {"code_suggestions": []}


def test_a_primed_mapping_survives_a_sign_off():
    """A reply with a closing fence and no opening one cannot be recovered by
    any fence pattern, since there is no pair to match."""
    assert load_yaml(PRIMED + SIGN_OFF, first_key="code_suggestions",
                     last_key="label") == {"code_suggestions": []}


def test_a_sign_off_is_not_folded_into_a_block_scalar():
    """Worse than a parse failure: a single block scalar absorbs the fence and
    the remark as part of its value, so the answer is published corrupted."""
    wrapped = "```yaml\nresponse: |\n  hello\n```" + SIGN_OFF

    assert load_yaml(wrapped)["response"].strip() == "hello"


def test_an_answer_following_a_fenced_example_is_not_truncated():
    """Dropping text after that fence would leave a plain scalar, so the
    response must be left alone for the fallbacks to handle."""
    assert load_yaml("```\nexample\n```\nresponse: hello") == {}


def test_a_fence_inside_a_block_scalar_is_not_treated_as_the_wrapper():
    """Only a fence at content level closes the wrapper."""
    answer = load_yaml("response: |\n  Use this:\n  ```python\n  print(1)\n  ```\n")

    assert answer["response"].count("```") == 2


def test_trailing_whitespace_after_the_fence_changes_nothing():
    assert load_yaml("```yaml\nresponse: |\n  hello\n```  \n\n")["response"].strip() == "hello"


def test_a_second_fenced_block_is_left_to_the_existing_behaviour():
    """Nothing follows the last fence, so there is no sign-off to drop."""
    reply = "```yaml\nresponse: |\n  hello\n```\n\n```\nprint(1)\n```"

    assert "hello" in load_yaml(reply)["response"]

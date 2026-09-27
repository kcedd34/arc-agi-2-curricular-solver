from src.curriculum.program_probe.extract import extract_code, rule_line
from src.curriculum.program_probe.prompt import GUIDED, PLAIN, SIGNATURE, base_response_head, build_prompt, chat_messages
from src.curriculum.program_probe.render import render_grid, render_pair

PAIRS = [([[0, 1], [2, 0]], [[1, 0, 0], [0, 2, 0]])]


def test_grid_uses_dot_for_background_and_digits_for_colours():
    assert render_grid([[0, 1, 0], [2, 0, 9]]) == [".1.", "2.9"]


def test_pair_is_side_by_side_and_pads_the_shorter_grid():
    text = render_pair(1, [[0, 1]], [[1, 0], [2, 2]])
    assert text.splitlines() == ["Example 1: input | output", ".1   1.", "     22"]


def test_plain_and_guided_prompts_differ_only_in_the_reply_rule():
    plain, guided = build_prompt(PAIRS, PLAIN), build_prompt(PAIRS, GUIDED)
    assert "code only" in plain.user_text and "# Rule:" in guided.user_text
    assert SIGNATURE.split(" ->")[0] in plain.base_text
    assert "```" not in plain.user_text
    assert plain.base_text.endswith(SIGNATURE + "\n") and guided.base_text.endswith("# Rule (one sentence): ")


def test_chat_messages_hold_the_user_text_only():
    prompt = build_prompt(PAIRS, PLAIN)
    assert chat_messages(prompt) == [{"role": "user", "content": prompt.user_text}]


def test_extract_takes_the_first_fenced_block():
    text = "```python\ndef solve(grid):\n    return grid\n```\ntrailing prose"
    assert extract_code(text) == "def solve(grid):\n    return grid\n"


def test_extract_accepts_an_unclosed_fence_and_rejects_missing_solve():
    assert extract_code("```python\ndef solve(grid):\n    return grid") is not None
    assert extract_code("```python\ndef other():\n    pass\n```") is None


def test_base_completion_is_rejoined_with_its_prefill():
    completion = "    return grid\n```\nmore"
    code = extract_code(base_response_head(PLAIN) + completion)
    assert code.startswith("def solve(grid: list[list[int]])") and code.endswith("return grid\n")


def test_rule_line_reads_the_leading_comment_only():
    assert rule_line("# Rule: cells change\ndef solve(g):\n    return g").startswith("# Rule")
    assert rule_line("def solve(g):\n    # Rule: x\n    return g") == ""

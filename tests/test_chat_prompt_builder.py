from src.solvers.neural.chat_prompt_builder import (
    CHAT_SYSTEM_PROMPT,
    build_chat_inference_prompt,
    build_chat_training_example,
)
from src.utils.task_loader import Pair


class _FakeTokenizer:
    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        rendered = "".join(f"<{m['role']}>{m['content']}</{m['role']}>" for m in messages)
        if add_generation_prompt:
            rendered += "<assistant>"
        return rendered


def test_build_chat_training_example_includes_system_user_assistant_turns():
    pair = Pair(input=[[1, 2]], output=[[3, 4]])
    text = build_chat_training_example(pair, _FakeTokenizer())
    assert f"<system>{CHAT_SYSTEM_PROMPT}</system>" in text
    assert "<user>Input:\n12</user>" in text
    assert "<assistant>34</assistant>" in text


def test_build_chat_inference_prompt_has_no_assistant_content_and_opens_generation():
    prompt = build_chat_inference_prompt([[5, 6]], _FakeTokenizer())
    assert "<user>Input:\n56</user>" in prompt
    assert prompt.endswith("<assistant>")
    assert "34" not in prompt

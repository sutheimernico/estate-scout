"""The honesty contract: system prompt encodes the rules, every response carries a disclaimer."""

from estatescout.assistant.assistant import DISCLAIMER, SYSTEM_PROMPT, Assistant, AssistantResponse
from estatescout.assistant.chat import FakeChat


def test_system_prompt_encodes_the_core_rules():
    p = SYSTEM_PROMPT.lower()
    assert "niemals selbst" in p  # the model must not compute numbers
    assert "tool" in p  # numbers come from tools
    assert "quelle" in p  # cite sources
    assert "keine steuer" in p  # not advice


def test_every_response_carries_the_disclaimer():
    model = FakeChat([{"role": "assistant", "content": "ok"}])
    resp = Assistant(model).ask("Was ist ein Kaufpreisfaktor?")
    assert resp.disclaimer == DISCLAIMER
    assert "keine" in resp.disclaimer.lower()


def test_disclaimer_is_the_default_on_the_dataclass():
    assert AssistantResponse(answer="x").disclaimer == DISCLAIMER

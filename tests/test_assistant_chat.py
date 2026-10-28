"""Tests for the chat-model seam: FakeChat scripting and OllamaChat over MockTransport."""

import httpx
import pytest

from estatescout.assistant.chat import ChatModel, FakeChat, OllamaChat, OllamaUnavailable


def test_fake_chat_satisfies_protocol_and_scripts_in_order():
    fake = FakeChat(
        [{"role": "assistant", "content": "one"}, {"role": "assistant", "content": "two"}]
    )
    assert isinstance(fake, ChatModel)
    assert fake.chat([{"role": "user", "content": "x"}])["content"] == "one"
    assert fake.chat([{"role": "user", "content": "y"}])["content"] == "two"
    assert len(fake.calls) == 2


def test_ollama_chat_posts_messages_and_tools():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        import json

        seen["path"] = request.url.path
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"message": {"role": "assistant", "content": "hi"}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    model = OllamaChat(model="qwen2.5:7b", host="http://h:11434", client=client)
    msg = model.chat([{"role": "user", "content": "q"}], tools=[{"type": "function"}])
    assert msg == {"role": "assistant", "content": "hi"}
    assert seen["path"] == "/api/chat"
    assert seen["body"]["tools"] == [{"type": "function"}]
    assert seen["body"]["stream"] is False


def test_ollama_chat_maps_connection_error_to_unavailable():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    client = httpx.Client(transport=httpx.MockTransport(handler))
    model = OllamaChat(host="http://h:11434", client=client)
    with pytest.raises(OllamaUnavailable):
        model.chat([{"role": "user", "content": "q"}])


def _chat_with(handler) -> OllamaChat:
    client = httpx.Client(transport=httpx.MockTransport(handler))
    return OllamaChat(model="qwen2.5:7b", host="http://h:11434", client=client, timeout=7)


def test_ollama_chat_unreachable_message_names_the_host():
    def handler(request):
        raise httpx.ConnectError("refused", request=request)

    with pytest.raises(OllamaUnavailable, match="http://h:11434"):
        _chat_with(handler).chat([{"role": "user", "content": "q"}])


def test_ollama_chat_timeout_is_not_reported_as_unreachable():
    from estatescout.errors import OllamaTimeout

    def handler(request):
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(OllamaTimeout, match="zu langsam") as info:
        _chat_with(handler).chat([{"role": "user", "content": "q"}])
    assert not isinstance(info.value, OllamaUnavailable)


def test_ollama_chat_missing_model_names_model_and_pull_command():
    from estatescout.errors import OllamaModelMissing

    def handler(request):
        return httpx.Response(404, json={"error": 'model "qwen2.5:7b" not found, try pulling it'})

    with pytest.raises(OllamaModelMissing, match="ollama pull qwen2.5:7b"):
        _chat_with(handler).chat([{"role": "user", "content": "q"}])


def test_ollama_chat_other_error_status_carries_ollama_text():
    from estatescout.errors import OllamaFailed

    def handler(request):
        return httpx.Response(500, json={"error": "out of memory"})

    with pytest.raises(OllamaFailed, match="out of memory"):
        _chat_with(handler).chat([{"role": "user", "content": "q"}])

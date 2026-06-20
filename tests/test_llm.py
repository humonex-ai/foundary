"""Tests for services.llm — no network; a fake Anthropic client is injected."""

import pytest

from services.config import Config, ConfigError
from services.llm import LLMClient, LLMError


class _Block:
    def __init__(self, type, text=None):
        self.type = type
        self.text = text


class _Response:
    def __init__(self, content):
        self.content = content


class FakeMessages:
    """Records the last create() call and returns a canned response."""

    def __init__(self, response=None, raises=None):
        self._response = response
        self._raises = raises
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        if self._raises is not None:
            raise self._raises
        return self._response


class FakeClient:
    def __init__(self, response=None, raises=None):
        self.messages = FakeMessages(response=response, raises=raises)


def _config():
    return Config(anthropic_api_key="sk-test", model="claude-sonnet-4-6")


def test_real_client_without_key_raises():
    # No injected client + empty key -> clear ConfigError at construction.
    with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY is required"):
        LLMClient(Config(anthropic_api_key=""))


def test_injected_client_needs_no_key():
    # Tests/primary code inject a client and never need a key.
    client = FakeClient(response=_Response([_Block("text", "ok")]))
    llm = LLMClient(Config(anthropic_api_key=""), client=client)
    assert llm.complete("p") == "ok"


def test_complete_returns_text():
    client = FakeClient(response=_Response([_Block("text", "Hello world")]))
    llm = LLMClient(_config(), client=client)
    assert llm.complete("hi") == "Hello world"


def test_complete_passes_model_and_prompt():
    client = FakeClient(response=_Response([_Block("text", "ok")]))
    llm = LLMClient(_config(), client=client)
    llm.complete("the prompt", system="be terse", max_tokens=123)
    kwargs = client.messages.last_kwargs
    assert kwargs["model"] == "claude-sonnet-4-6"
    assert kwargs["max_tokens"] == 123
    assert kwargs["system"] == "be terse"
    assert kwargs["messages"] == [{"role": "user", "content": "the prompt"}]


def test_complete_omits_system_when_none():
    client = FakeClient(response=_Response([_Block("text", "ok")]))
    llm = LLMClient(_config(), client=client)
    llm.complete("p")
    assert "system" not in client.messages.last_kwargs


def test_complete_joins_multiple_text_blocks():
    client = FakeClient(
        response=_Response([_Block("text", "a"), _Block("text", "b")])
    )
    llm = LLMClient(_config(), client=client)
    assert llm.complete("p") == "ab"


def test_complete_skips_non_text_blocks():
    client = FakeClient(
        response=_Response([_Block("tool_use"), _Block("text", "kept")])
    )
    llm = LLMClient(_config(), client=client)
    assert llm.complete("p") == "kept"


def test_empty_content_raises():
    client = FakeClient(response=_Response([]))
    llm = LLMClient(_config(), client=client)
    with pytest.raises(LLMError):
        llm.complete("p")


def test_no_text_blocks_raises():
    client = FakeClient(response=_Response([_Block("tool_use")]))
    llm = LLMClient(_config(), client=client)
    with pytest.raises(LLMError):
        llm.complete("p")


def test_sdk_error_wrapped():
    client = FakeClient(raises=RuntimeError("boom"))
    llm = LLMClient(_config(), client=client)
    with pytest.raises(LLMError, match="LLM request failed"):
        llm.complete("p")

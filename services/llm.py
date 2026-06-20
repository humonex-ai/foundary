"""LLM client wrapper.

A thin layer over the Anthropic SDK (``06-decisions.md`` D-010). Agents call
:meth:`LLMClient.complete` with a prompt and an optional system message and get
back plain text. Nothing agent-specific lives here — no prompt templates, no
artifact knowledge (that is WO-002 / WO-003 and out of scope for WO-001).
"""

from __future__ import annotations

from typing import Any

from services.config import Config

# Conservative default cap on a single completion. Overridable per call.
DEFAULT_MAX_TOKENS = 8192


class LLMError(RuntimeError):
    """Raised when the LLM call fails or returns an unusable response."""


class LLMClient:
    """Thin wrapper over the Anthropic Messages API.

    ``client`` is injectable so tests can pass a fake and avoid network calls.
    When omitted, a real ``anthropic.Anthropic`` is created from ``config``.
    """

    def __init__(self, config: Config, client: Any | None = None) -> None:
        self._config = config
        if client is not None:
            self._client = client
        else:
            # Imported lazily so the rest of the services layer (config, artifact
            # I/O) is usable without the anthropic package installed.
            from anthropic import Anthropic

            self._client = Anthropic(api_key=config.anthropic_api_key)

    def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        """Send a single user prompt and return the model's text response.

        ``system`` sets the system message when provided. Raises
        :class:`LLMError` on an empty or unexpected response.
        """
        kwargs: dict[str, Any] = {
            "model": self._config.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system is not None:
            kwargs["system"] = system

        try:
            response = self._client.messages.create(**kwargs)
        except Exception as exc:  # surface SDK/transport errors uniformly
            raise LLMError(f"LLM request failed: {exc}") from exc

        return self._extract_text(response)

    @staticmethod
    def _extract_text(response: Any) -> str:
        """Pull the text out of a Messages API response.

        The response ``content`` is a list of blocks; join the text of every
        text block. Raises :class:`LLMError` if no text is present.
        """
        blocks = getattr(response, "content", None)
        if not blocks:
            raise LLMError("LLM response had no content.")

        parts = [
            block.text
            for block in blocks
            if getattr(block, "type", None) == "text" and getattr(block, "text", None)
        ]
        if not parts:
            raise LLMError("LLM response contained no text blocks.")

        return "".join(parts)

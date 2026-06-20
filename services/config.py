"""Configuration for Foundry services.

A single ``Config`` object holds everything the services layer needs: the
Anthropic credentials, which model to call, and where generated artifacts live.
Loaded from the environment via :meth:`Config.from_env`.

Kept deliberately small (``06-decisions.md`` D-010). No settings framework — a
plain pydantic model plus an explicit environment reader.
"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic import BaseModel, Field

# Default model. Overridable via FOUNDRY_MODEL. See `06-decisions.md` D-006
# (single model per artifact in V1).
DEFAULT_MODEL = "claude-sonnet-4-6"

# Default output root for generated artifacts (`02-architecture.md`, Output
# Location; D-008). Each project gets its own subdirectory.
DEFAULT_PROJECTS_DIR = "projects"


class ConfigError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


class Config(BaseModel):
    """Resolved configuration for the services layer."""

    anthropic_api_key: str = Field(..., min_length=1)
    model: str = DEFAULT_MODEL
    projects_dir: Path = Field(default=Path(DEFAULT_PROJECTS_DIR))
    # Execution V1 (GitHub Issue sync). Optional — only the GitHub commands need
    # them; planning and tests do not.
    github_token: str = ""
    default_repo: str = ""

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "Config":
        """Build a ``Config`` from environment variables.

        Reads ``ANTHROPIC_API_KEY`` (required), ``FOUNDRY_MODEL`` (optional),
        ``FOUNDRY_PROJECTS_DIR`` (optional), and for Execution V1
        ``GITHUB_TOKEN`` / ``FOUNDRY_DEFAULT_REPO`` (optional). ``env`` defaults
        to ``os.environ``; pass a dict to load from an explicit mapping (tests).
        """
        source = os.environ if env is None else env

        api_key = source.get("ANTHROPIC_API_KEY", "").strip()
        if not api_key:
            raise ConfigError(
                "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and "
                "fill it in, or export the variable."
            )

        model = source.get("FOUNDRY_MODEL", "").strip() or DEFAULT_MODEL
        projects_dir = source.get("FOUNDRY_PROJECTS_DIR", "").strip() or DEFAULT_PROJECTS_DIR

        return cls(
            anthropic_api_key=api_key,
            model=model,
            projects_dir=Path(projects_dir),
            github_token=source.get("GITHUB_TOKEN", "").strip(),
            default_repo=source.get("FOUNDRY_DEFAULT_REPO", "").strip(),
        )

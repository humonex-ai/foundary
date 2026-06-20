"""Tests for the Architecture agent (WO-004). No network — a fake LLM is injected."""

from pathlib import Path

import pytest

from agents.architecture import build_prompt, generate_architecture
from services.artifacts import ArtifactError, read_artifact, write_artifact
from services.config import Config

VISION_DOC = """\
# Vision — acme

## Problem
Support agents waste time.

## Users
Tier-1 support agents.

## Goals
Faster ticket handling.

## Non-Goals
Not a CRM.

## Success Criteria
Handle time < 3 min.

## Assumptions
Shopify in use.
"""

ARCHITECTURE_OUTPUT = """\
# Architecture — acme

## Overview
A CLI worker enriches tickets.

## Components
Poller, mapper, writer.

## Data & Control Flow
Poll, map, write back.

## Boundaries
No CRM, no billing.

## Tech Stack
Python, CLI.

## Assumptions
Zendesk API exposes order IDs.
"""


class FakeLLM:
    """Captures the prompt/system and returns a canned response."""

    def __init__(self, response: str):
        self._response = response
        self.prompt = None
        self.system = None
        self.calls = 0

    def complete(self, prompt: str, *, system=None, max_tokens=8192) -> str:
        self.prompt = prompt
        self.system = system
        self.calls += 1
        return self._response


def _config(tmp_path: Path) -> Config:
    return Config(anthropic_api_key="sk-test", projects_dir=tmp_path / "projects")


def _write_vision(cfg, project="acme", doc=VISION_DOC):
    write_artifact(cfg, project, "00-vision.md", doc)


def test_generates_and_writes_architecture(tmp_path):
    cfg = _config(tmp_path)
    _write_vision(cfg)
    llm = FakeLLM(ARCHITECTURE_OUTPUT)

    path = generate_architecture(cfg, "acme", llm=llm)

    assert path == cfg.projects_dir / "acme" / "01-architecture.md"
    assert path.is_file()
    assert read_artifact(cfg, "acme", "01-architecture.md") == ARCHITECTURE_OUTPUT
    assert llm.calls == 1


def test_prompt_includes_vision_and_template(tmp_path):
    cfg = _config(tmp_path)
    _write_vision(cfg)
    llm = FakeLLM(ARCHITECTURE_OUTPUT)

    generate_architecture(cfg, "acme", llm=llm)

    # Vision content reached the model.
    assert "Support agents waste time." in llm.prompt
    # Architecture skeleton headers reached the model.
    assert "## Components" in llm.prompt
    assert "## Boundaries" in llm.prompt
    # System prompt establishes the architecture-only boundary.
    assert "Architecture agent" in llm.system
    assert "Do NOT produce a roadmap" in llm.system
    # Refinement: never invent tech; leave unspecified choices unresolved; carry Open Questions.
    assert "Never invent a NEW stack" in llm.system
    assert "default PARAMETER" in llm.system  # named-technology default rule
    assert "Decision List" in llm.system
    assert "## Decision List" in llm.prompt


def test_build_prompt_substitutes_project():
    prompt = build_prompt(VISION_DOC, "zeta")
    assert "{{ project }}" not in prompt
    assert "# Architecture — zeta" in prompt


def test_missing_vision_fails_clearly(tmp_path):
    cfg = _config(tmp_path)
    llm = FakeLLM(ARCHITECTURE_OUTPUT)
    with pytest.raises(ArtifactError, match="not found"):
        generate_architecture(cfg, "acme", llm=llm)
    assert llm.calls == 0
    assert not (cfg.projects_dir / "acme" / "01-architecture.md").exists()

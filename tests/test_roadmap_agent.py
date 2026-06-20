"""Tests for the Roadmap agent (WO-005). No network — a fake LLM is injected."""

from pathlib import Path

import pytest

from agents.roadmap import build_prompt, generate_roadmap
from services.artifacts import ArtifactError, read_artifact, write_artifact
from services.config import Config

VISION_DOC = "# Vision — acme\n\n## Problem\nAgents waste time enriching tickets.\n"
ARCHITECTURE_DOC = "# Architecture — acme\n\n## Overview\nA CLI worker enriches tickets.\n"

ROADMAP_OUTPUT = """\
# Roadmap — acme

## Goal
Deliver ticket enrichment.

## Phases
P1 read-only enrichment; P2 write-back.

## Sequencing Principle
Prove enrichment before write-back.

## Deferred
Multi-language support.

## Assumptions
Zendesk API stable.
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


def _write_upstream(cfg, project="acme", vision=VISION_DOC, architecture=ARCHITECTURE_DOC):
    if vision is not None:
        write_artifact(cfg, project, "00-vision.md", vision)
    if architecture is not None:
        write_artifact(cfg, project, "01-architecture.md", architecture)


def test_generates_and_writes_roadmap(tmp_path):
    cfg = _config(tmp_path)
    _write_upstream(cfg)
    llm = FakeLLM(ROADMAP_OUTPUT)

    path = generate_roadmap(cfg, "acme", llm=llm)

    assert path == cfg.projects_dir / "acme" / "02-roadmap.md"
    assert path.is_file()
    assert read_artifact(cfg, "acme", "02-roadmap.md") == ROADMAP_OUTPUT
    assert llm.calls == 1


def test_prompt_includes_both_upstreams_and_template(tmp_path):
    cfg = _config(tmp_path)
    _write_upstream(cfg)
    llm = FakeLLM(ROADMAP_OUTPUT)

    generate_roadmap(cfg, "acme", llm=llm)

    assert "Agents waste time enriching tickets." in llm.prompt  # vision
    assert "A CLI worker enriches tickets." in llm.prompt  # architecture
    assert "## Sequencing Principle" in llm.prompt  # roadmap skeleton
    assert "Roadmap agent" in llm.system
    assert "Do NOT produce work orders" in llm.system
    # Refinement: scope guard + Open Questions propagation.
    assert "Non-Goals as hard limits" in llm.system
    assert "Decision List" in llm.system
    assert "## Decision List" in llm.prompt


def test_build_prompt_substitutes_project():
    prompt = build_prompt(VISION_DOC, ARCHITECTURE_DOC, "zeta")
    assert "{{ project }}" not in prompt
    assert "# Roadmap — zeta" in prompt


def test_missing_vision_fails_clearly(tmp_path):
    cfg = _config(tmp_path)
    _write_upstream(cfg, vision=None)  # architecture only
    llm = FakeLLM(ROADMAP_OUTPUT)
    with pytest.raises(ArtifactError, match="not found"):
        generate_roadmap(cfg, "acme", llm=llm)
    assert llm.calls == 0
    assert not (cfg.projects_dir / "acme" / "02-roadmap.md").exists()


def test_missing_architecture_fails_clearly(tmp_path):
    cfg = _config(tmp_path)
    _write_upstream(cfg, architecture=None)  # vision only
    llm = FakeLLM(ROADMAP_OUTPUT)
    with pytest.raises(ArtifactError, match="not found"):
        generate_roadmap(cfg, "acme", llm=llm)
    assert llm.calls == 0
    assert not (cfg.projects_dir / "acme" / "02-roadmap.md").exists()

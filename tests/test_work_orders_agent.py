"""Tests for the Work Order agent (WO-006). No network — a fake LLM is injected."""

from pathlib import Path

import pytest

from agents.work_orders import build_prompt, generate_work_orders
from services.artifacts import ArtifactError, read_artifact, write_artifact
from services.config import Config

ROADMAP_DOC = """\
# Roadmap — acme

## Goal
Deliver ticket enrichment.

## Phases
P1 read-only enrichment; P2 write-back.
"""

WORK_ORDERS_OUTPUT = """\
# Work Orders — acme

## Format
Each Work Order has Goal, scope, dependencies, done-when, Complexity, Risk.

## Work Orders

### WO-001 — Poller
- **Goal:** Poll Zendesk for new tickets.
- **In scope:** Polling loop.
- **Out of scope:** Write-back.
- **Depends on:** none.
- **Done when:** New tickets are detected.
- **Complexity:** S. **Risk:** Low.

## Deferred
Write-back (P2).

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


def _write_roadmap(cfg, project="acme", doc=ROADMAP_DOC):
    write_artifact(cfg, project, "02-roadmap.md", doc)


def test_generates_and_writes_work_orders(tmp_path):
    cfg = _config(tmp_path)
    _write_roadmap(cfg)
    llm = FakeLLM(WORK_ORDERS_OUTPUT)

    path = generate_work_orders(cfg, "acme", llm=llm)

    assert path == cfg.projects_dir / "acme" / "03-work-orders.md"
    assert path.is_file()
    assert read_artifact(cfg, "acme", "03-work-orders.md") == WORK_ORDERS_OUTPUT
    assert llm.calls == 1


def test_prompt_includes_roadmap_and_template(tmp_path):
    cfg = _config(tmp_path)
    _write_roadmap(cfg)
    llm = FakeLLM(WORK_ORDERS_OUTPUT)

    generate_work_orders(cfg, "acme", llm=llm)

    assert "Deliver ticket enrichment." in llm.prompt  # roadmap
    assert "## Work Orders" in llm.prompt  # skeleton
    assert "Work Order agent" in llm.system
    # System prompt mandates the documented field set.
    assert "Complexity (S/M/L)" in llm.system
    assert "Risk (Low/Medium/High)" in llm.system
    assert "No time estimates" in llm.system
    # Refinement: scope guard + Open Questions propagation.
    assert "Non-Goals as hard limits" in llm.system
    assert "Decision List" in llm.system
    assert "## Decision List" in llm.prompt


def test_build_prompt_substitutes_project():
    prompt = build_prompt(ROADMAP_DOC, "zeta")
    assert "{{ project }}" not in prompt
    assert "# Work Orders — zeta" in prompt


def test_missing_roadmap_fails_clearly(tmp_path):
    cfg = _config(tmp_path)
    llm = FakeLLM(WORK_ORDERS_OUTPUT)
    with pytest.raises(ArtifactError, match="not found"):
        generate_work_orders(cfg, "acme", llm=llm)
    assert llm.calls == 0
    assert not (cfg.projects_dir / "acme" / "03-work-orders.md").exists()

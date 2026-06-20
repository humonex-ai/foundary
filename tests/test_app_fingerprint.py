"""Tests for the V1.6 structural approval fingerprint (app.state)."""

from pathlib import Path

import pytest

from app import state as S
from services.artifacts import write_artifact
from services.config import Config

PLAN = """\
# Work Orders — p

## Work Orders
### WO-001 — Cap
- **Goal:** build the thing
- **In scope:** the thing
- **Out of scope:** other things
- **Depends on:** none
- **Done when:** it works
- **Complexity:** M. **Risk:** Low.

## Decision List

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | a choice | Founder | Product | Open | WO-001 | because |
"""


def _cfg(tmp_path: Path) -> Config:
    return Config(anthropic_api_key="sk-test", projects_dir=tmp_path / "projects")


def _fp(cfg, md, name="p"):
    write_artifact(cfg, name, S.PLAN_ARTIFACT, md)
    return S.plan_fingerprint(cfg, name)


def test_formatting_change_does_not_change_fingerprint(tmp_path):
    cfg = _cfg(tmp_path)
    base = _fp(cfg, PLAN)
    reflowed = PLAN.replace("## Work Orders", "## Work Orders\n").replace(
        "- **Goal:** build the thing", "- **Goal:**   build the thing   "
    ) + "\n\n<!-- a comment -->\n"
    assert _fp(cfg, reflowed) == base


def test_goal_change_changes_fingerprint(tmp_path):
    cfg = _cfg(tmp_path)
    base = _fp(cfg, PLAN)
    assert _fp(cfg, PLAN.replace("build the thing", "build a different thing")) != base


def test_scope_change_changes_fingerprint(tmp_path):
    cfg = _cfg(tmp_path)
    base = _fp(cfg, PLAN)
    assert _fp(cfg, PLAN.replace("other things", "everything else")) != base


def test_done_when_change_changes_fingerprint(tmp_path):
    cfg = _cfg(tmp_path)
    base = _fp(cfg, PLAN)
    assert _fp(cfg, PLAN.replace("it works", "it works and is tested")) != base


def test_decision_status_change_changes_fingerprint(tmp_path):
    cfg = _cfg(tmp_path)
    base = _fp(cfg, PLAN)
    assert _fp(cfg, PLAN.replace("| Open | WO-001 |", "| Decided | WO-001 |")) != base


def test_decision_blocks_change_changes_fingerprint(tmp_path):
    cfg = _cfg(tmp_path)
    base = _fp(cfg, PLAN)
    assert _fp(cfg, PLAN.replace("| Open | WO-001 |", "| Open | — |")) != base


def test_other_artifacts_do_not_affect_plan_fingerprint(tmp_path):
    cfg = _cfg(tmp_path)
    base = _fp(cfg, PLAN)
    # Changing Vision/Architecture/Roadmap cannot affect the plan fingerprint.
    write_artifact(cfg, "p", "00-vision.md", "# Vision — p\n\n## Problem\nA\n")
    write_artifact(cfg, "p", "01-architecture.md", "# Architecture — p\n\n## Overview\nB\n")
    assert S.plan_fingerprint(cfg, "p") == base
    write_artifact(cfg, "p", "00-vision.md", "# Vision — p\n\n## Problem\nCOMPLETELY DIFFERENT\n")
    assert S.plan_fingerprint(cfg, "p") == base


def test_parse_failure_yields_unparseable_and_blocks(tmp_path):
    cfg = _cfg(tmp_path)
    write_artifact(cfg, "p", S.PLAN_ARTIFACT, "garbage with no work orders\n")
    assert S.plan_fingerprint(cfg, "p") == S.UNPARSEABLE
    with pytest.raises(S.StateError):
        S.approve(cfg, "p")  # cannot approve an unparseable plan


def test_unparseable_after_approval_refuses_sync(tmp_path):
    cfg = _cfg(tmp_path)
    write_artifact(cfg, "p", S.PLAN_ARTIFACT, PLAN)
    S.approve(cfg, "p")
    # Plan becomes unparseable after approval -> export refused (not silently passed).
    write_artifact(cfg, "p", S.PLAN_ARTIFACT, "broken now\n")
    ok, reason = S.export_allowed(cfg, "p")
    assert not ok and "parse" in reason

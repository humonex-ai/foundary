"""Tests for app.ingest (Model B system-of-record path). Offline, no LLM."""

from pathlib import Path

import pytest

from app import ingest
from app import projects as app
from app import state as S
from services.config import Config
from services.github import Issue
from services.templates import template_body

# Vision/Architecture/Roadmap skeletons already carry every required section.
VISION = template_body("vision")
ARCH = template_body("architecture")
ROADMAP = template_body("roadmap")

# A parseable, section-complete Work Orders artifact (template body has WO-NNN
# placeholders that don't parse, so author a real one).
WORK_ORDERS = """\
# Work Orders — acme

## Format
Each WO has goal, scope, deps, done-when, complexity, risk.

## Work Orders
### WO-001 — Core capability
- **Goal:** ship it
- **In scope:** the thing
- **Out of scope:** other things
- **Depends on:** none
- **Done when:** it works
- **Complexity:** M. **Risk:** Low.

### WO-002 — Follow-on
- **Goal:** extend it
- **In scope:** more
- **Out of scope:** unrelated
- **Depends on:** WO-001
- **Done when:** extended
- **Complexity:** S. **Risk:** Low.

## Deferred
Nothing yet.

## Assumptions
Stuff is stable.

## Decision List

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | a choice | Architect | Technical | Assumed | WO-001 | default |
"""


def _full():
    return {"vision": VISION, "architecture": ARCH, "roadmap": ROADMAP, "work-orders": WORK_ORDERS}


def _cfg(tmp_path: Path) -> Config:
    return Config(anthropic_api_key="sk-test", projects_dir=tmp_path / "projects")


class FakeGitHub:
    def __init__(s): s.issues=[]; s._n=1; s.writes=[]
    def list_issues(s, r, *, labels=None): return []
    def create_issue(s, r, *, title, body, labels):
        i = Issue(s._n, title, body, "open", list(labels)); s._n += 1; s.issues.append(i)
        s.writes.append(("create", i.number)); return Issue(i.number, i.title, i.body, i.state, list(i.labels))
    def update_issue(s, r, n, *, body): s.writes.append(("update", n))
    def set_labels(s, r, n, labels): s.writes.append(("labels", n))


# --- happy path ------------------------------------------------------------

def test_valid_submission_drafts_and_writes(tmp_path):
    cfg = _cfg(tmp_path)
    res = ingest.submit_project(cfg, "acme", _full())
    assert res["state"] == S.DRAFT
    assert res["validated"] is True
    assert set(res["written"]) == {"00-vision.md", "01-architecture.md",
                                    "02-roadmap.md", "03-work-orders.md"}
    assert S.load_state(cfg, "acme").lifecycle == S.DRAFT


def test_validate_clean_submission_has_no_problems():
    assert ingest.validate_artifacts(_full()) == []


# --- structural failures (nothing written) ---------------------------------

def test_missing_required_artifact(tmp_path):
    cfg = _cfg(tmp_path)
    sub = _full(); del sub["roadmap"]
    with pytest.raises(ingest.IngestError) as exc:
        ingest.submit_project(cfg, "acme", sub)
    assert any("missing required artifact: roadmap" in p for p in exc.value.problems)
    assert not (cfg.projects_dir / "acme" / "00-vision.md").exists()  # atomic


def test_missing_section_in_artifact(tmp_path):
    cfg = _cfg(tmp_path)
    sub = _full(); sub["vision"] = VISION.replace("## Goals", "## Aims")  # rename a required section
    with pytest.raises(ingest.IngestError) as exc:
        ingest.submit_project(cfg, "acme", sub)
    assert any("vision: missing section(s)" in p and "Goals" in p for p in exc.value.problems)


def test_unparseable_work_orders(tmp_path):
    cfg = _cfg(tmp_path)
    sub = _full(); sub["work-orders"] = "# Work Orders\n\n## Format\nx\n## Work Orders\nno WOs\n## Deferred\n\n## Assumptions\n\n## Decision List\n"
    with pytest.raises(ingest.IngestError) as exc:
        ingest.submit_project(cfg, "acme", sub)
    assert any("does not parse" in p for p in exc.value.problems)


# --- coherence failures ----------------------------------------------------

def test_dependency_on_unknown_wo(tmp_path):
    cfg = _cfg(tmp_path)
    sub = _full(); sub["work-orders"] = WORK_ORDERS.replace("**Depends on:** WO-001", "**Depends on:** WO-099")
    with pytest.raises(ingest.IngestError) as exc:
        ingest.submit_project(cfg, "acme", sub)
    assert any("depends on unknown WO-099" in p for p in exc.value.problems)


def test_decision_blocks_unknown_wo(tmp_path):
    cfg = _cfg(tmp_path)
    sub = _full(); sub["work-orders"] = WORK_ORDERS.replace("| Assumed | WO-001 |", "| Assumed | WO-077 |")
    with pytest.raises(ingest.IngestError) as exc:
        ingest.submit_project(cfg, "acme", sub)
    assert any("blocks unknown WO-077" in p for p in exc.value.problems)


# --- lifecycle interaction -------------------------------------------------

def test_resubmit_identical_keeps_approved(tmp_path):
    cfg = _cfg(tmp_path)
    ingest.submit_project(cfg, "acme", _full())
    app.approve_project(cfg, "acme")
    res = ingest.submit_project(cfg, "acme", _full())  # identical plan
    assert res["state"] == S.APPROVED


def test_resubmit_changed_goes_stale(tmp_path):
    cfg = _cfg(tmp_path)
    ingest.submit_project(cfg, "acme", _full())
    app.approve_project(cfg, "acme")
    changed = _full()
    changed["work-orders"] = WORK_ORDERS.replace("ship it", "ship something different")
    res = ingest.submit_project(cfg, "acme", changed)
    assert res["state"] == S.STALE


def test_submitted_project_approves_and_exports(tmp_path):
    cfg = _cfg(tmp_path)
    ingest.submit_project(cfg, "acme", _full())
    app.approve_project(cfg, "acme")
    gh = FakeGitHub()
    res = app.export(cfg, "acme", "o/r", gh=gh, via="mcp")
    assert res["synced"] is True and res["state"] == S.APPROVED  # export keeps Approved
    assert res["summary"].get("create") == 2  # WO-001, WO-002


def test_get_templates_returns_canonical_shapes():
    t = app.get_templates()
    assert set(t) == {"product-input", "vision", "architecture", "roadmap", "work-orders"}
    # Work Orders template must show the Decision List pipe-table + Depends on field.
    wo = t["work-orders"]
    assert "## Decision List" in wo and "| ID | Decision |" in wo
    assert "Depends on" in wo
    # Single-key selection works.
    assert set(app.get_templates("vision")) == {"vision"}


def test_bullet_decision_list_rejected(tmp_path):
    cfg = _cfg(tmp_path)
    sub = _full()
    # Replace the pipe-table Decision List with a bullet list (the real failure).
    sub["work-orders"] = WORK_ORDERS.split("## Decision List")[0] + (
        "## Decision List\n"
        "- D1 — Universe fixed to Nifty 50. Rationale: scope.\n"
        "- D2 — Rule-based score, not ML.\n"
    )
    with pytest.raises(ingest.IngestError) as exc:
        ingest.submit_project(cfg, "acme", sub)
    assert any("Decision List has entries but none parsed" in p for p in exc.value.problems)


def test_empty_decision_list_is_allowed(tmp_path):
    cfg = _cfg(tmp_path)
    sub = _full()
    # A genuinely empty Decision List (header only) must NOT be rejected.
    sub["work-orders"] = WORK_ORDERS.split("## Decision List")[0] + "## Decision List\n\nNone.\n"
    assert ingest.validate_artifacts(sub) == []


def test_optional_product_input_validated_when_present(tmp_path):
    cfg = _cfg(tmp_path)
    sub = _full()
    sub["product-input"] = "# Product Input — acme\n\n## Problem\nx\n"  # incomplete
    with pytest.raises(ingest.IngestError) as exc:
        ingest.submit_project(cfg, "acme", sub)
    assert any("product-input: missing section(s)" in p for p in exc.value.problems)

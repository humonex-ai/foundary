"""Tests for app.projects (MCP V1 services). Offline: FakeLLM + FakeGitHub."""

from pathlib import Path

import pytest

from app import projects as app
from app import state as S
from services.artifacts import write_artifact
from services.config import Config
from services.github import Issue
from services.product_input import ProductInputError
from services.templates import template_body

PI_SECTIONS = [
    "Problem", "Users", "Goals", "Non-Goals", "Constraints",
    "Success Criteria", "Assumptions", "Open Questions",
]

_ROLE = {
    "Vision agent": "vision",
    "Architecture agent": "architecture",
    "Roadmap agent": "roadmap",
    "Work Order agent": "work-orders",
}

REAL_WO = """\
# Work Orders — acme

## Work Orders
### WO-001 — Core capability
- **Goal:** ship the thing
- **In scope:** the thing
- **Out of scope:** other things
- **Depends on:** none
- **Done when:** it works
- **Complexity:** M. **Risk:** Low.

## Decision List

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | a default | Architect | Technical | Assumed | — | default chosen |
"""


class FakeLLM:
    """Returns the stage's template skeleton, or an override for work-orders."""

    def __init__(self, work_orders_text: str | None = None):
        self._wo = work_orders_text
        self.calls: list[str] = []

    def complete(self, prompt: str, *, system=None, max_tokens=8192) -> str:
        stage = next(s for marker, s in _ROLE.items() if marker in (system or ""))
        self.calls.append(stage)
        if stage == "work-orders":
            # Return a PARSEABLE Work Orders artifact (template body has WO-NNN
            # placeholders that don't parse). Other stages don't feed the
            # fingerprint, so their template skeletons are fine.
            return self._wo if self._wo is not None else REAL_WO
        return template_body(stage)


class FakeGitHub:
    def __init__(self):
        self.issues = []
        self._n = 1
        self.writes = []

    def list_issues(self, repo, *, labels=None):
        return []

    def create_issue(self, repo, *, title, body, labels):
        iss = Issue(self._n, title, body, "open", list(labels))
        self._n += 1
        self.issues.append(iss)
        self.writes.append(("create", iss.number))
        return Issue(iss.number, iss.title, iss.body, iss.state, list(iss.labels))

    def update_issue(self, repo, number, *, body):
        self.writes.append(("update", number))

    def set_labels(self, repo, number, labels):
        self.writes.append(("labels", number))


def _cfg(tmp_path: Path) -> Config:
    return Config(anthropic_api_key="sk-test", projects_dir=tmp_path / "projects")


def _pi(project="acme") -> str:
    return f"# Product Input — {project}\n\n" + "\n\n".join(
        f"## {s}\ncontent for {s}." for s in PI_SECTIONS
    )


# --- create / list / show --------------------------------------------------

def test_create_project_drafts_and_writes_artifacts(tmp_path):
    cfg = _cfg(tmp_path)
    res = app.create_project(cfg, "acme", _pi(), llm=FakeLLM())
    assert res["state"] == S.DRAFT
    assert res["artifacts"] == ["00-vision.md", "01-architecture.md",
                                "02-roadmap.md", "03-work-orders.md"]
    assert S.load_state(cfg, "acme").lifecycle == S.DRAFT


def test_create_project_invalid_input_fails_fast(tmp_path):
    cfg = _cfg(tmp_path)
    bad = "# Product Input — acme\n\n## Problem\nonly one\n"
    llm = FakeLLM()
    with pytest.raises(ProductInputError):
        app.create_project(cfg, "acme", bad, llm=llm)
    assert llm.calls == []  # chain never ran
    assert not (cfg.projects_dir / "acme" / "00-vision.md").exists()


def test_list_projects(tmp_path):
    cfg = _cfg(tmp_path)
    app.create_project(cfg, "beta", _pi("beta"), llm=FakeLLM())
    app.create_project(cfg, "alpha", _pi("alpha"), llm=FakeLLM())
    summaries = {s.name: s.lifecycle for s in app.list_projects(cfg)}
    assert summaries == {"alpha": S.DRAFT, "beta": S.DRAFT}


def test_show_project(tmp_path):
    cfg = _cfg(tmp_path)
    app.create_project(cfg, "acme", _pi(), llm=FakeLLM())
    view = app.show_project(cfg, "acme")
    assert view["state"] == S.DRAFT
    assert view["artifacts"]["vision"] is True
    assert view["artifacts"]["product-input"] is True
    content = app.show_project(cfg, "acme", artifact="vision")["content"]
    assert content.startswith("# Vision")
    with pytest.raises(ValueError):
        app.show_project(cfg, "acme", artifact="nope")


# --- regenerate / stale ----------------------------------------------------

def test_regenerate_identical_stays_approved(tmp_path):
    cfg = _cfg(tmp_path)
    app.create_project(cfg, "acme", _pi(), llm=FakeLLM())
    app.approve_project(cfg, "acme")
    res = app.regenerate(cfg, "acme", "work-orders", llm=FakeLLM())  # identical output
    assert res["state"] == S.APPROVED


def test_regenerate_changed_goes_stale(tmp_path):
    cfg = _cfg(tmp_path)
    app.create_project(cfg, "acme", _pi(), llm=FakeLLM())
    app.approve_project(cfg, "acme")
    res = app.regenerate(cfg, "acme", "work-orders",
                         llm=FakeLLM(work_orders_text="# Work Orders — acme\n\n## Work Orders\n### WO-001 — Different\n- **Goal:** changed\n"))
    assert res["state"] == S.STALE


# --- approve / sync guard --------------------------------------------------

def test_approve_records_fingerprint(tmp_path):
    cfg = _cfg(tmp_path)
    write_artifact(cfg, "acme", S.PLAN_ARTIFACT, REAL_WO)
    res = app.approve_project(cfg, "acme")
    assert res["state"] == S.APPROVED
    assert res["plan_fingerprint"]
    assert res["approved_at"]


def test_export_refused_when_draft(tmp_path):
    cfg = _cfg(tmp_path)
    write_artifact(cfg, "acme", S.PLAN_ARTIFACT, REAL_WO)
    gh = FakeGitHub()
    res = app.export(cfg, "acme", "o/r", gh=gh, via="mcp")
    assert res["synced"] is False
    assert "Draft" in res["refused_reason"]
    assert gh.writes == []


def test_export_succeeds_when_approved_records_export(tmp_path):
    cfg = _cfg(tmp_path)
    write_artifact(cfg, "acme", S.PLAN_ARTIFACT, REAL_WO)
    app.approve_project(cfg, "acme")
    gh = FakeGitHub()
    res = app.export(cfg, "acme", "o/r", gh=gh, via="cli")
    assert res["synced"] is True
    assert res["state"] == S.APPROVED  # export does not change lifecycle
    assert res["summary"].get("create") == 1
    # export recorded with via and the approved fingerprint
    st = S.load_state(cfg, "acme")
    assert st.exports[-1]["via"] == "cli"
    assert st.exports[-1]["ref"] == "o/r"
    assert st.exports[-1]["fingerprint"] == st.approved_fingerprint


def test_export_dry_run_records_nothing(tmp_path):
    cfg = _cfg(tmp_path)
    write_artifact(cfg, "acme", S.PLAN_ARTIFACT, REAL_WO)
    app.approve_project(cfg, "acme")
    gh = FakeGitHub()
    res = app.export(cfg, "acme", "o/r", gh=gh, dry_run=True, via="cli")
    assert res["synced"] is False and res["dry_run"] is True
    assert S.load_state(cfg, "acme").exports == []  # no record on dry-run
    assert S.load_state(cfg, "acme").lifecycle == S.APPROVED


def test_export_refused_when_plan_changed_after_approval(tmp_path):
    cfg = _cfg(tmp_path)
    write_artifact(cfg, "acme", S.PLAN_ARTIFACT, REAL_WO)
    app.approve_project(cfg, "acme")
    write_artifact(cfg, "acme", S.PLAN_ARTIFACT, REAL_WO.replace("ship the thing", "ship something else"))
    gh = FakeGitHub()
    res = app.export(cfg, "acme", "o/r", gh=gh, via="mcp")
    assert res["synced"] is False
    assert "differs" in res["refused_reason"]
    assert gh.writes == []
    assert S.load_state(cfg, "acme").exports == []

"""Tests for the `foundry submit` CLI command (local twin of MCP submit_project)."""

from pathlib import Path

import pytest

import cli
from app import ingest
from app import state as S
from services.config import Config
from services.templates import template_body

VISION = template_body("vision")
ARCH = template_body("architecture")
ROADMAP = template_body("roadmap")
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

## Deferred
Nothing yet.

## Assumptions
Stuff is stable.

## Decision List

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | a choice | Architect | Technical | Assumed | WO-001 | default |
"""


def _write_artifacts(dir_: Path) -> None:
    dir_.mkdir(parents=True, exist_ok=True)
    (dir_ / ingest.artifact_filename("vision")).write_text(VISION, encoding="utf-8")
    (dir_ / ingest.artifact_filename("architecture")).write_text(ARCH, encoding="utf-8")
    (dir_ / ingest.artifact_filename("roadmap")).write_text(ROADMAP, encoding="utf-8")
    (dir_ / ingest.artifact_filename("work-orders")).write_text(WORK_ORDERS, encoding="utf-8")


def _patch_cfg(monkeypatch, tmp_path):
    cfg = Config(anthropic_api_key="sk-test", projects_dir=tmp_path / "projects")
    monkeypatch.setattr(cli.Config, "from_env", staticmethod(lambda: cfg))
    return cfg


def _args(project, dir_=""):
    return type("A", (), {"project": project, "dir": str(dir_)})()


def test_submit_from_external_dir_records_draft(monkeypatch, tmp_path, capsys):
    cfg = _patch_cfg(monkeypatch, tmp_path)
    src = tmp_path / "authored"
    _write_artifacts(src)
    rc = cli.cmd_submit(_args("acme", src))
    assert rc == 0
    assert S.load_state(cfg, "acme").lifecycle == S.DRAFT
    # Materialized into the project record dir.
    assert (cfg.projects_dir / "acme" / "00-vision.md").is_file()
    assert "submitted: acme [Draft]" in capsys.readouterr().out


def test_submit_default_dir_is_project_record(monkeypatch, tmp_path):
    cfg = _patch_cfg(monkeypatch, tmp_path)
    _write_artifacts(cfg.projects_dir / "acme")
    rc = cli.cmd_submit(_args("acme"))  # no --dir → <projects_dir>/<project>
    assert rc == 0
    assert S.load_state(cfg, "acme").lifecycle == S.DRAFT


def test_submit_invalid_returns_1_and_writes_nothing(monkeypatch, tmp_path, capsys):
    cfg = _patch_cfg(monkeypatch, tmp_path)
    src = tmp_path / "authored"
    _write_artifacts(src)
    # Break the Decision List into bullets (the real nifty50 failure).
    bad = WORK_ORDERS.split("## Decision List")[0] + "## Decision List\n- D1 — a choice\n"
    (src / ingest.artifact_filename("work-orders")).write_text(bad, encoding="utf-8")
    rc = cli.cmd_submit(_args("acme", src))
    assert rc == 1
    assert "validation failed" in capsys.readouterr().out
    assert not (cfg.projects_dir / "acme" / "00-vision.md").exists()  # atomic


def test_submit_no_files_errors(monkeypatch, tmp_path):
    _patch_cfg(monkeypatch, tmp_path)
    with pytest.raises(SystemExit):
        cli.cmd_submit(_args("acme", tmp_path / "empty"))

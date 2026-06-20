"""Tests for app.state (MCP V1 project lifecycle)."""

from pathlib import Path

import pytest

from app import state as S
from services.artifacts import write_artifact
from services.config import Config

WO_MD = "# Work Orders — p\n\n## Work Orders\n### WO-001 — Cap\n- **Goal:** g\n"
# Same parsed fields, different prose/formatting only (must NOT change fingerprint).
WO_MD_REFORMATTED = "# Work Orders — p\n\n\n## Work Orders\n\n###   WO-001 — Cap  \n- **Goal:**   g\n\n"
# A real structural change (Goal differs) — must change fingerprint.
WO_MD_CHANGED = "# Work Orders — p\n\n## Work Orders\n### WO-001 — Cap\n- **Goal:** different goal\n"


def _cfg(tmp_path: Path) -> Config:
    return Config(anthropic_api_key="sk-test", projects_dir=tmp_path / "projects")


def _write_plan(cfg, name="p", md=WO_MD):
    write_artifact(cfg, name, S.PLAN_ARTIFACT, md)


def test_default_state_is_draft(tmp_path):
    cfg = _cfg(tmp_path)
    assert S.load_state(cfg, "p").lifecycle == S.DRAFT


def test_fingerprint_deterministic_and_changes(tmp_path):
    cfg = _cfg(tmp_path)
    assert S.plan_fingerprint(cfg, "p") == ""  # no artifact yet
    _write_plan(cfg)
    fp1 = S.plan_fingerprint(cfg, "p")
    assert fp1 and S.plan_fingerprint(cfg, "p") == fp1  # stable
    _write_plan(cfg, md=WO_MD_REFORMATTED)
    assert S.plan_fingerprint(cfg, "p") == fp1  # formatting-only: unchanged
    _write_plan(cfg, md=WO_MD_CHANGED)
    assert S.plan_fingerprint(cfg, "p") != fp1  # structural change


def test_save_load_roundtrip(tmp_path):
    cfg = _cfg(tmp_path)
    _write_plan(cfg)
    st = S.approve(cfg, "p", now="2026-06-20T00:00:00Z")
    loaded = S.load_state(cfg, "p")
    assert loaded.lifecycle == S.APPROVED
    assert loaded.approved_fingerprint == st.approved_fingerprint
    assert loaded.approvals[-1]["at"] == "2026-06-20T00:00:00Z"


def test_approve_requires_plan(tmp_path):
    cfg = _cfg(tmp_path)
    with pytest.raises(S.StateError):
        S.approve(cfg, "p")  # no plan artifact


def test_stale_if_changed(tmp_path):
    cfg = _cfg(tmp_path)
    _write_plan(cfg)
    S.approve(cfg, "p")
    # Formatting-only change -> stays Approved.
    _write_plan(cfg, md=WO_MD_REFORMATTED)
    assert S.stale_if_changed(cfg, "p").lifecycle == S.APPROVED
    # Structural change -> Stale.
    _write_plan(cfg, md=WO_MD_CHANGED)
    assert S.stale_if_changed(cfg, "p").lifecycle == S.STALE


def test_sync_allowed_matrix(tmp_path):
    cfg = _cfg(tmp_path)
    _write_plan(cfg)
    # Draft -> not allowed.
    ok, reason = S.sync_allowed(cfg, "p")
    assert not ok and "Draft" in reason
    # Approved + unchanged -> allowed.
    S.approve(cfg, "p")
    ok, _ = S.sync_allowed(cfg, "p")
    assert ok
    # Plan changed after approval -> not allowed (mismatch).
    _write_plan(cfg, md=WO_MD_CHANGED)
    ok, reason = S.sync_allowed(cfg, "p")
    assert not ok and "differs" in reason
    # Stale -> not allowed.
    S.stale_if_changed(cfg, "p")
    ok, reason = S.sync_allowed(cfg, "p")
    assert not ok and "Stale" in reason

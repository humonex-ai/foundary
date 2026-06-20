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


def test_export_allowed_matrix(tmp_path):
    cfg = _cfg(tmp_path)
    _write_plan(cfg)
    # Draft -> not allowed.
    ok, reason = S.export_allowed(cfg, "p")
    assert not ok and "Draft" in reason
    # Approved + unchanged -> allowed.
    S.approve(cfg, "p")
    ok, _ = S.export_allowed(cfg, "p")
    assert ok
    # Plan changed after approval -> not allowed (mismatch).
    _write_plan(cfg, md=WO_MD_CHANGED)
    ok, reason = S.export_allowed(cfg, "p")
    assert not ok and "differs" in reason
    # Stale -> not allowed.
    S.stale_if_changed(cfg, "p")
    ok, reason = S.export_allowed(cfg, "p")
    assert not ok and "Stale" in reason


def test_no_synced_lifecycle_constant():
    assert not hasattr(S, "SYNCED")
    assert not hasattr(S, "mark_synced")


def test_record_export_appends_without_changing_lifecycle(tmp_path):
    cfg = _cfg(tmp_path)
    _write_plan(cfg)
    S.approve(cfg, "p")
    S.record_export(cfg, "p", target="github", ref="o/r", fingerprint="abc", via="mcp",
                    at="2026-06-21T00:00:00Z")
    st = S.load_state(cfg, "p")
    assert st.lifecycle == S.APPROVED          # export does not change lifecycle
    assert st.exports[-1] == {"target": "github", "ref": "o/r", "fingerprint": "abc",
                              "at": "2026-06-21T00:00:00Z", "via": "mcp"}


def test_record_export_duplicates_accepted(tmp_path):
    cfg = _cfg(tmp_path)
    _write_plan(cfg)
    S.approve(cfg, "p")
    for _ in range(2):
        S.record_export(cfg, "p", target="github", ref="o/r", fingerprint="abc", via="cli")
    assert len(S.load_state(cfg, "p").exports) == 2  # no dedupe


def test_record_contains_no_secrets(tmp_path):
    cfg = _cfg(tmp_path)
    _write_plan(cfg)
    S.approve(cfg, "p")
    S.record_export(cfg, "p", target="github", ref="o/r", fingerprint="abc", via="mcp")
    raw = (cfg.projects_dir / "p" / S.STATE_FILENAME).read_text()
    for needle in ("ghp_", "sk-", "token", "api_key", "ANTHROPIC", "GITHUB_TOKEN"):
        assert needle not in raw


def test_record_file_is_record_json(tmp_path):
    cfg = _cfg(tmp_path)
    _write_plan(cfg)
    S.approve(cfg, "p")
    assert (cfg.projects_dir / "p" / "record.json").is_file()
    # no stray temp file left behind by the atomic write
    assert not (cfg.projects_dir / "p" / "record.json.tmp").exists()


def test_migration_from_legacy_synced(tmp_path):
    cfg = _cfg(tmp_path)
    _write_plan(cfg)
    proj = cfg.projects_dir / "p"
    proj.mkdir(parents=True, exist_ok=True)
    # legacy v1 file: no version, lifecycle Synced.
    (proj / S.LEGACY_STATE_FILENAME).write_text(
        '{"name": "p", "lifecycle": "Synced", "approved_fingerprint": "x", "approvals": []}'
    )
    st = S.load_state(cfg, "p")
    assert st.lifecycle == S.APPROVED          # Synced -> Approved
    assert st.version == S.SCHEMA_VERSION
    assert st.exports == []
    assert (proj / "record.json").is_file()                       # one authoritative file
    assert not (proj / S.LEGACY_STATE_FILENAME).is_file()          # legacy retired
    assert (proj / S.LEGACY_BACKUP_FILENAME).is_file()             # rollback kept (inactive)


def test_record_json_takes_precedence_over_legacy(tmp_path):
    cfg = _cfg(tmp_path)
    proj = cfg.projects_dir / "p"
    proj.mkdir(parents=True, exist_ok=True)
    (proj / "record.json").write_text(
        '{"version": 2, "name": "p", "lifecycle": "Stale", "approved_fingerprint": "",'
        ' "approvals": [], "exports": []}'
    )
    (proj / S.LEGACY_STATE_FILENAME).write_text('{"name": "p", "lifecycle": "Approved"}')
    assert S.load_state(cfg, "p").lifecycle == S.STALE  # record.json wins; legacy untouched

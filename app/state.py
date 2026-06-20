"""Per-project record (System of Record).

One JSON file per project at ``projects/<name>/record.json`` — the authoritative,
git-tracked project record: lifecycle, the approved plan fingerprint, an
append-only approval log, and an append-only export log. Everything else is
regenerable artifacts or execution state (GitHub).

Lifecycle: Draft -> Approved -> Stale. (Approved is terminal for projects that
never export; export does not change lifecycle — it appends to the export log.)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from execution.parse import ParseError, parse_decisions, parse_work_orders
from services.artifacts import artifact_exists, project_dir, read_artifact
from services.config import Config

STATE_FILENAME = "record.json"
LEGACY_STATE_FILENAME = ".foundry-state.json"
LEGACY_BACKUP_FILENAME = ".foundry-state.json.bak"
SCHEMA_VERSION = 2

PLAN_ARTIFACT = "03-work-orders.md"  # embeds all Work Orders + the Decision List

DRAFT = "Draft"
APPROVED = "Approved"
STALE = "Stale"

# Sentinel fingerprint for a plan that exists but does not parse. Never equal to a
# real (or empty) fingerprint, so it can never accidentally satisfy the export guard.
UNPARSEABLE = "UNPARSEABLE"


class StateError(RuntimeError):
    """Raised on an invalid lifecycle operation."""


@dataclass
class ProjectState:
    name: str
    lifecycle: str = DRAFT
    approved_fingerprint: str = ""
    approvals: list[dict] = field(default_factory=list)  # append-only
    exports: list[dict] = field(default_factory=list)     # append-only
    version: int = SCHEMA_VERSION

    def to_json(self) -> str:
        return json.dumps(
            {
                "version": self.version,
                "name": self.name,
                "lifecycle": self.lifecycle,
                "approved_fingerprint": self.approved_fingerprint,
                "approvals": self.approvals,
                "exports": self.exports,
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, name: str, text: str) -> "ProjectState":
        data = json.loads(text)
        return cls(
            name=data.get("name", name),
            lifecycle=data.get("lifecycle", DRAFT),
            approved_fingerprint=data.get("approved_fingerprint", ""),
            approvals=data.get("approvals", []),
            exports=data.get("exports", []),
            version=data.get("version", 1),  # missing version => legacy v1
        )


def _state_path(config: Config, name: str):
    return project_dir(config, name) / STATE_FILENAME


def _legacy_path(config: Config, name: str):
    return project_dir(config, name) / LEGACY_STATE_FILENAME


def _migrate(state: ProjectState) -> bool:
    """Upgrade a parsed state to the current schema in place. Returns True if it
    changed (caller should persist). Maps the removed ``Synced`` lifecycle to
    ``Approved`` and stamps the current version."""
    changed = False
    if state.lifecycle == "Synced":
        state.lifecycle = APPROVED
        changed = True
    if state.version != SCHEMA_VERSION:
        state.version = SCHEMA_VERSION
        changed = True
    return changed


def load_state(config: Config, name: str) -> ProjectState:
    """Load a project's record, migrating legacy state on the way.

    Resolution order: ``record.json`` (migrate in place if older schema) →
    legacy ``.foundry-state.json`` (migrate, write ``record.json``, retire the
    legacy file to ``.bak``) → default Draft. After migration there is exactly
    one authoritative file (``record.json``); the retired ``.bak`` is an inactive
    local rollback copy.
    """
    path = _state_path(config, name)
    if path.is_file():
        state = ProjectState.from_json(name, path.read_text(encoding="utf-8"))
        if _migrate(state):
            save_state(config, state)
        return state

    legacy = _legacy_path(config, name)
    if legacy.is_file():
        state = ProjectState.from_json(name, legacy.read_text(encoding="utf-8"))
        _migrate(state)
        save_state(config, state)            # write the new authoritative record.json
        os.replace(legacy, legacy.with_name(LEGACY_BACKUP_FILENAME))  # retire legacy
        return state

    return ProjectState(name=name)


def save_state(config: Config, state: ProjectState) -> None:
    """Atomically persist the record (temp file + replace) so an interrupted
    write cannot corrupt the authoritative record."""
    path = _state_path(config, state.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(state.to_json(), encoding="utf-8")
    os.replace(tmp, path)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _plan_projection(config: Config, name: str) -> str | None:
    """The sync-relevant structured projection of the plan, or None if absent.

    Covers exactly what GitHub sync emits — per Work Order: id, title, goal,
    in/out scope, done-when, depends-on, complexity, risk; per Decision: id,
    status, blocks. Vision/Architecture/Roadmap prose and pure markdown
    formatting are deliberately excluded. Sorted by id; whitespace-normalized.
    Raises ParseError if the artifact is present but malformed.
    """
    if not artifact_exists(config, name, PLAN_ARTIFACT):
        return None
    text = read_artifact(config, name, PLAN_ARTIFACT)
    wos = parse_work_orders(text)
    decisions = parse_decisions(text)

    wo_rows = sorted(
        "|".join([
            w.id, _norm(w.title), _norm(w.goal), _norm(w.in_scope),
            _norm(w.out_of_scope), _norm(w.done_when),
            ",".join(sorted(w.depends_on)), _norm(w.complexity), _norm(w.risk),
        ])
        for w in wos
    )
    dec_rows = sorted(
        "|".join([d.id, _norm(d.status), ",".join(sorted(d.blocks))])
        for d in decisions
    )
    return "WO\n" + "\n".join(wo_rows) + "\nDEC\n" + "\n".join(dec_rows)


def plan_fingerprint(config: Config, name: str) -> str:
    """Fingerprint the sync-relevant structured projection of the plan.

    Returns "" if the plan artifact does not exist yet, or the
    :data:`UNPARSEABLE` sentinel if it exists but cannot be parsed (so the export
    guard refuses rather than passing an unverifiable plan).
    """
    try:
        projection = _plan_projection(config, name)
    except ParseError:
        return UNPARSEABLE
    if projection is None:
        return ""
    return hashlib.sha256(projection.encode("utf-8")).hexdigest()[:16]


# --- transitions -----------------------------------------------------------

def mark_draft(config: Config, name: str) -> ProjectState:
    """Set/reset a freshly generated or ingested project to Draft."""
    state = load_state(config, name)
    state.lifecycle = DRAFT
    save_state(config, state)
    return state


def stale_if_changed(config: Config, name: str) -> ProjectState:
    """If an Approved plan diverged from its approved fingerprint, flip to Stale.
    Identical plans keep their state."""
    state = load_state(config, name)
    if state.lifecycle == APPROVED:
        if plan_fingerprint(config, name) != state.approved_fingerprint:
            state.lifecycle = STALE
            save_state(config, state)
    return state


def approve(config: Config, name: str, *, now: str | None = None) -> ProjectState:
    """Record founder approval of the current plan."""
    if not artifact_exists(config, name, PLAN_ARTIFACT):
        raise StateError(f"Cannot approve {name!r}: no plan artifact yet.")
    fp = plan_fingerprint(config, name)
    if fp == UNPARSEABLE:
        raise StateError(f"Cannot approve {name!r}: plan does not parse — fix it first.")
    state = load_state(config, name)
    stamp = now or datetime.now(timezone.utc).isoformat()
    state.lifecycle = APPROVED
    state.approved_fingerprint = fp
    state.approvals.append({"fingerprint": fp, "at": stamp})
    save_state(config, state)
    return state


def export_allowed(config: Config, name: str) -> tuple[bool, str]:
    """Whether an export is permitted. Returns (allowed, reason_if_not).

    Allowed only when the plan is Approved and the current plan still matches the
    approved fingerprint. Enforced from every export entrypoint via app.export.
    """
    state = load_state(config, name)
    if state.lifecycle == DRAFT:
        return False, "project is Draft — approve it before exporting"
    if state.lifecycle == STALE:
        return False, "project is Stale (plan changed after approval) — re-approve before exporting"
    if state.lifecycle != APPROVED:
        return False, f"project state {state.lifecycle!r} does not permit export"
    current = plan_fingerprint(config, name)
    if current == UNPARSEABLE:
        return False, "plan does not parse — cannot verify against approval; refusing export"
    if current != state.approved_fingerprint:
        return False, "current plan differs from the approved plan — re-approve before exporting"
    return True, ""


def record_export(
    config: Config,
    name: str,
    *,
    target: str,
    ref: str,
    fingerprint: str,
    via: str,
    at: str | None = None,
) -> ProjectState:
    """Append an export event to the record. Does not change lifecycle.

    Append-only: retries may produce duplicate entries (accepted, not deduped).
    Records no secrets — only target, ref, fingerprint, timestamp, via.
    """
    state = load_state(config, name)
    state.exports.append({
        "target": target,
        "ref": ref,
        "fingerprint": fingerprint,
        "at": at or datetime.now(timezone.utc).isoformat(),
        "via": via,
    })
    save_state(config, state)
    return state

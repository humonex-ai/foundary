"""Per-project lifecycle state (MCP V1).

The single piece of mutable, Foundry-owned persistence: one JSON file per project
at ``projects/<name>/.foundry-state.json`` holding the lifecycle state, an
append-only approval log, and the plan fingerprint that was approved. Everything
else is regenerable artifacts (on disk) or execution state (GitHub).

Lifecycle: Draft -> Approved -> Synced, plus Stale (an Approved/Synced plan whose
fingerprint changed and must be re-approved before the next sync).
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from execution.parse import ParseError, parse_decisions, parse_work_orders
from services.artifacts import artifact_exists, project_dir, read_artifact
from services.config import Config

STATE_FILENAME = ".foundry-state.json"
PLAN_ARTIFACT = "03-work-orders.md"  # embeds all Work Orders + the Decision List

DRAFT = "Draft"
APPROVED = "Approved"
SYNCED = "Synced"
STALE = "Stale"

# Sentinel fingerprint for a plan that exists but does not parse. Never equal to a
# real (or empty) fingerprint, so it can never accidentally satisfy the sync guard.
UNPARSEABLE = "UNPARSEABLE"


class StateError(RuntimeError):
    """Raised on an invalid lifecycle operation."""


@dataclass
class ProjectState:
    name: str
    lifecycle: str = DRAFT
    approved_fingerprint: str = ""
    approvals: list[dict] = field(default_factory=list)  # append-only log

    def to_json(self) -> str:
        return json.dumps(
            {
                "name": self.name,
                "lifecycle": self.lifecycle,
                "approved_fingerprint": self.approved_fingerprint,
                "approvals": self.approvals,
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
        )


def _state_path(config: Config, name: str):
    return project_dir(config, name) / STATE_FILENAME


def load_state(config: Config, name: str) -> ProjectState:
    """Load a project's state, defaulting to Draft if no state file exists."""
    path = _state_path(config, name)
    if path.is_file():
        return ProjectState.from_json(name, path.read_text(encoding="utf-8"))
    return ProjectState(name=name)


def save_state(config: Config, state: ProjectState) -> None:
    path = _state_path(config, state.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(state.to_json(), encoding="utf-8")


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
    :data:`UNPARSEABLE` sentinel if it exists but cannot be parsed (so the sync
    guard refuses rather than passing an unverifiable plan). Cosmetic prose /
    formatting changes that do not alter the parsed fields do not change it;
    structural or decision changes do.
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
    """Set/reset a freshly generated project to Draft."""
    state = load_state(config, name)
    state.lifecycle = DRAFT
    save_state(config, state)
    return state


def stale_if_changed(config: Config, name: str) -> ProjectState:
    """After a regenerate: if the plan diverged from the approved fingerprint,
    flip Approved/Synced -> Stale. Identical plans keep their state."""
    state = load_state(config, name)
    if state.lifecycle in (APPROVED, SYNCED):
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


def sync_allowed(config: Config, name: str) -> tuple[bool, str]:
    """Whether GitHub sync is permitted. Returns (allowed, reason_if_not)."""
    state = load_state(config, name)
    if state.lifecycle == DRAFT:
        return False, "project is Draft — approve it before syncing"
    if state.lifecycle == STALE:
        return False, "project is Stale (plan changed after approval) — re-approve before syncing"
    if state.lifecycle not in (APPROVED, SYNCED):
        return False, f"project state {state.lifecycle!r} does not permit sync"
    current = plan_fingerprint(config, name)
    if current == UNPARSEABLE:
        return False, "plan does not parse — cannot verify against approval; refusing sync"
    if current != state.approved_fingerprint:
        return False, "current plan differs from the approved plan — re-approve before syncing"
    return True, ""


def mark_synced(config: Config, name: str) -> ProjectState:
    state = load_state(config, name)
    state.lifecycle = SYNCED
    save_state(config, state)
    return state

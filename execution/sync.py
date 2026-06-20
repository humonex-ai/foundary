"""Idempotent Work Order -> GitHub Issue sync (Execution V1).

Pure logic (fingerprint, body, labels, readiness) plus orchestration over an
injected issue store (``services.github.GitHubClient`` in production, an in-memory
fake in tests). One-way only: Foundry -> GitHub. Closed issues are never touched.

Guards (per the revised Execution V1 plan):
- Identity: a content fingerprint over stable WO content (title + goal + in/out
  scope) is stored in the managed block. A matched OPEN issue whose fingerprint
  diverged is NOT overwritten — it is flagged ``foundry:needs-reconcile`` and
  requires ``--reconcile``.
- Ready: a computed, Foundry-managed cache label; full label recompute every
  sync; ``ready`` removed whenever any ``blocked:*`` applies; a post-reconcile
  invariant forbids ``ready`` + ``blocked:*`` together.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from execution.parse import Decision, WorkOrder
from services.github import Issue

# Markers (kept outside the human-editable managed block).
_ID_RE = re.compile(r"<!--\s*foundry-id:\s*(\S+)\s*-->")
_FP_RE = re.compile(r"<!--\s*foundry-fingerprint:\s*(\S+)\s*-->")
# The full Foundry-controlled region: id marker through the end marker.
_MANAGED_RE = re.compile(
    r"<!--\s*foundry-id:.*?<!--\s*foundry:end\s*-->", re.DOTALL
)

LABEL_FOUNDRY = "foundry"
LABEL_READY = "ready"
LABEL_NEEDS_RECONCILE = "foundry:needs-reconcile"
_FOUNDRY_PREFIXES = ("complexity:", "risk:", "blocked:", "phase:")


class SyncInvariantError(RuntimeError):
    """Raised if the ready/blocked invariant is violated after reconciliation."""


# --- identity & body -------------------------------------------------------

def foundry_id(project: str, wo_id: str) -> str:
    return f"{project}/{wo_id}"


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def fingerprint(wo: WorkOrder) -> str:
    """Stable content fingerprint: title + goal + in scope + out of scope only.

    Metadata (done-when, complexity, risk, depends) is excluded so it can change
    without triggering the divergence guard.
    """
    payload = "".join(_norm(x) for x in (wo.title, wo.goal, wo.in_scope, wo.out_of_scope))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def read_marker(body: str, regex: re.Pattern) -> str | None:
    m = regex.search(body or "")
    return m.group(1) if m else None


def render_managed(
    project: str,
    wo: WorkOrder,
    *,
    blocking_decisions: list[Decision],
    dep_numbers: dict[str, int],
) -> str:
    """Render the Foundry-controlled region (markers + managed block)."""
    deps = (
        ", ".join(
            f"{d} (#{dep_numbers[d]})" if d in dep_numbers else d for d in wo.depends_on
        )
        or "none"
    )
    blocked = (
        "; ".join(f"{d.id} ({d.status} — {_norm(d.decision)[:80]})" for d in blocking_decisions)
        or "none"
    )
    return (
        f"<!-- foundry-id: {foundry_id(project, wo.id)} -->\n"
        f"<!-- foundry-fingerprint: {fingerprint(wo)} -->\n"
        f"<!-- foundry:begin -->\n"
        f"**Goal:** {_norm(wo.goal)}\n\n"
        f"**In scope:** {_norm(wo.in_scope)}\n\n"
        f"**Out of scope:** {_norm(wo.out_of_scope)}\n\n"
        f"**Done when:**\n{wo.done_when.strip() or '—'}\n\n"
        f"**Complexity:** {wo.complexity or '—'} · **Risk:** {wo.risk or '—'}\n\n"
        f"**Depends on:** {deps}\n\n"
        f"**Blocked decisions:** {blocked}\n\n"
        f"**Traceability:** Product Input → Vision (00-vision.md) → Architecture "
        f"(01-architecture.md) → Roadmap (02-roadmap.md) → Work Orders "
        f"(03-work-orders.md), {wo.id}\n"
        f"<!-- foundry:end -->"
    )


def splice_body(existing_body: str, managed: str) -> str:
    """Return a body with the managed region replaced (preserving outside text)."""
    if existing_body and _MANAGED_RE.search(existing_body):
        return _MANAGED_RE.sub(lambda _m: managed, existing_body, count=1)
    if existing_body.strip():
        return f"{existing_body.rstrip()}\n\n{managed}\n"
    return managed + "\n"


# --- readiness & labels ----------------------------------------------------

@dataclass(frozen=True)
class Readiness:
    blocked_decision: bool
    blocked_dependency: bool
    blocking_decisions: tuple[Decision, ...]
    open_deps: tuple[str, ...]

    @property
    def ready(self) -> bool:
        return not (self.blocked_decision or self.blocked_dependency)


def compute_readiness(
    wo: WorkOrder, decisions: list[Decision], dep_state: dict[str, str]
) -> Readiness:
    """dep_state maps WO id -> issue state ('open'/'closed'); missing => not closed."""
    blocking = tuple(
        d for d in decisions if d.status.strip().lower() == "open" and wo.id in d.blocks
    )
    open_deps = tuple(d for d in wo.depends_on if dep_state.get(d) != "closed")
    return Readiness(
        blocked_decision=bool(blocking),
        blocked_dependency=bool(open_deps),
        blocking_decisions=blocking,
        open_deps=open_deps,
    )


def is_foundry_label(label: str) -> bool:
    return (
        label == LABEL_FOUNDRY
        or label == LABEL_READY
        or label == LABEL_NEEDS_RECONCILE
        or label.startswith(_FOUNDRY_PREFIXES)
    )


def foundry_labels(wo: WorkOrder, r: Readiness) -> set[str]:
    """The full Foundry-owned label set for a WO (excludes needs-reconcile)."""
    labels = {LABEL_FOUNDRY}
    if wo.complexity:
        labels.add(f"complexity:{wo.complexity.upper()[:1]}")
    if wo.risk:
        labels.add(f"risk:{wo.risk.lower()}")
    if r.blocked_decision:
        labels.add("blocked:decision")
    if r.blocked_dependency:
        labels.add("blocked:dependency")
    if r.ready:
        labels.add(LABEL_READY)
    return labels


def assert_invariant(labels: set[str]) -> None:
    blocked = any(lbl.startswith("blocked:") for lbl in labels)
    if LABEL_READY in labels and blocked:
        raise SyncInvariantError(f"Issue has both 'ready' and a 'blocked:*' label: {sorted(labels)}")


def merge_labels(existing: list[str], foundry: set[str]) -> list[str]:
    """Human (non-Foundry) labels preserved; Foundry namespace fully recomputed."""
    human = [lbl for lbl in existing if not is_foundry_label(lbl)]
    return sorted(set(human) | foundry)


# --- orchestration ---------------------------------------------------------

@dataclass
class Action:
    wo_id: str | None
    action: str  # create | update | noop | skip-closed | needs-reconcile | orphan
    number: int | None = None
    ready: bool | None = None
    labels: list[str] = field(default_factory=list)
    note: str = ""


@dataclass
class SyncReport:
    actions: list[Action] = field(default_factory=list)

    def by(self, name: str) -> list[Action]:
        return [a for a in self.actions if a.action == name]


def _index_by_id(issues: list[Issue], project: str) -> dict[str, Issue]:
    out: dict[str, Issue] = {}
    prefix = f"{project}/"
    for iss in issues:
        fid = read_marker(iss.body, _ID_RE)
        if fid and fid.startswith(prefix):
            out[fid[len(prefix):]] = iss
    return out


def sync(
    project: str,
    repo: str,
    work_orders: list[WorkOrder],
    decisions: list[Decision],
    gh,
    *,
    dry_run: bool = False,
    reconcile: bool = False,
) -> SyncReport:
    existing = gh.list_issues(repo, labels=LABEL_FOUNDRY)
    by_id = _index_by_id(existing, project)

    dep_state = {wid: iss.state for wid, iss in by_id.items()}
    dep_numbers = {wid: iss.number for wid, iss in by_id.items()}

    report = SyncReport()

    for wo in work_orders:
        r = compute_readiness(wo, decisions, dep_state)
        fset = foundry_labels(wo, r)
        assert_invariant(fset)
        managed = render_managed(
            project, wo, blocking_decisions=list(r.blocking_decisions), dep_numbers=dep_numbers
        )
        title = f"[{wo.id}] {wo.title}"
        existing_issue = by_id.get(wo.id)

        if existing_issue is None:
            if not dry_run:
                created = gh.create_issue(repo, title=title, body=managed + "\n", labels=sorted(fset))
                dep_state[wo.id] = created.state
                dep_numbers[wo.id] = created.number
                num = created.number
            else:
                num = None
            report.actions.append(
                Action(wo.id, "create", num, r.ready, sorted(fset), "new issue")
            )
            continue

        if existing_issue.state == "closed":
            report.actions.append(
                Action(wo.id, "skip-closed", existing_issue.number, None,
                       existing_issue.labels, "closed issue untouched")
            )
            continue

        # Open issue: divergence guard.
        existing_fp = read_marker(existing_issue.body, _FP_RE)
        diverged = existing_fp is not None and existing_fp != fingerprint(wo)

        if diverged and not reconcile:
            new_labels = sorted(set(existing_issue.labels) | {LABEL_NEEDS_RECONCILE})
            if not dry_run and set(new_labels) != set(existing_issue.labels):
                gh.set_labels(repo, existing_issue.number, new_labels)
            report.actions.append(
                Action(wo.id, "needs-reconcile", existing_issue.number, r.ready, new_labels,
                       "fingerprint diverged; body NOT overwritten (use --reconcile)")
            )
            continue

        # Update (fingerprint matches, or --reconcile): refresh body + labels.
        new_body = splice_body(existing_issue.body, managed)
        new_labels = merge_labels(existing_issue.labels, fset)  # drops needs-reconcile
        assert_invariant(set(new_labels))

        body_changed = new_body != existing_issue.body
        labels_changed = set(new_labels) != set(existing_issue.labels)
        if not body_changed and not labels_changed:
            report.actions.append(
                Action(wo.id, "noop", existing_issue.number, r.ready, new_labels, "unchanged")
            )
            continue

        if not dry_run:
            if body_changed:
                gh.update_issue(repo, existing_issue.number, body=new_body)
            if labels_changed:
                gh.set_labels(repo, existing_issue.number, new_labels)
        report.actions.append(
            Action(wo.id, "update", existing_issue.number, r.ready, new_labels,
                   "reconciled" if diverged else "updated")
        )

    # Orphans: foundry issues with no matching WO. Reported, never closed.
    wo_ids = {wo.id for wo in work_orders}
    for wid, iss in sorted(by_id.items()):
        if wid not in wo_ids:
            report.actions.append(
                Action(wid, "orphan", iss.number, None, iss.labels,
                       f"issue #{iss.number} has no Work Order ({iss.state}); not closed")
            )
    return report


# --- authoritative status view --------------------------------------------

@dataclass
class StatusRow:
    wo_id: str
    number: int | None
    state: str
    ready: bool
    blocked_decision: bool
    blocked_dependency: bool
    detail: str


def status(
    project: str, repo: str, work_orders: list[WorkOrder], decisions: list[Decision], gh
) -> list[StatusRow]:
    """Authoritative readiness view — recomputed; ignores the stored ready label."""
    existing = gh.list_issues(repo, labels=LABEL_FOUNDRY)
    by_id = _index_by_id(existing, project)
    dep_state = {wid: iss.state for wid, iss in by_id.items()}

    rows: list[StatusRow] = []
    for wo in work_orders:
        r = compute_readiness(wo, decisions, dep_state)
        iss = by_id.get(wo.id)
        bits = []
        if r.blocked_decision:
            bits.append("decisions: " + ", ".join(d.id for d in r.blocking_decisions))
        if r.blocked_dependency:
            bits.append("deps open: " + ", ".join(r.open_deps))
        rows.append(
            StatusRow(
                wo_id=wo.id,
                number=iss.number if iss else None,
                state=iss.state if iss else "not-synced",
                ready=r.ready,
                blocked_decision=r.blocked_decision,
                blocked_dependency=r.blocked_dependency,
                detail="; ".join(bits) or "ready",
            )
        )
    return rows

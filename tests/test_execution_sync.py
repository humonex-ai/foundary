"""Tests for execution.sync (Execution V1). In-memory fake GitHub — no network."""

import pytest

from execution.parse import Decision, WorkOrder
from execution.sync import (
    LABEL_NEEDS_RECONCILE,
    LABEL_READY,
    SyncInvariantError,
    assert_invariant,
    fingerprint,
    foundry_id,
    status,
    sync,
)
from services.github import Issue

PROJECT = "todo"


class FakeGitHub:
    def __init__(self, issues=None):
        self.issues = list(issues or [])
        self._next = max((i.number for i in self.issues), default=0) + 1
        self.writes = []

    def _copy(self, i):
        return Issue(i.number, i.title, i.body, i.state, list(i.labels))

    def _find(self, number):
        return next(i for i in self.issues if i.number == number)

    def list_issues(self, repo, *, labels=None):
        return [self._copy(i) for i in self.issues if not labels or labels in i.labels]

    def create_issue(self, repo, *, title, body, labels):
        iss = Issue(self._next, title, body, "open", list(labels))
        self._next += 1
        self.issues.append(iss)
        self.writes.append(("create", iss.number))
        return self._copy(iss)

    def update_issue(self, repo, number, *, body):
        self._find(number).body = body
        self.writes.append(("update", number))
        return self._copy(self._find(number))

    def set_labels(self, repo, number, labels):
        self._find(number).labels = list(labels)
        self.writes.append(("labels", number))


def _wo(wid="WO-001", title="Cap", goal="g", in_scope="i", out="o",
        depends=(), complexity="M", risk="Low"):
    return WorkOrder(wid, title, goal, in_scope, out, "done", tuple(depends), complexity, risk)


def _seed(wo, *, fp=None, state="open", labels=None, extra=""):
    fp = fp if fp is not None else fingerprint(wo)
    body = (
        f"<!-- foundry-id: {foundry_id(PROJECT, wo.id)} -->\n"
        f"<!-- foundry-fingerprint: {fp} -->\n"
        f"<!-- foundry:begin -->\nOLD BODY\n<!-- foundry:end -->\n{extra}"
    )
    return Issue(1, f"[{wo.id}] {wo.title}", body, state, list(labels or ["foundry"]))


# --- body generation -------------------------------------------------------

def test_issue_body_generation():
    gh = FakeGitHub()
    wo = _wo()
    sync(PROJECT, "o/r", [wo], [], gh)
    body = gh.issues[0].body
    assert f"foundry-id: {PROJECT}/WO-001" in body
    assert f"foundry-fingerprint: {fingerprint(wo)}" in body
    assert "<!-- foundry:begin -->" in body and "<!-- foundry:end -->" in body
    assert "**Goal:** g" in body
    assert "Traceability:" in body


# --- create vs update / idempotency ---------------------------------------

def test_create_when_missing():
    gh = FakeGitHub()
    rep = sync(PROJECT, "o/r", [_wo()], [], gh)
    assert rep.by("create") and len(gh.issues) == 1


def test_idempotent_second_sync_is_noop():
    gh = FakeGitHub()
    wo = _wo()
    sync(PROJECT, "o/r", [wo], [], gh)
    writes_after_first = len(gh.writes)
    rep = sync(PROJECT, "o/r", [wo], [], gh)
    assert [a.action for a in rep.actions] == ["noop"]
    assert len(gh.writes) == writes_after_first  # no new writes


def test_update_when_open_and_fingerprint_matches():
    wo = _wo()
    gh = FakeGitHub([_seed(wo)])  # correct fp, stale OLD BODY
    rep = sync(PROJECT, "o/r", [wo], [], gh)
    assert rep.by("update")
    assert "OLD BODY" not in gh.issues[0].body
    assert "**Goal:** g" in gh.issues[0].body


# --- dry-run ---------------------------------------------------------------

def test_dry_run_no_writes():
    gh = FakeGitHub()
    rep = sync(PROJECT, "o/r", [_wo()], [], gh, dry_run=True)
    assert rep.by("create")
    assert gh.writes == []
    assert gh.issues == []


# --- divergence guard ------------------------------------------------------

def test_diverged_fingerprint_does_not_overwrite():
    wo = _wo()
    gh = FakeGitHub([_seed(wo, fp="WRONGHASH")])
    rep = sync(PROJECT, "o/r", [wo], [], gh)
    assert rep.by("needs-reconcile")
    assert "OLD BODY" in gh.issues[0].body  # body untouched
    assert LABEL_NEEDS_RECONCILE in gh.issues[0].labels


def test_reconcile_updates_diverged_issue():
    wo = _wo()
    gh = FakeGitHub([_seed(wo, fp="WRONGHASH")])
    rep = sync(PROJECT, "o/r", [wo], [], gh, reconcile=True)
    assert rep.by("update")
    assert "OLD BODY" not in gh.issues[0].body
    assert f"foundry-fingerprint: {fingerprint(wo)}" in gh.issues[0].body
    assert LABEL_NEEDS_RECONCILE not in gh.issues[0].labels


def test_closed_diverged_issue_untouched():
    wo = _wo()
    gh = FakeGitHub([_seed(wo, fp="WRONGHASH", state="closed", labels=["foundry", "risk:low"])])
    before = (gh.issues[0].body, list(gh.issues[0].labels))
    rep = sync(PROJECT, "o/r", [wo], [], gh)
    assert rep.by("skip-closed")
    assert gh.writes == []
    assert (gh.issues[0].body, gh.issues[0].labels) == before


# --- blocked / ready labels ------------------------------------------------

def test_blocked_decision_label_and_no_ready():
    wo = _wo()
    d = Decision("D-001", "modality", "Product", "Product", "Open", ("WO-001",), "fork")
    gh = FakeGitHub()
    sync(PROJECT, "o/r", [wo], [d], gh)
    labels = gh.issues[0].labels
    assert "blocked:decision" in labels
    assert LABEL_READY not in labels


def test_assumed_decision_does_not_block():
    wo = _wo()
    d = Decision("D-002", "path", "Architect", "Technical", "Assumed", ("WO-001",), "default")
    gh = FakeGitHub()
    sync(PROJECT, "o/r", [wo], [d], gh)
    assert "blocked:decision" not in gh.issues[0].labels
    assert LABEL_READY in gh.issues[0].labels


def test_blocked_dependency_label():
    w1, w2 = _wo("WO-001"), _wo("WO-002", depends=["WO-001"])
    gh = FakeGitHub()
    sync(PROJECT, "o/r", [w1, w2], [], gh)
    # WO-002 depends on WO-001 which is open (just created) -> blocked
    iss2 = next(i for i in gh.issues if "[WO-002]" in i.title)
    assert "blocked:dependency" in iss2.labels
    assert LABEL_READY not in iss2.labels


def test_dependency_closed_clears_block():
    w1, w2 = _wo("WO-001"), _wo("WO-002", depends=["WO-001"])
    # seed WO-001 as a CLOSED foundry issue
    seed1 = _seed(w1, state="closed")
    seed1.number = 5
    gh = FakeGitHub([seed1])
    sync(PROJECT, "o/r", [w1, w2], [], gh)
    iss2 = next(i for i in gh.issues if "[WO-002]" in i.title)
    assert "blocked:dependency" not in iss2.labels
    assert LABEL_READY in iss2.labels


def test_ready_removed_when_blocked_on_resync():
    wo = _wo()
    gh = FakeGitHub()
    sync(PROJECT, "o/r", [wo], [], gh)  # ready
    assert LABEL_READY in gh.issues[0].labels
    d = Decision("D-001", "x", "Product", "Product", "Open", ("WO-001",), "now blocks")
    sync(PROJECT, "o/r", [wo], [d], gh)  # now blocked
    assert LABEL_READY not in gh.issues[0].labels
    assert "blocked:decision" in gh.issues[0].labels


# --- invariant -------------------------------------------------------------

def test_invariant_rejects_ready_plus_blocked():
    with pytest.raises(SyncInvariantError):
        assert_invariant({"foundry", LABEL_READY, "blocked:decision"})
    assert_invariant({"foundry", LABEL_READY})  # fine


# --- authoritative status --------------------------------------------------

def test_issue_status_ignores_stored_ready_label():
    wo = _wo()
    # Issue carries a STALE 'ready' label, but an Open decision blocks the WO.
    seed = _seed(wo, labels=["foundry", LABEL_READY])
    gh = FakeGitHub([seed])
    d = Decision("D-001", "x", "Product", "Product", "Open", ("WO-001",), "blocks")
    rows = status(PROJECT, "o/r", [wo], [d], gh)
    assert rows[0].ready is False
    assert rows[0].blocked_decision is True


# --- human labels & orphans ------------------------------------------------

def test_human_labels_preserved():
    wo = _wo(risk="High")
    gh = FakeGitHub([_seed(wo, labels=["foundry", "risk:low", "needs-design"])])
    sync(PROJECT, "o/r", [wo], [], gh)
    labels = gh.issues[0].labels
    assert "needs-design" in labels          # human label kept
    assert "risk:high" in labels             # foundry label recomputed
    assert "risk:low" not in labels          # stale foundry label dropped


def test_orphan_reported_not_closed():
    ghost = _wo("WO-999")
    seed = _seed(ghost)
    seed.number = 7
    gh = FakeGitHub([seed])
    rep = sync(PROJECT, "o/r", [_wo("WO-001")], [], gh)  # WO-999 not in plan
    orphans = rep.by("orphan")
    assert orphans and orphans[0].wo_id == "WO-999"
    assert gh._find(7).state == "open"  # not closed
    assert ("update", 7) not in gh.writes

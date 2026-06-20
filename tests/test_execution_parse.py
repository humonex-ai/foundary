"""Tests for execution.parse (Execution V1)."""

import pytest

from execution.parse import ParseError, parse_decisions, parse_work_orders

WORK_ORDERS_MD = """\
# Work Orders — acme

## Format
_blah_

## Work Orders

### WO-001 — Core task loop with durable local storage
- **Goal:** A user can add, complete, and list tasks that persist.
- **In scope:** storage layer, task operations, tests.
- **Out of scope:** GUI.
- **Depends on:** none.
- **Done when:**
- [ ] add/list/complete work
- [ ] survives restart
- **Complexity:** M. **Risk:** Low.

### WO-002 — Shippable CLI
- **Goal:** Packaged CLI a user installs once.
- **In scope:** packaging, README.
- **Out of scope:** sync.
- **Depends on:** WO-001.
- **Done when:** installs and runs.
- **Complexity:** S. **Risk:** Medium.

## Deferred
_none_

## Decision List

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | Interface modality CLI vs GUI | Product | Product | Open | WO-001 | big fork |
| D-002 | File path default | Architect | Technical | Assumed | — | ~/.todo default |
| D-003 | Retention | Product | Product | Deferred | WO-002 | later |
"""


def test_parse_work_orders():
    wos = parse_work_orders(WORK_ORDERS_MD)
    assert [w.id for w in wos] == ["WO-001", "WO-002"]
    w1 = wos[0]
    assert w1.title == "Core task loop with durable local storage"
    assert "persist" in w1.goal
    assert w1.out_of_scope == "GUI."
    assert w1.depends_on == ()
    assert w1.complexity == "M"
    assert w1.risk == "Low"
    assert "survives restart" in w1.done_when
    assert wos[1].depends_on == ("WO-001",)
    assert wos[1].risk == "Medium"


def test_parse_decisions():
    ds = parse_decisions(WORK_ORDERS_MD)
    assert [d.id for d in ds] == ["D-001", "D-002", "D-003"]
    assert ds[0].status == "Open"
    assert ds[0].blocks == ("WO-001",)
    assert ds[1].status == "Assumed"
    assert ds[1].blocks == ()
    assert ds[2].blocks == ("WO-002",)


def test_parse_work_orders_empty_raises():
    with pytest.raises(ParseError, match="No Work Orders"):
        parse_work_orders("# Work Orders\n\n## Format\nnothing\n")


def test_parse_decisions_absent_section_returns_empty():
    assert parse_decisions("# Work Orders\n\n## Work Orders\n### WO-001 — x\n") == []


def test_parse_decisions_bad_header_raises():
    bad = (
        "## Decision List\n\n"
        "| ID | Wrong | Header |\n|--|--|--|\n| D-001 | a | b |\n"
    )
    with pytest.raises(ParseError, match="header mismatch"):
        parse_decisions(bad)


def test_duplicate_wo_id_raises():
    dup = "## Work Orders\n### WO-001 — a\n- **Goal:** x\n### WO-001 — b\n- **Goal:** y\n"
    with pytest.raises(ParseError, match="Duplicate"):
        parse_work_orders(dup)

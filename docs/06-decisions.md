# Foundry — Decisions

Record of decisions that shaped Foundry, and the reasoning behind them. A
decision is logged here when it constrains future work or explains why an obvious
alternative was not taken.

This stays a **single file**. ADR-per-file folders (`docs/adrs/`) are not adopted
yet — at this volume they add ceremony without benefit. Migration to one file per
decision (preserving IDs, e.g. D-001 → ADR-001) happens only if this file exceeds
~20 decisions or concurrent editing demands it.

Each decision carries: **Status** (Accepted / Superseded), **Date**, and where
relevant **Supersedes** / **Superseded By**.

---

## D-001 — Direction is Foundry's center of gravity; V1 stops before implementation

**Status:** Accepted
**Date:** 2026-06-20
**Decision:** Foundry's permanent center of gravity is direction — Vision,
Architecture, Roadmap, Work Orders. **In V1**, Foundry produces that direction
and stops before implementation: no application code, no PRs, no repository.
Later phases may coordinate engineering execution on top of direction (see
`03-roadmap.md`), but direction always leads.
**Why:** Deciding *what* to build and *in what order* is the highest-leverage,
hardest part. Owning that is more valuable than adding another code generator —
and it must be proven before Foundry crosses into execution.
**Consequence:** Code-writing capability is out of scope for V1 (see D-005). The
"stop before implementation" boundary is a V1 constraint, not a permanent
identity — the long-term vision explicitly allows execution later.

---

## D-002 — Four artifacts are the whole V1 product

**Status:** Accepted
**Date:** 2026-06-20
**Decision:** Vision, Architecture, Roadmap, Work Orders are the V1 product, each
derived from a Product Input; everything else serves them.
**Why:** A clear product boundary prevents scope creep. Each feature is testable
against "does it serve one of the four?"
**Consequence:** Features that do not serve an artifact are rejected
(`01-principles.md` #2).

---

## D-003 — Coherence flows downward; V1 handles drift by re-running

**Status:** Accepted
**Date:** 2026-06-20
**Decision:** Each artifact derives from the one above it. When an upstream
artifact changes, the founder re-runs the downstream stages from a
**user-selected** entry stage. No automatic drift detection in V1.
**Why:** Re-running is the simplest mechanism that keeps artifacts coherent.
Targeted drift detection is more work than V1 needs.
**Consequence:** No incremental/partial drift logic in V1
(`02-architecture.md`, coherence). Coherence is structural (input-based), not
independently verified; a critic/Council pass is deferred.

---

## D-004 — Artifacts are plain markdown files on disk

**Status:** Accepted
**Date:** 2026-06-20
**Decision:** The file is the source of truth. No database, no proprietary
format.
**Why:** Artifacts stay readable without Foundry and the system stays simple.
**Consequence:** Storage, querying, and versioning all reduce to files; richer
storage is deferred until a real need appears (`01-principles.md` #7).

---

## D-005 — Defer power features out of V1

**Status:** Accepted
**Date:** 2026-06-20
**Decision:** No coding agents, no GitHub integration, no LLM Council, no Repo
Intelligence in V1.
**Why:** Each is powerful but premature. None is worth building until the core
artifact loop is proven.
**Consequence:** V1 ships the loop only; deferred features are recorded in
`03-roadmap.md` with a sequencing rule, not scheduled. These are V1 deferrals,
not permanent exclusions (see D-001).

---

## D-006 — Single model per artifact in V1 (no Council yet)

**Status:** Accepted
**Date:** 2026-06-20
**Decision:** In V1, one model produces each artifact.
**Why:** Multi-model deliberation (LLM Council) adds cost and complexity before
the single-model loop has proven its value.
**Consequence:** V1 quality relies on prompts + templates; Council is a later
phase, not ruled out (`03-roadmap.md`).

---

## D-007 — Foundry dogfoods its own format

**Status:** Accepted
**Date:** 2026-06-20
**Decision:** Foundry's own direction is captured in the same artifact form
Foundry produces for any project.
**Why:** Forces the artifact format to be good enough for real use, and gives a
working example.
**Consequence:** Foundry's own direction lives at `projects/foundry/`; the
hand-authored `docs/` describes how Foundry is built (see D-008).

---

## D-008 — Generated artifacts live under `projects/`, separate from `docs/`

**Status:** Accepted
**Date:** 2026-06-20
**Decision:** Each project's generated artifacts live in
`projects/<name>/` (`product-input.md`, `00-vision.md`, `01-architecture.md`,
`02-roadmap.md`, `03-work-orders.md`; numeric prefixes give a natural read
order). Foundry's own meta-documentation stays in
`docs/` and is never a generation target. Foundry dogfoods via
`projects/foundry/`.
**Why:** The earlier design mixed Foundry's own `docs/` with generated output,
risking a run overwriting Foundry's own direction. Per-project directories remove
the collision and scale to multiple projects.
**Consequence:** Artifact IO (WO-001) targets `projects/<name>/`. Resolved before
WO-001 because services implement it. (`02-architecture.md`, Output Location.)

---

## D-009 — Templates are plain markdown with named sections

**Status:** Accepted
**Date:** 2026-06-20
**Decision:** Templates are plain markdown files defining named section headers.
No schema engines, no database, no complex templating system. Jinja2 is used only
for trivial variable substitution (e.g. project name). Every artifact template
includes an `## Assumptions` section.
**Why:** The template's value is consistent, human-readable structure
(`01-principles.md` #7), not machinery. Keeping it dumb avoids coupling agents to
a templating engine. Assumptions sections surface hidden assumptions and aid
drift detection.
**Consequence:** WO-002 produces markdown templates only. Decided before WO-002
because agents couple to the template shape. (`02-architecture.md`, Template
Strategy.)

---

## D-010 — V1 stack is small; orchestration is plain Python

**Status:** Accepted
**Date:** 2026-06-20
**Decision:** V1 stack: **Python 3.12, uv, pydantic, jinja2, Anthropic SDK,
pytest**. Entry point is a **CLI** — no FastAPI / HTTP surface in V1. No agent
framework: **no LangGraph, CrewAI, AutoGen, or Temporal**.
**Why:** The V1 workflow is four sequential calls passing markdown; a `for` loop
over stages is the entire orchestrator. A multi-agent framework would be
premature over-engineering and would fight the clean "agents don't call each
other" boundary. FastAPI buys nothing without a caller. uv keeps maintenance low.
**Consequence:** Orchestration stays plain Python until the workflow has real
branching or dynamic control flow. A framework or API surface is revisited only
when that need is concrete. (`02-architecture.md`, Interface / V1 Stack.)

---

## D-011 — Work Orders are shippable outcomes (CTO compression)

**Status:** Accepted
**Date:** 2026-06-20
**Decision:** The Roadmap and Work Order agents decompose by **founder-visible
outcome**, not by implementation step. Phases are usable increments (prefer 2–4
for V1). A Work Order is one shippable outcome: tests, setup, and hardening fold
into its *Done when*; decisions go to Open Questions; low-leverage units are
merged upward. No Work Order exists solely to select, settle, confirm, document,
or test.
**Why:** The first dogfood runs produced implementation-oriented, over-decomposed
Work Orders (e.g. 14 for a local todo app) — decisions, tests, and layers each
minted as separate units. That is engineer-altitude, not CTO-altitude, and buries
leverage in count.
**Why now / consequence:** Implemented as prompt and template guidance only (the
Roadmap and Work Order agents and their templates); no code, architecture, or
agent-set change. Validated by re-running the three dogfood projects, which fell
from ~53 to ~21 Work Orders with scope, Constraints, and Open Questions preserved.

---

## D-012 — Open Questions and Decisions unified into one Decision List

**Status:** Accepted
**Date:** 2026-06-20
**Decision:** A project has one **Decision List** instead of separate Open
Questions and Decisions. An Open Question is simply a Decision with Status =
Open. Each row carries: ID, Decision, Owner (Founder/Product/Architect/Engineer/
Compliance/Legal), Type (Product/Technical/Compliance/Legal/Operational), Status
(Open/Assumed/Deferred/Decided/Superseded), Blocks (Work Order id or —), and
Rationale. The list is seeded at the Vision stage from the Product Input's Open
Questions, carried forward verbatim (IDs and statuses preserved) and extended at
each stage, and consolidated in the terminal Work Orders artifact with Blocks set.
Agents triage: trivial low-risk defaults become Assumed (with the default stated);
only decisions that materially affect architecture, roadmap, work orders,
compliance, legal, or founder strategy stay Open; real-but-non-blocking become
Deferred; upstream-resolved items become Decided and are never reopened. Agents
never auto-decide compliance, legal, or major product-strategy items.
**Why:** The V1.2/V1.3 reviews found Open Questions had become the bottleneck:
~half were noise (trivial defaults or already-settled constraints), each was
restated 3–5× across artifacts with no owner/status/blocking, and decided items
resurfaced as open. Open Questions and Decisions are the same object at different
lifecycle states; one primitive removes the duplication and the reconciliation
gap. Reuses the ADR-lite format Foundry already runs on itself (this file).
**Consequence:** Implemented as template + prompt guidance only — the four
artifact templates replace their free-prose "## Open Questions" section with a
"## Decision List" table; the Product Input keeps a founder-authored Open
Questions section that seeds the list. No new artifact, agent, or architecture
(`02-architecture.md`, Template Strategy). Solo-founder scope: no review/approval
workflow, no severity matrix, no deadlines beyond the Blocks link.

---

## D-013 — Foundry's strategic direction is System of Record; internal generation is compatibility-only

**Status:** Accepted
**Date:** 2026-06-20
**Decision:** Foundry's long-term identity is a planning + decision + delivery
**system of record**, not a plan generator. The **primary** path is
`submit_project` (`app/ingest.py`): the founder's client LLM (Claude / ChatGPT /
Codex) authors the artifacts, and Foundry validates, records, fingerprints,
approves, gates, and syncs them — with **no internal LLM**. The internal
generator (`create_project` / `regenerate`, backed by `agents/`,
`services/llm.py`, `workflows/chain.py`, and the Anthropic SDK) is **legacy /
compatibility only, pending retirement**.
**Why:** The actual workflow is "brainstorm in a capable client, then call
Foundry." The internal generator produced a weaker, one-shot *second* plan after
the founder already planned interactively, and its nondeterminism drove the
approval churn that V1.6 had to fix. Plan generation is commoditized; **plan
governance** (decisions, approval, traceability, sync) is the durable,
differentiated value. Dogfooding `submit_project` across three client-authored
projects confirmed deterministic validation is sufficient for the governance
spine, with less churn, fewer dependencies, and a clearer mental model.
**Consequence (this phase — Phase 1, labeling only):** `submit_project` is
documented and described as PRIMARY; `create_project`/`regenerate` are labeled
LEGACY in their MCP tool and code docstrings; `ANTHROPIC_API_KEY` is required
**only** for the legacy generator (the primary path needs only `GITHUB_TOKEN` for
sync). No runtime behavior, architecture, or component is removed. Retirement
(remove `agents/`, `services/llm.py`, chain generation, Anthropic dependency) is
**Phase 4**, gated on a coherence validator (Phase 2) and evidence that the
primary path is the sole path in real use. Migration plan recorded separately.

**Phase 1.1 (done):** `ANTHROPIC_API_KEY` is decoupled from startup. `Config`
makes it optional and `Config.from_env` no longer raises when it is absent; the
requirement moved to the point of use — `LLMClient` raises a clear `ConfigError`
only when the legacy generator constructs a real client without it. The server
boots and the primary `submit_project` path runs with no Anthropic key (only
`GITHUB_TOKEN`, and only for `sync_github`). No generator code removed; no MCP
surface change. Existing generator users (key set) are unaffected.

---

## D-014 — Lifecycle is Draft/Approved/Stale; export is metadata; record.json is the authoritative, git-tracked record

**Status:** Accepted
**Date:** 2026-06-21
**Decision:** The project lifecycle is **Draft → Approved → Stale** only.
`Synced` is removed: export is **not** a lifecycle state — it is metadata
appended to the record. The project record lives in
`projects/<name>/record.json` (renamed from the hidden `.foundry-state.json`),
is **git-tracked** (durability/recovery via git history; Foundry performs no git
operations — the founder commits), and carries `version`, `lifecycle`,
`approved_fingerprint`, append-only `approvals[]`, and append-only `exports[]`
(`{target, ref, fingerprint, at, via}`). A **single shared `app.export()`** is the
only path that calls `execution.sync.sync`; both the MCP `sync_github` tool and
the CLI `sync-issues` command delegate to it. `export()` enforces the export
guard (Approved + current fingerprint == approved fingerprint), honors `dry_run`
and `reconcile`, and records an export **only after a successful real sync**
(duplicates from retries accepted, never deduped). Export freshness is computed
per `(target, ref)` against `approved_fingerprint`. The MCP tool stays named
`sync_github`; no `ExportAdapter` abstraction and no `export_github` rename until
a real second target exists.
**Why:** `Synced` baked one export destination into the state machine and was a
dead state for projects that never export — contradicting the System-of-Record
identity (D-013). Export is an event against a destination, not a stage of the
record. A single guarded path removes a previously unguarded CLI export and the
duplicated guard/record logic. Storing the record in git makes the
durability/audit claims real with no new infrastructure (single founder, no DB,
no SaaS).
**Consequence:** `Synced`/`mark_synced`/`sync_allowed` removed
(`sync_allowed`→`export_allowed`); writes are atomic (temp + replace); the record
never contains secrets. Migration is lazy on load: a legacy `.foundry-state.json`
(or a v1 `record.json`) is read, `Synced`→`Approved`, schema stamped to v2, and
the legacy file retired to `.foundry-state.json.bak` (inactive rollback) so there
is exactly one authoritative file. Implements the M1–M6 review modifications.

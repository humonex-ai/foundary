# Foundry — Progress

Current state of Foundry V1 (Phase 1, `03-roadmap.md`). Updated as Work Orders
land.

## Status: Foundry V1 milestone reached — WO-001..WO-008 complete

The full V1 core loop is built, tested, and validated. Services foundation
(WO-001), artifact templates (WO-002), Product Input intake (WO-002b), all four
agents — Vision (WO-003), Architecture (WO-004), Roadmap (WO-005), Work Order
(WO-006) — the chain workflow (WO-007), and the end-to-end loop tests (WO-008)
are done. A template/prompt refinement pass (Constraints propagation,
no-invented-tech, Open Questions propagation) is in place. Validated by three
real dogfood projects (`projects/foundry/`, `projects/ai-investment-firm/`,
`projects/simple-todo-app/`), each producing the full four-artifact chain. No
bugs uncovered during WO-008 validation.

A V1.1 "CTO compression" pass followed (prompt + template guidance only;
`06-decisions.md` D-011): the Roadmap and Work Order agents now decompose by
founder-visible outcome, not implementation step. Re-running the three dogfood
projects from the roadmap stage cut Work Orders from ~53 to ~10 with scope,
Constraints, and Open Questions preserved and no hallucinated technology.

A V1.4 "Decision List" pass (D-012) unified Open Questions and Decisions into one
triaged per-project Decision List table (ID/Decision/Owner/Type/Status/Blocks/
Rationale; Open Question = Decision with Status=Open). Template + prompt guidance
only — no new artifact/agent/architecture. Re-running all three dogfood projects
collapsed free-prose Open Questions into structured rows, dropped Open items by
~45% (trivial defaults became Assumed), kept compliance/legal items Open, and
reconciled constraint-settled items to Decided so they no longer resurface.

A V1.5.1 "decision triage" pass added two generic triage rules to the agent
prompts/templates (reversibility + blast-radius over Type label; a default
parameter of an already-named technology is Assumed, not invented). Re-running
the three dogfood projects, Foundry's mis-triaged Open defaults (validation
strictness, model id) became Assumed; compliance/legal decisions stayed Open
(AIF); no technology hallucinations appeared.

**Execution V1 (Work Orders → GitHub Issues)** is built. First step across the
planning boundary the Vision always reserved (`00-vision.md`). One-way, idempotent
sync of Work Orders to GitHub Issues with: stable `foundry-id` marker, content
fingerprint + divergence guard (`foundry:needs-reconcile`, `--reconcile`), managed
body block, `blocked:decision` / `blocked:dependency` / computed `ready` labels,
closed-issue and human-label preservation, orphan reporting, and an authoritative
`issue-status` view. CLI: `foundry sync-issues` / `foundry issue-status`. No coding
agents, PRs, review, merge, queue, DB, UI, or bidirectional sync.

**MCP V1 (founder operating system)** is built. A thin MCP server (`mcp_server.py`,
`foundry-mcp`) exposes six tools — `list_projects`, `create_project`,
`show_project`, `regenerate`, `approve_project`, `sync_github` — over an
application layer (`app/projects.py`, `app/state.py`). Project lifecycle
Draft → Approved → Synced (+ Stale); approval records a plan fingerprint and
`sync_github` is refused unless the plan is Approved and unchanged. The only new
persistence is a per-project `.foundry-state.json` (no DB). `update_decision` was
deliberately deferred (decision-edit vs regeneration reconciliation = future
work). Single new dependency: the `mcp` SDK.

A V1.6 pass refined the approval fingerprint: `app.state.plan_fingerprint` now
hashes the **parsed, sync-relevant projection** of `03-work-orders.md` (per WO:
id/title/goal/in-out-scope/done-when/depends-on/complexity/risk; per Decision:
id/status/blocks; sorted, whitespace-normalized) instead of the raw text. Cosmetic
LLM rewording / reformatting no longer invalidates approval; structural or
decision changes still do; an unparseable plan yields a sentinel that refuses
sync. Lifecycle, MCP tools, and state are unchanged.

## Direction Documents

| Document | State |
|---|---|
| `00-vision.md` | Done |
| `01-principles.md` | Done |
| `02-architecture.md` | Done |
| `03-roadmap.md` | Done |
| `04-work-orders.md` | Done |
| `06-decisions.md` | Done |
| `07-agent-catalog.md` | Done |
| `08-product-input-template.md` | Done |

## Work Orders (Phase 1)

| ID | Work Order | Complexity | Risk | Status |
|---|---|---|---|---|
| WO-001 | Services foundation | M | Low | Done |
| WO-002 | Artifact templates | S | Medium | Done |
| WO-002b | Product Input intake | S | Low | Done |
| WO-003 | Vision agent (pattern spike) | L | Medium | Done |
| WO-004 | Architecture agent | S | Low | Done |
| WO-005 | Roadmap agent | S | Low | Done |
| WO-006 | Work Order agent | S | Low | Done |
| WO-007 | Chain workflow | M | Medium | Done |
| WO-008 | Loop tests | S | Low | Done |

## Code

`services/` holds the WO-001 layer (`config.py`, `llm.py`, `artifacts.py`) plus
the WO-002 template loader (`templates.py`) and the WO-002b Product Input intake
(`product_input.py`). `templates/` holds the five markdown templates
(product-input, vision, architecture, roadmap, work-orders), each with Purpose /
Required Sections / How To Use guidance and an Assumptions section.
`agents/` holds all four agents — Vision (WO-003), Architecture (WO-004),
Roadmap (WO-005), Work Order (WO-006) — in `vision.py`, `architecture.py`,
`roadmap.py`, `work_orders.py`, all following the same pattern: read upstream →
load template → LLM → write artifact. `workflows/chain.py` (WO-007) sequences
the agents from a caller-chosen entry stage to the end — plain Python, no
framework, no CLI. `tests/test_loop_e2e.py` (WO-008) validates the full loop and
every restart/failure path end to end.

`execution/` holds Execution V1: `parse.py` (Work Order + Decision List parsing)
and `sync.py` (fingerprint, body, labels, readiness, idempotent sync + divergence
guard). `services/github.py` is the thin injectable REST client. `cli.py` exposes
`foundry sync-issues` / `foundry issue-status` (stdlib argparse). `pyproject.toml`
(uv, Python 3.12; anthropic + pydantic, pytest dev); **132 tests pass**, all
GitHub I/O faked (no live calls). Three dogfood projects under `projects/` hold
complete four-artifact chains.

## Next

Foundry V1 planning is complete and Execution V1 (Issue sync) is built. Execution
V2 (single coding agent, human-gated PRs) and V3 (tiered autonomy) are designed
(`06-decisions.md`, V2.0 design) but **not started** — out of current scope. Repo
Intelligence and LLM Council remain deferred per `03-roadmap.md`.

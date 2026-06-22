---
name: foundry-spec
description: >-
  Turn a matured product idea into a Foundry-shaped project spec — the four
  artifacts (vision, architecture, roadmap, work-orders) in Foundry's exact
  format, with a parseable Decision List and Work Order dependencies, ready to
  pass Foundry's validation. Use when
  the user has been brainstorming an idea (here or in another chat) and now wants
  to "make it a Foundry project", "write the project spec", "create the work
  orders / roadmap / vision", or hand the plan to Foundry for tracking and
  GitHub sync. Works with or without the Foundry MCP connected.
---

# Foundry project spec

Foundry is a **system of record** for a project plan. It does not invent the
plan — your chat authors it; Foundry validates it, records it (lifecycle
Draft → Approved → Stale), and exports Work Orders to GitHub Issues. This skill
makes your chat author artifacts in the exact shape Foundry's validation expects,
then routes them into it.

**This skill does not validate, record, or sync — that is code, not a prompt.**
Authoring a spec here produces *candidate* artifacts. They only become a
validated, recorded plan when Foundry actually ingests them: `submit_project`
(MCP) or `foundry submit` (CLI) runs the deterministic checks in
`app/ingest.py`, and lifecycle/approval/GitHub sync run in `app/state.py` and
`execution/`. The skill carries Foundry's *authoring contract*, not its
*enforcement*. Following it well makes ingest likely to pass — it does not make
the plan validated on its own.

The two mistakes that make a spec useless even though it "looks fine":
1. **Decision List as bullets** → parses to zero decisions → gates go blind.
2. **`Depends on:` missing or named `Refs:`** → no dependency graph → no gates.

This skill exists to prevent both.

## Procedure

### 1. Confirm the idea is ready
A Foundry spec needs a settled core: the problem, the primary user, the goals,
the hard constraints (tech/budget/regulatory), and what's explicitly out of
scope. If any are still fuzzy, ask — briefly — and settle them first. Don't
generate a spec on top of an unsettled idea. If the user brainstormed elsewhere,
ask them to paste the conclusion.

### 2. Load the exact format + the authoring rules
- **Templates (the skeleton you fill):**
  - If the Foundry MCP is connected (you can see `submit_project` / a
    `get_templates` tool), call `get_templates` first — it returns the live,
    authoritative skeletons. Author against those.
  - Otherwise (web Claude / ChatGPT, no MCP), use bundled
    [references/templates.md](references/templates.md) — the full template files
    (Purpose / Required Sections / How To Use + the skeleton), verbatim.
- **Authoring rules (how to think while filling them):** always read
  [references/authoring-rules.md](references/authoring-rules.md). It carries
  Foundry's coherence principles and the exact per-artifact rules each Foundry
  agent follows (Vision/Architecture/Roadmap/Work-Orders) — Decision List triage,
  constraint carry-through, vertical slices, "one WO = one outcome", and the
  traps. The skeleton tells you *what sections*; this tells you *what good
  looks like*. The MCP does not serve these rules — they live only in the bundle,
  so read it on every surface.

### 3. Author the four artifacts
Produce `00-vision.md`, `01-architecture.md`, `02-roadmap.md`,
`03-work-orders.md` (optionally `product-input.md`). Non-negotiable:
- Keep **every `##` header verbatim** — Foundry checks section presence.
- Trace downward: every component serves a Vision goal; every Work Order serves
  a Roadmap phase. Carry **Constraints** faithfully into Architecture.
- **Decision List = pipe-table with `D-NNN` ids** (ID | Decision | Owner | Type |
  Status | Blocks | Rationale). Never bullets. Carry rows forward across
  artifacts with stable ids; `03-work-orders.md` holds the canonical list with
  `Blocks` set to the WO each decision gates.
- Each Work Order: outcome-first title, `Goal / In scope / Out of scope /
  Depends on / Done when / Complexity / Risk`. `Depends on:` uses earlier WO ids
  (`WO-001`) — that exact field name — or `none`. One WO = one observable
  outcome; fold tests/setup/hardening into *Done when*; route choices to the
  Decision List, never a "select X" Work Order.

Triage decision Status by reversibility + blast radius (see templates.md). Keep
compliance/legal/strategic items **Open** — never auto-decide them.

### 4. Materialize into Foundry
Pick the branch that matches the surface:

**A. Foundry MCP connected (Claude Code / Desktop):**
1. Call `submit_project(name, artifacts)` with the artifact map
   (`{"vision": "...", "architecture": "...", "roadmap": "...",
   "work-orders": "...", optional "product-input": "..."}`).
2. If it returns validation problems, fix the named artifact and resubmit —
   nothing is written on failure.
3. On success (state `Draft`) tell the user. Approval + sync are explicit next
   steps the **user** triggers: `approve_project` → then `sync_github(name,
   repo)` (needs `GITHUB_TOKEN`, refuses unless Approved + unchanged). Do not
   approve or sync without the user asking.

**B. No MCP (web Claude / ChatGPT):**
1. Emit each artifact as its own fenced code block, labeled with its filename.
2. Tell the user to save each block to its filename (`00-vision.md`,
   `01-architecture.md`, `02-roadmap.md`, `03-work-orders.md`, optional
   `product-input.md`) in one directory, then validate + record it locally with
   `foundry submit <name> --dir <that-dir>` — or paste the blocks into a Claude
   Code session where the Foundry MCP is connected and ask to `submit_project`.
3. The artifacts are authored to Foundry's required shape, so they're intended
   to pass ingest — but validation only actually runs when the user submits them
   to Foundry. Tell the user to fix and resubmit if `submit` reports problems.

## Guardrails
- Don't fabricate the plan. If the idea is thin, surface what's missing rather
  than inventing scope, users, or constraints.
- Don't invent a tech stack the user never named. An unspecified choice is a
  Decision List row (Open if it forks the design, Assumed with a stated default
  if trivial), not a silent pick.
- Don't approve or sync to GitHub on the user's behalf — those are founder
  decisions and `sync_github` is irreversible (creates real issues).
- Re-submitting a changed plan that was already Approved moves it to **Stale** —
  that's expected; the user re-approves.

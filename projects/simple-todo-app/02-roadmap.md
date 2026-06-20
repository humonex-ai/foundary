# Roadmap — simple-todo-app

## Goal
Deliver a working, local-only todo tool in the smallest number of phases that leave the product genuinely usable at each step — starting with the core loop a user depends on every day, then hardening the experience so the tool is something a person would actually keep and recommend.

## Phases

### Phase 1 — The Core Loop Works
**Capability:** A user can add a task, mark it complete, remove it, and see the full list — open tasks above completed ones — from the command line. All changes persist to a plain-text file in the user's home directory and survive process restarts. If the file does not exist, it is created automatically. No configuration is required to get started.

**Done when:**
- A task typed at the command line appears immediately in the list and in the data file.
- Marking a task complete moves it visually below open tasks; the file reflects the change.
- Removing a task eliminates it from both the list and the file.
- Killing and restarting the tool shows exactly the same list as before.
- The data file is human-readable and remains valid if hand-edited between invocations.
- A partial write (simulated crash mid-save) does not corrupt the data file.

---

### Phase 2 — The Experience Is Solid Enough to Keep
**Capability:** The tool handles every realistic edge case gracefully, presents errors in plain language the user understands without documentation, and installs in a single step. A first-time user can pick it up and use it correctly without reading a manual. The secondary (developer) user can read the entire codebase in one sitting and adapt it.

**Done when:**
- Bad input (unknown commands, out-of-range task numbers, empty descriptions, malformed lines in a hand-edited file) produces a clear, actionable message and exits cleanly without data loss.
- The install story is a single command or a single binary download with no runtime dependencies to manage separately.
- The `--file` flag and `SIMPLE_TODO_FILE` environment variable let a user point at a non-default file path without touching source code.
- The codebase is small enough to read and fully understand in under an hour.
- All success criteria from the Vision are demonstrably met end-to-end.

---

## Sequencing Principle
Phase 1 exists because nothing else matters if the fundamental loop — capture, complete, remove, persist — does not work reliably. Every other capability is an improvement on top of a working tool; without Phase 1, there is nothing to improve.

Phase 2 follows because a tool that works but breaks on bad input, or that requires expert knowledge to install, does not satisfy the Vision's promise of zero-friction capture and no-setup-required use. Hardening the experience and nailing the install story are what turn a working prototype into something a real user keeps. These do not need to exist before the core loop is proven, but they must exist before the product is considered done.

This order also respects the open decisions: D-002 (CLI vs. GUI) and D-006 (implementation language) must be resolved before Phase 1 begins, since they determine what is being built. D-001 (completed task retention) must be resolved before the data model in Phase 1 is finalised. Nothing in Phase 2 is required by Phase 1 — Phase 1 is a complete, usable tool; Phase 2 makes it a trustworthy one.

## Deferred

- **GUI front-end:** Pending resolution of D-002. The architecture isolates the renderer so a graphical interface can be added later without redesigning the core. Not scheduled until D-002 is decided in favour of a GUI.
- **Completed-task archiving or auto-deletion:** Pending resolution of D-001. The current model retains completed tasks indefinitely. Archive or purge behaviour will be scoped once the product decision is made.
- **Manual task reordering:** Explicitly post-V1 per D-003. Creation-time order with open tasks first covers the common case.
- **Projects, tags, labels, nested sub-tasks:** Non-goal for V1 per the Vision. Not deferred for reconsideration — excluded.
- **Reminders, notifications, calendar integration:** Non-goal for V1 per the Vision. Excluded.
- **Multi-device sync or any network capability:** Non-goal and a hard constraint. Excluded.

## Assumptions

- D-002 will be resolved as CLI before Phase 1 work begins; the Architecture already proceeds on this assumption and the phases are scoped accordingly.
- D-006 will be resolved before Phase 1 begins; the chosen language produces a single executable or trivially installed artefact consistent with the minimal-footprint constraint.
- D-001 will be resolved before the data model is finalised in Phase 1; the current roadmap assumes completed tasks are retained indefinitely unless D-001 decides otherwise.
- The user's home directory is writable; no fallback path is provided if it is not.
- A personal task list will not grow large enough for full in-memory loading to become a concern.
- One process invocation at a time is the expected usage pattern; no concurrent access from multiple terminals is anticipated.
- Both phases can be completed by a single developer; no team coordination overhead is assumed.

## Decision List

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | Should completed tasks be automatically archived or deleted after some period, or kept indefinitely? | Product | Product | Open | Phase 1 data model, D-005 | Affects data model, storage growth, and whether a user can recover accidentally completed tasks. Auto-deletion is irreversible; wrong choice has lasting user-data impact. Must be resolved before Phase 1 begins. |
| D-002 | Is a terminal (CLI) interface sufficient for V1, or is a minimal graphical (GUI) interface required? | Product | Product | Open | Phase 1 scope, D-006 | Determines implementation language constraints, target audience reach, and total scope. Choosing GUI materially expands cost and complexity. High blast radius — must be decided before Phase 1 begins. |
| D-003 | Should task ordering be by creation time, manual drag/reorder, or sorted by completion state? | Product | Product | Assumed | — | Default: creation time ascending, completed tasks shown after open ones. Reversible and low-cost to change post-V1; manual reorder deferred. |
| D-004 | What is the default path for the data file? | Architect | Technical | Assumed | — | Default: `~/.simple-todo/todos.txt`. Predictable, isolated from working directory, requires no configuration. Override-able via `--file` flag or `SIMPLE_TODO_FILE` environment variable. |
| D-005 | What is the exact line serialisation format for a task record? | Architect | Technical | Assumed | D-001 | Default: `[status]\t{ISO-8601 creation timestamp}\t{description}` where status is space for open and `x` for done. Human-readable and hand-editable. If D-001 introduces an archived state, a third status character can be added without breaking existing lines. |
| D-006 | What implementation language should be used? | Architect | Technical | Open | Phase 1 scope | The Vision names no language. Must satisfy: runs offline, minimal install footprint, produces a single executable or trivial install, readable by a developer user. Candidates depend on D-002 outcome. High blast radius on toolchain and install story — must be decided before Phase 1 begins. |
| D-007 | Should Phase 2 ship as a distinct release or be continuous with Phase 1? | Product | Product | Assumed | — | Default: ship Phase 1 as soon as the core loop is stable so real use can inform Phase 2 priorities. Reversible — phases can be merged into a single release if the team is small and the gap is short. |
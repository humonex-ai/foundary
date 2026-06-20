# Work Orders — simple-todo-app

## Format
_Each Work Order has: an ID, a goal, scope (in/out), dependencies, a done-when check, and metadata — Complexity (S/M/L) and Risk (Low/Medium/High). No time estimates._

## Work Orders
_One block per shippable outcome, in dependency order._

---

### WO-001 — Core task loop persists reliably to disk
- **Goal:** A user can add, complete, remove, and list tasks from the command line, with all state surviving process restarts, stored in a human-readable plain-text file that is never corrupted by a mid-write crash.
- **In scope:**
  - `add`, `done`, `remove`, and `list` commands wired end-to-end.
  - Display order: open tasks above completed tasks, creation-time ascending within each group.
  - Auto-creation of the data file (and any parent directory) on first run; no manual setup required.
  - Atomic write strategy (write-to-temp, rename) so a simulated mid-save crash leaves the previous file intact.
  - Data file format per D-005: `[status]\t{ISO-8601 creation timestamp}\t{description}`, human-readable and valid when hand-edited between invocations.
  - Roundtrip tests: add → list → complete → list → remove → list, with process restart between each step.
  - Crash-safety test: interrupt mid-write, verify file is either fully written or unchanged.
- **Out of scope:** Error handling for bad user input beyond what is needed for the happy path; alternate file paths (`--file`, env var); install packaging; GUI.
- **Depends on:** None. (D-001, D-002, D-005, D-006 must be resolved before work begins — see Decision List.)
- **Done when:**
  - A task typed at the CLI appears immediately in `list` output and in the data file.
  - Marking a task done moves it below open tasks in the display and the file reflects the change.
  - Removing a task eliminates it from both list and file.
  - Killing and restarting the process produces exactly the same list as before.
  - The data file is readable and remains valid after manual edits between invocations.
  - A simulated partial write (process killed mid-save) leaves the data file uncorrupted and the previous state fully intact.
  - All of the above are covered by automated tests that pass cleanly.
- **Complexity:** M. **Risk:** Medium.

---

### WO-002 — Hardened experience, custom file path, and single-step install
- **Goal:** A first-time user can install the tool in one step, point it at any file they choose, and receive a clear, actionable message for every realistic error — without reading documentation or losing any data.
- **In scope:**
  - Input validation and plain-language error messages for: unknown commands, out-of-range task numbers, empty task descriptions, and malformed lines in a hand-edited file (skip/warn on bad lines without aborting).
  - `--file <path>` flag and `SIMPLE_TODO_FILE` environment variable, with precedence: flag > env var > default path (D-004). All Phase 1 behaviour works identically against the alternate path.
  - Single-step install story (single binary download or one install command, zero separately managed runtime dependencies).
  - All error paths exit with a non-zero status code and produce no data loss.
  - End-to-end tests for every error case above; a test that exercises `--file` and the env var; a smoke test of the install artifact on a clean environment.
  - Codebase review gate: the full source can be read and understood in under an hour (no structural change required if already small; this is a scope constraint, not a separate work item).
- **Out of scope:** GUI; multi-device sync; projects/tags/sub-tasks; notifications; completed-task archiving or auto-deletion (pending D-001); concurrent multi-process access.
- **Depends on:** WO-001.
- **Done when:**
  - Every bad-input case (unknown command, out-of-range number, empty description, malformed file line) produces a clear message and exits cleanly without modifying the data file.
  - `--file <path>` and `SIMPLE_TODO_FILE` both redirect all reads and writes correctly; explicit flag beats the env var.
  - A fresh machine running the documented single install command (or downloading the binary) produces a working tool with no additional steps.
  - All success criteria from WO-001 remain passing against the install artifact.
  - All error-path and file-override behaviours are covered by automated tests that pass cleanly.
- **Complexity:** M. **Risk:** Low.

---

## Deferred
- **GUI front-end:** Not broken into Work Orders. Pending resolution of D-002 (currently assumed CLI for V1). Architecture should keep the renderer isolated so this can be added without redesigning the core.
- **Completed-task archiving or auto-deletion:** Not scoped. Pending resolution of D-001. Current model retains completed tasks indefinitely.
- **Manual task reordering:** Explicitly post-V1 per D-003. Not reconsidered here.
- **Projects, tags, labels, nested sub-tasks:** Hard non-goal for V1. Excluded.
- **Reminders, notifications, calendar integration:** Hard non-goal for V1. Excluded.
- **Multi-device sync or any network capability:** Hard non-goal and architectural constraint. Excluded.

---

## Assumptions
- D-001, D-002, and D-006 will be resolved before WO-001 work begins; the phases are scoped on the assumption that D-002 resolves as CLI and D-001 resolves as indefinite retention.
- D-006 will be resolved before WO-001 begins; the chosen language produces a single executable or a trivially installed artifact consistent with the WO-002 install story.
- The user's home directory is writable; no fallback path is provided if it is not.
- A personal task list will not grow large enough for full in-memory loading to become a concern.
- One process invocation at a time is the expected usage pattern; no concurrent-access handling is required.
- Both Work Orders can be completed by a single developer; no team coordination overhead is assumed.
- The codebase will naturally remain small enough to read in under an hour given the tight V1 scope; no explicit size-reduction refactor is planned as a separate work item.

---

## Decision List

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | Should completed tasks be automatically archived or deleted after some period, or kept indefinitely? | Product | Product | Open | WO-001 | Affects data model, storage growth, and recoverability of accidentally completed tasks. Auto-deletion is irreversible; wrong choice has lasting user-data impact. Must be resolved before WO-001 begins. Current roadmap assumes indefinite retention. |
| D-002 | Is a terminal (CLI) interface sufficient for V1, or is a minimal graphical (GUI) interface required? | Product | Product | Open | WO-001 | Determines implementation language constraints, target audience, and total scope. Choosing GUI materially expands cost and complexity. High blast radius — must be decided before WO-001 begins. Roadmap proceeds on CLI assumption. |
| D-003 | Should task ordering be by creation time, manual drag/reorder, or sorted by completion state? | Product | Product | Assumed | — | Default: creation time ascending, completed tasks shown after open ones. Reversible and low-cost to change post-V1; manual reorder deferred explicitly. |
| D-004 | What is the default path for the data file? | Architect | Technical | Assumed | — | Default: `~/.simple-todo/todos.txt`. Predictable, isolated from working directory, requires no configuration. Overridable via `--file` flag or `SIMPLE_TODO_FILE` env var (scoped in WO-002). |
| D-005 | What is the exact line serialisation format for a task record? | Architect | Technical | Assumed | — | Default: `[status]\t{ISO-8601 creation timestamp}\t{description}` where status is space for open and `x` for done. Human-readable and hand-editable. If D-001 introduces an archived state, a third status character can be added without breaking existing lines. |
| D-006 | What implementation language should be used? | Architect | Technical | Open | WO-001 | Must satisfy: runs offline, minimal install footprint, produces a single executable or trivial install, readable by a developer in under an hour. Candidates depend on D-002 outcome. High blast radius on toolchain and install story — must be decided before WO-001 begins. |
| D-007 | Should Phase 2 ship as a distinct release or be continuous with Phase 1? | Product | Product | Assumed | — | Default: ship WO-001 as soon as the core loop is stable so real use can inform WO-002 priorities. Reversible — the two Work Orders can be merged into a single release if the development gap is short. |
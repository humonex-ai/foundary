# Architecture — simple-todo-app

## Overview
The system is a single-process, local-only tool that reads a plain-text file from disk into memory, exposes operations to add, complete, and remove tasks, renders the current list to the user, and writes changes back to disk before exiting. There is no server, no daemon, no network call, and no database engine. The entire runtime is one process with one persistent artifact: the data file. The tool's shape is the smallest possible loop — load, act, save, display — repeated as the user needs it.

## Components

**CLI Entry Point**
Accepts the user's command and arguments, validates them, and dispatches to the appropriate operation. Owns nothing; it is the seam between the operating system and the application logic.

**Task Store (in-memory model)**
The authoritative representation of the task list for the lifetime of one process invocation. Holds an ordered list of task records (id, description, completion flag, creation timestamp). Provides operations: add, complete, remove, and list. Has no knowledge of storage or presentation.

**File Persistence Layer**
Responsible for loading the data file into the Task Store at startup and serialising the Task Store back to the data file after every mutating operation. Owns the file path, the serialisation format, and the atomic-write strategy. Isolated so the format can be changed without touching business logic.

**Renderer**
Formats the task list for terminal output. Separates open from completed tasks visually, shows item indices the user can reference in commands, and keeps the display readable without colour dependencies. Reads from the Task Store; never writes.

## Data & Control Flow

1. **Startup**: The CLI Entry Point receives the command. The File Persistence Layer attempts to read the data file from the default path on disk; if the file does not exist, it initialises an empty Task Store. The loaded or empty state is held in memory for the duration of the invocation.

2. **Dispatch**: The CLI Entry Point routes to the relevant Task Store operation (add / complete / remove / list). All operations are synchronous and in-process.

3. **Mutation**: For add, complete, and remove, the Task Store updates its in-memory list and immediately hands the updated state to the File Persistence Layer, which serialises it and writes it to disk via an atomic write (write to a temporary file alongside the target, then rename into place) to prevent partial writes from corrupting the data file.

4. **Display**: After any operation, the Renderer reads the in-memory Task Store and prints the current list to stdout — open tasks first in creation-time order, completed tasks after.

5. **Exit**: The process exits. There is no background process, lock file, or open connection left behind.

State lives in exactly one place at rest: the data file on disk. In-flight state exists only for the duration of a single process invocation.

## Boundaries

**No GUI.** A graphical interface is excluded pending resolution of D-002. Building a GUI materially expands scope and dependencies; the architecture is designed so that the Task Store and File Persistence Layer are presentation-agnostic, and a GUI front-end could be bolted on later without redesigning those components.

**No daemon or watch mode.** There is no background process keeping the file in sync or watching for changes. Each invocation is fully self-contained. This keeps the footprint minimal and eliminates concurrency concerns.

**No network layer.** No HTTP client, no sync endpoint, no telemetry. Any network capability would contradict the offline-first and privacy constraints.

**No relational database or embedded database engine.** A plain-text file is the only storage mechanism. An embedded database (even a local one) would violate the "inspectable without special tooling" constraint.

**No sub-task, tag, or project model.** The data model is a flat list of tasks with three fields (description, completion flag, creation timestamp). Richer modelling is explicitly a non-goal for V1.

**No undo history or change log.** Recovery of accidentally completed or removed tasks is deferred to D-001; until that decision is made, no archive or history mechanism is included.

**No configuration file required.** The tool must work out of the box with a single install; optional configuration (e.g. overriding the data file path) may be supported via an environment variable or flag, but no config file is created or required.

## Tech Stack

The Vision's Constraints name no specific implementation language, framework, or library — they specify only properties: local, offline, plain inspectable storage, minimal footprint, single-user. The following records what can be resolved from those constraints and what cannot.

| Layer | Technology / Format | Reason | Status |
|---|---|---|---|
| Storage format | Plain text file, one task per line, human-readable and hand-editable | Directly required by the Constraint: "plain, inspectable format the user can read and edit by hand without special tooling" | Decided by Constraint |
| Storage encoding | UTF-8 | Universal, hand-editable in any text editor; no special tooling needed | Assumed, override-able |
| Data file name | `todos.txt` in the user's home directory (`~/.simple-todo/todos.txt`) | Predictable, out of the way, survives working-directory changes; no configuration required to start | Assumed, override-able (see D-004) |
| Serialisation schema | Each line: `[ ]` or `[x]` prefix, then a tab, then an ISO-8601 creation timestamp, then a tab, then the task description (e.g. `[ ]\t2024-01-15T09:00:00\tdraft the report`) | Human-readable, hand-editable, unambiguous, requires no parser library | Assumed, override-able (see D-005) |
| Atomic write strategy | Write to `todos.txt.tmp` then `rename()` into place | Prevents data corruption on crash mid-write; available on all POSIX systems and Windows | Assumed |
| Implementation language | Unresolved — the Vision names no language | See D-006 | Open |

## Assumptions

- The user's home directory is writable. If it is not, the tool will report an error; no fallback path is provided.
- A single data file will not grow large enough to make full in-memory loading a concern for a personal task list (thousands of tasks at most).
- The operating system's file rename operation is atomic enough to protect against partial writes for this use case.
- One process invocation at a time is the expected usage pattern; no concurrent access from multiple terminals is anticipated.
- The primary user can invoke a command-line tool even if D-002 is not yet resolved; the architecture proceeds on that assumption and isolates the renderer so a GUI can replace it later.
- A flat list sorted by creation time (open tasks first, completed after) is sufficient until D-003 is revisited, as D-003 is already Assumed upstream with that default.

## Decision List

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | Should completed tasks be automatically archived or deleted after some period, or kept indefinitely? | Product | Product | Open | D-005 | Affects data model, storage growth, and whether a user can recover accidentally completed tasks. Auto-deletion is irreversible; wrong choice has lasting user-data impact. Must be resolved before storage design is finalised. |
| D-002 | Is a terminal (CLI) interface sufficient for V1, or is a minimal graphical (GUI) interface required? | Product | Product | Open | D-006 | Determines implementation language constraints, target audience reach, and total scope. Choosing GUI materially expands cost and complexity; choosing CLI may exclude the primary (non-developer) user if they are not comfortable in a terminal. High blast radius on scope and user fit — must be decided explicitly. |
| D-003 | Should task ordering be by creation time, manual drag/reorder, or sorted by completion state? | Product | Product | Assumed | — | Reversible and low-cost to change later. Default: order by creation time ascending, with completed tasks shown after open ones. Covers the common case and is simple to implement; manual reorder can be added post-V1 if users need it. |
| D-004 | What is the default path for the data file? | Architect | Technical | Assumed | — | Default: `~/.simple-todo/todos.txt`. Predictable, isolated from the working directory, requires no configuration. Override-able via a `--file` flag or `SIMPLE_TODO_FILE` environment variable. |
| D-005 | What is the exact line serialisation format for a task record? | Architect | Technical | Assumed | D-001 | Default: `[status]\t{ISO-8601 creation timestamp}\t{description}` where status is space for open and `x` for done. Human-readable and hand-editable. If D-001 introduces an archived state, a third status character can be added without breaking existing lines. |
| D-006 | What implementation language should be used? | Architect | Technical | Open | — | The Vision names no language. The choice must satisfy: runs offline, minimal install footprint, produces a single executable or trivial install, readable by the secondary (developer) user. Candidates depend on D-002 outcome. High blast radius on developer toolchain and install story; must be decided explicitly before implementation begins. |
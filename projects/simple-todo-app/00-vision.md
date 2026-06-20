# Vision — simple-todo-app

## Problem
Most task-tracking tools demand more than personal use warrants: accounts, cloud sync, subscriptions, and a surface area too large to learn quickly. Someone who simply wants to capture and check off items on their own machine is forced to choose between these over-engineered products and a raw text file. The text file is private and fast, but it lacks even the minimal conveniences a purpose-built tool provides — marking something done, reordering items, and seeing open versus finished tasks at a glance.

This product exists to close that gap: a focused, local-first todo tool that gives individuals the small conveniences of a real app while matching the simplicity and privacy of a file.

## Users
**Primary:** An individual who wants to capture and complete personal tasks quickly on one device, with no account and no cloud involvement. Speed of capture and clarity of the list matter more than features.

**Secondary:** A developer who wants a small, readable, and hackable todo tool — one they can study in full and adapt to their own workflow without digging through layers of abstraction.

## Goals
- Enable task capture in seconds with the least possible friction.
- Make the current state of open and completed tasks immediately obvious.
- Keep all user data entirely local and private, requiring no account or network.
- Remain small enough that a single person can hold the whole tool in their head and own it completely.

## Non-Goals
- No multi-user support, sharing, or collaboration of any kind.
- No cloud sync, accounts, authentication, or login flows.
- No reminders, notifications, or calendar integration.
- No projects, tags, labels, or nested sub-tasks in V1.

## Constraints
- Single-user, single-device only; all data stored locally on disk.
- Must run fully offline with zero network dependency at any point.
- Minimal footprint: the entire tool must be graspable by one person quickly.
- Storage must be in a plain, inspectable format that the user can read and edit by hand without special tooling.

## Success Criteria
- A user can add, complete, and remove a task within a few seconds each, without consulting documentation.
- The task list persists across restarts and is stored in a human-readable file that remains valid if hand-edited.
- The full codebase is small enough to read and understand in a single sitting.
- The tool runs with no setup beyond a one-time install — no configuration required to get started.

## Assumptions
- One device per user is sufficient; no mechanism for synchronising across devices is expected or desired.
- A flat, unordered list covers the large majority of personal task-tracking needs in V1.
- Users are comfortable with their data residing in a local file on their own machine.

## Decision List

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | Should completed tasks be automatically archived or deleted after some period, or kept indefinitely? | Product | Product | Open | — | Affects data model, storage growth, and whether a user can recover accidentally completed tasks. Auto-deletion is irreversible; wrong choice has lasting user-data impact. Must be resolved before storage design is finalised. |
| D-002 | Is a terminal (CLI) interface sufficient for V1, or is a minimal graphical (GUI) interface required? | Product | Product | Open | — | Determines implementation language constraints, target audience reach, and total scope. Choosing GUI materially expands cost and complexity; choosing CLI may exclude the primary (non-developer) user if they are not comfortable in a terminal. High blast radius on scope and user fit — must be decided explicitly. |
| D-003 | Should task ordering be by creation time, manual drag/reorder, or sorted by completion state? | Product | Product | Assumed | — | Reversible and low-cost to change later. Default: order by creation time ascending, with completed tasks shown after open ones. Covers the common case and is simple to implement; manual reorder can be added post-V1 if users need it. |
# Product Input — simple-todo-app

## Problem
People who want to track personal tasks are pushed toward apps that are far
heavier than they need: accounts, sync, notifications, projects, labels, and a
subscription. For someone who just wants a fast, private list on their own
machine, every option is over-built. They end up using a text file and losing
the small conveniences (done-state, ordering, quick capture) that a purpose-made
tool would give them.

## Users
Primary: an individual who wants to capture and complete personal tasks quickly
on one device, with no account and no cloud.
Secondary: a developer who wants a tiny, hackable todo tool they can read in one
sitting and modify.

## Goals
- Capture a task in seconds with the least possible friction.
- See what is open and what is done at a glance.
- Keep all data local and private — no account, no server.
- Stay small enough that one person can understand the whole thing.

## Non-Goals
- No multi-user support, sharing, or collaboration.
- No cloud sync, accounts, or login.
- No reminders, notifications, or calendar integration.
- No projects, tags, or nested sub-tasks in V1.

## Constraints
- Single-user, single-device; data stored locally on disk.
- Must run offline with no network dependency.
- Minimal footprint: a person should grasp the whole tool quickly.
- Plain, inspectable storage format the user can read and edit by hand.

## Success Criteria
- A user can add, complete, and remove a task in a few seconds each.
- The task list survives restarts and is stored in a human-readable file.
- The whole tool is small enough to read and understand in one sitting.
- It runs with no setup beyond installing it once.

## Assumptions
- One device per user is sufficient; no sync is expected.
- A flat list (no hierarchy) covers the large majority of personal use.
- Users are comfortable with their data living in a local file.

## Open Questions
- Should completed tasks be archived or deleted after some time?
- Is a terminal interface enough, or is a minimal graphical one needed for V1?
- Should task ordering be manual, by creation time, or by completion state?

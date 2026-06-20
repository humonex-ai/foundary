# Product Input — foundry

## Problem
Founders and small teams move fast but lose the thread between intent and
execution. The vision lives in one person's head, the architecture is implied
and never written, the roadmap is a feature list with no rationale, and work is
handed off as vague tickets. The result is drift: what gets built stops matching
why it was supposed to exist. Most teams cannot afford a CTO to hold all four
layers — vision, architecture, roadmap, work — coherent as reality changes, and
the CTOs who exist are too deep in execution to keep the picture current.

## Users
Primary: a technical founder or solo builder who sets product direction but has
no one to turn that direction into structured, coherent technical artifacts.
Secondary: small engineering teams (2–10) who need a written, traceable line
from why to what before they start building.

## Goals
- Turn a founder's intent into four coherent artifacts: Vision, Architecture,
  Roadmap, Work Orders.
- Keep the artifacts traceable — every downstream artifact derives from the one
  above it.
- Make direction explicit and reviewable so it stops living in one head.
- Let a founder go from a structured input to actionable Work Orders in one pass.
- Stay simple enough that a solo founder can run and maintain it.

## Non-Goals
- Not a coding platform: V1 does not write application code, open pull requests,
  or manage a repository.
- Not a project manager: no scheduling, time tracking, or ticket-board sync.
- Not a multi-model deliberation system in V1 (no LLM Council).
- Not aware of any existing codebase in V1 (no Repo Intelligence).

## Constraints
- Python 3.12, managed with uv. Minimal dependencies: pydantic, jinja2,
  Anthropic SDK, pytest.
- CLI only — no web service or API surface in V1.
- Artifacts are plain markdown files on disk; no database.
- Single model backs each agent in V1.
- Built and maintained by one founder; low operational overhead is mandatory.

## Success Criteria
- A founder provides a structured Product Input and receives four coherent
  markdown artifacts, each tracing to the one above it.
- The artifacts are readable on their own without the tool.
- Re-running from any stage downward refreshes the dependent artifacts.
- Foundry can produce its own direction artifacts (dogfooding).

## Assumptions
- A structured Product Input yields markedly better artifacts than free-form
  intent.
- A single LLM call per artifact, guided by a template, produces acceptable V1
  quality.
- Markdown with named sections is enough structure for both humans and agents.
- One founder, one project at a time is the V1 usage shape.

## Open Questions
- Should generated artifacts be version-controlled for history, or is overwrite
  acceptable in V1?
- How strict should structural validation be on the founder's Product Input?
- When does coherence need active verification rather than relying on each agent
  reading its upstream input?

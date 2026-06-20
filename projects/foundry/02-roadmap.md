# Roadmap — foundry

## Goal

Deliver a working, dogfood-ready pipeline that takes a founder's structured intent and produces four coherent, traceable markdown artifacts in a single pass — then prove it on itself — before adding any resilience, power-user, or developer-experience features.

## Phases

### Phase 1 — End-to-End Pipeline, One Real Run

The founder can point Foundry at a Product Input, run a single CLI command, and receive four markdown artifacts — Vision, Architecture, Roadmap, Work Orders — written to disk, each traceable to the one above it. The pipeline runs linearly from start to finish and can be re-entered at any stage using `--from <stage>`.

**Done when:** A founder supplies a valid Product Input, runs `foundry`, and receives four readable, coherent artifacts without manual intervention. Foundry successfully produces its own direction artifacts (dogfood run passes).

---

### Phase 2 — Reliable Inputs, Legible Failures

The founder receives clear, actionable feedback when anything goes wrong: a malformed Product Input is rejected before any API call is made, a missing upstream artifact is caught and named, and an API failure is reported with enough context to act on. No run fails silently or leaves the artifact set in a partially-updated state.

**Done when:** A malformed or incomplete Product Input produces a structured error and halts before the first API call. A missing upstream artifact produces a named, actionable error. An API failure is reported clearly and the existing artifact on disk is not corrupted. All Input Validator and Artifact Store behaviors are covered by automated tests with mocked Anthropic responses.

---

### Phase 3 — Prompt Quality and Iterability

The founder can iterate on prompt templates without touching Python. Template changes are immediately reflected in the next run. Each agent's prompt is demonstrably grounded in its upstream artifact so drift between intent and output is visible in the template, not hidden in code. Foundry's own artifacts serve as the ongoing quality benchmark.

**Done when:** A founder can edit any `.j2` template, re-run from the affected stage, and see updated artifacts with no code change. The prompt-to-artifact trace is legible to a non-engineer reading the template. Repeated dogfood runs produce artifacts that are coherent and improving.

## Sequencing Principle

Phase 1 comes first because nothing else is worth building until the core loop works end-to-end. A pipeline that runs once, on real inputs, against the live API, and produces real artifacts is the only credible foundation for everything downstream.

Phase 2 comes second because operational reliability is a prerequisite for confident iteration. A founder who cannot trust that a failed run is clean — or that a bad input is caught early — cannot iterate safely. Error handling and test coverage must be solid before prompt quality becomes the bottleneck.

Phase 3 comes third because prompt quality is only meaningfully improvable once the pipeline is stable and re-runnable without friction. Template iterability unlocks the primary lever on artifact quality identified in the Vision, but it delivers no value until Phases 1 and 2 give it a trustworthy surface to operate on.

## Deferred

- **Artifact version history / overwrite protection** — Silent overwrite is the V1 default pending resolution of D-001. The Artifact Store is the single change point when a history policy is adopted.
- **Dry-run mode** — Validates inputs and renders prompts without calling the Anthropic API (D-008). Useful for prompt iteration but not blocking V1.
- **Active coherence verification across artifacts** — Semantic cross-artifact checking (D-003). Passive read-upstream is sufficient for V1; active verification is a post-V1 candidate.
- **Multi-project or multi-user workspace isolation** — One project, one founder at a time is the operative V1 shape. Directory isolation for concurrent projects is out of scope.
- **Per-agent model or parameter configuration surface** — Model ID and API parameters are hardcoded defaults with environment-variable overrides (D-004, D-007). A full configuration surface is not warranted in V1.
- **Streaming or partial-artifact display** — The CLI waits for each API call to complete before writing and proceeding. Progress indication is a plain status line.
- **Integration with ticket boards, version control, or any external system** — Work Orders are markdown on disk; no push to Jira, Linear, GitHub Issues, or Git.

## Assumptions

- The Anthropic API is reachable from the machine running Foundry and a valid API key is present in the environment throughout development and dogfooding.
- A single synchronous API call per agent, with no retries beyond SDK defaults, is sufficient reliability for the single-founder V1 usage shape.
- The dogfood run — Foundry producing its own artifacts — is achievable within Phase 1 and serves as the primary integration validation.
- One founder building and maintaining Foundry means phases are sequential and non-overlapping; parallel development tracks are not assumed.
- Prompt template quality sufficient for a credible dogfood run can be achieved within Phase 1 without a dedicated iteration phase; Phase 3 refines rather than establishes baseline quality.
- The Phase 2 test suite, using mocked Anthropic responses, is sufficient to validate pipeline correctness without requiring live API calls in CI.

## Decision List

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | Should generated artifacts be version-controlled (history preserved) or is silent overwrite acceptable in V1? | Founder | Product | Open | — | Overwrite is simpler operationally, but version history changes the value proposition and affects re-run semantics materially. The Artifact Store module isolates this decision to one change point, but the policy must be set before the store is implemented. Blast radius: re-run UX, user trust, and artifact naming scheme. |
| D-002 | How strict should structural validation be on the founder's Product Input? | Product | Product | Assumed | — | Default: validate that all required section headers are present and non-empty; emit a clear error and halt. Deep semantic validation deferred. Reversible and low-cost to tighten later. |
| D-003 | When does coherence between artifacts require active verification rather than relying on each agent reading its upstream input? | Architect | Technical | Deferred | — | Passive read-upstream is the V1 default. Active coherence checking is a post-V1 candidate once the artifact pipeline is proven. |
| D-004 | Which Anthropic model ID backs each agent? | Architect | Technical | Assumed | — | Default: `claude-opus-4-5` for all agents. Anthropic is the named provider; model ID is a reversible parameter. Override-able per-agent via environment variable or a config file without code change. |
| D-005 | Where does Foundry write output artifacts, and is the path configurable? | Architect | Technical | Assumed | — | Default output directory: `./artifacts/` relative to the working directory at invocation. Override-able via a `--output-dir` CLI flag. Reversible and low blast-radius; chosen to keep artifacts co-located with the project without polluting the working directory root. |
| D-006 | How should the CLI represent stage selection — named stages, numeric index, or re-run-from-stage flag? | Architect | Technical | Assumed | — | Default: `--from <stage>` flag accepting one of `vision`, `architecture`, `roadmap`, `work_orders`. Runs the named stage and all downstream stages. Reversible UX decision; simple to change before first release. |
| D-007 | Should per-agent Anthropic API parameters (temperature, max_tokens) be configurable by the founder or hardcoded? | Architect | Technical | Assumed | — | Default: hardcoded sensible defaults per agent (temperature 1.0 per Anthropic guidance; max_tokens 4096). Override-able via environment variables per agent if needed. Reversible; a full config surface is not warranted in V1. |
| D-008 | Should the CLI provide a dry-run mode that validates inputs and renders prompts without calling the Anthropic API? | Architect | Technical | Deferred | — | Useful for development and prompt iteration but not blocking V1 delivery. Deferring avoids premature interface commitment. |
| D-009 | In which phase must D-001 (overwrite vs. version history) be resolved? | Founder | Product | Open | Phase 1 | The Artifact Store must be implemented in Phase 1. Without a resolved overwrite policy, the store cannot be built to its final contract. This decision blocks Phase 1 completion and cannot be deferred further. |
| D-010 | Is a passing dogfood run (Foundry producing its own artifacts) the sole integration acceptance criterion for Phase 1, or are additional validation criteria required? | Founder | Product | Assumed | — | Default: the dogfood run is the primary Phase 1 acceptance gate. It exercises the full pipeline on real inputs against the live API and produces human-reviewable artifacts. Additional criteria (e.g., structured output schema checks) are deferred to Phase 2 as part of the validation and test coverage work. |
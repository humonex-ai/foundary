# Work Orders — foundry

## Format
_Each Work Order has: an ID, a goal, scope (in/out), dependencies, a done-when
check, and metadata — Complexity (S/M/L) and Risk (Low/Medium/High). No time
estimates._

## Work Orders
_One block per shippable outcome, in dependency order. Not one per
implementation step — fold tests, setup, and hardening into Done when, and route
decisions to Open Questions._

---

### WO-001 — Four-Artifact Pipeline Running End to End
- **Goal:** A founder can run a single CLI command against a valid Product Input and receive four coherent markdown artifacts — Vision, Architecture, Roadmap, Work Orders — written to the output directory, each traceable to the one above it.
- **In scope:**
  - CLI entry point accepting a Product Input file path, a `--from <stage>` re-entry flag, and a `--output-dir` flag
  - Four sequential agents (Vision, Architecture, Roadmap, Work Orders), each reading its upstream artifact and calling the Anthropic API once
  - Jinja2 prompt templates for all four agents, grounded in their upstream inputs and sufficient to produce credible artifacts in a single pass
  - Artifact Store: writes each agent's output to `./artifacts/` (or the specified output directory) as a markdown file, silent overwrite per D-001 resolution
  - Plain status-line progress output to the terminal for each stage
  - Dogfood run: Foundry is pointed at its own Product Input and produces all four of its own direction artifacts without manual intervention
- **Out of scope:** Input validation beyond what is needed to run (Phase 2); structured error handling and actionable failure messages (Phase 2); template editing workflow (Phase 3); retries beyond SDK defaults; streaming output; any external integrations; version history or overwrite protection; dry-run mode.
- **Depends on:** None.
- **Done when:**
  - `foundry <product-input>` completes without error and four markdown files are present in the output directory
  - Each artifact references or is visibly grounded in the artifact above it (human review of dogfood output confirms traceability)
  - `--from roadmap` re-runs from the Roadmap stage, reads the existing Architecture artifact, and overwrites only the Roadmap and Work Orders files
  - The dogfood run produces four artifacts that a non-engineer can read and find coherent
  - All four agent prompt templates are `.j2` files on disk, not strings in code
- **Complexity:** L. **Risk:** High.

---

### WO-002 — Validated Inputs and Clean Failure Modes
- **Goal:** A malformed or incomplete Product Input is rejected before any API call is made; a missing upstream artifact is caught and named; an API failure is reported with enough context to act on; no run leaves artifacts in a partially-updated state.
- **In scope:**
  - Input Validator: checks that all required section headers are present and non-empty in the Product Input; emits a structured, human-readable error and halts before the first API call on failure
  - Upstream artifact presence check: before each agent runs, confirms its required input artifact exists on disk; emits a named, actionable error on failure
  - API failure handling: catches Anthropic API errors, reports them with stage name and error context, and leaves the previously written artifact on disk unmodified
  - Atomic write pattern for the Artifact Store: artifact file is only replaced after a successful API response is fully received
  - Automated test suite covering: valid and invalid Product Input permutations, missing upstream artifact scenarios, and simulated API failures — all with mocked Anthropic responses
- **Out of scope:** Deep semantic validation of Product Input content; cross-artifact coherence checking (Deferred, D-003); retry logic beyond SDK defaults; dry-run mode (Deferred, D-008).
- **Depends on:** WO-001.
- **Done when:**
  - A Product Input missing any required section header produces a structured error message and exits before any Anthropic API call is made (verified by test with mocked API that asserts zero calls)
  - Running `--from architecture` when the Vision artifact is absent produces an error naming the missing file and the stage that requires it
  - A simulated API failure at the Roadmap stage leaves the existing Roadmap file on disk unchanged and prints a clear error naming the stage
  - All Input Validator and Artifact Store behaviors described above are covered by automated tests using mocked Anthropic responses, and the test suite passes in CI without a live API key
- **Complexity:** M. **Risk:** Medium.

---

### WO-003 — Editable Prompt Templates with Traceable Grounding
- **Goal:** A founder can edit any `.j2` prompt template, re-run from the affected stage, and see updated artifacts with no code change; the prompt-to-artifact trace is legible to a non-engineer reading the template.
- **In scope:**
  - Template loading: all four agent prompts are loaded from `.j2` files at runtime, with no prompt strings embedded in Python
  - Each template receives its upstream artifact content as a named variable, used explicitly in the template body so the grounding is visible to a reader
  - Repeated dogfood runs after template edits produce artifacts that reflect the changes
  - Documentation (inline comments in templates or a brief README section) sufficient for a non-engineer to understand which variable carries the upstream artifact and how to reference it
- **Out of scope:** A prompt-testing UI; automated prompt quality scoring; dry-run mode (Deferred, D-008); semantic coherence verification across artifacts (Deferred, D-003); any changes to the pipeline execution logic.
- **Depends on:** WO-001, WO-002.
- **Done when:**
  - Editing a `.j2` template (e.g., adding a new instruction line) and running `foundry --from <that stage>` produces an artifact that reflects the edit, with no Python file modified
  - A non-engineer can read any `.j2` template and identify where the upstream artifact content is injected and how it influences the prompt
  - At least two successive dogfood runs (before and after a template edit) produce artifacts that are coherent and show visible improvement or change corresponding to the edit
- **Complexity:** S. **Risk:** Low.

---

## Deferred
- **Artifact version history / overwrite protection** — Silent overwrite is the V1 default pending D-001. The Artifact Store is the single change point. Not broken into a Work Order until D-001 is resolved.
- **Dry-run mode** — Validates inputs and renders prompts without calling the Anthropic API. Useful for prompt iteration; not blocking V1. Deferred per D-008.
- **Active coherence verification across artifacts** — Semantic cross-artifact checking. Passive read-upstream is sufficient for V1; deferred per D-003.
- **Multi-project / multi-user workspace isolation** — One project, one founder at a time is the V1 shape. Out of scope.
- **Per-agent model or parameter configuration surface** — Hardcoded defaults with environment-variable overrides are sufficient for V1 per D-004 and D-007.
- **Streaming or partial-artifact display** — CLI waits for each API call to complete. Progress is a plain status line.
- **Integration with ticket boards, version control, or external systems** — Work Orders are markdown on disk only.

---

## Assumptions
- The Anthropic API is reachable from the development machine and a valid API key is present in the environment throughout development and dogfooding.
- A single synchronous API call per agent, with no retries beyond SDK defaults, is sufficient reliability for the single-founder V1 usage shape.
- The dogfood run — Foundry producing its own artifacts — is achievable within WO-001 and serves as the primary Phase 1 integration validation.
- Prompt template quality sufficient for a credible dogfood run can be achieved within WO-001 without a dedicated prior iteration phase; WO-003 refines rather than establishes baseline quality.
- The automated test suite introduced in WO-002, using mocked Anthropic responses, is sufficient to validate pipeline correctness without requiring live API calls in CI.
- One founder building and maintaining Foundry means Work Orders are sequential and non-overlapping; parallel development tracks are not assumed.
- D-001 (overwrite vs. version history) will be resolved before the Artifact Store in WO-001 is finalized; silent overwrite is the working default and the Artifact Store is the single change point if policy changes.
- Python with the Anthropic SDK and Jinja2 is the implementation language and templating layer (reversible but treated as given for scoping purposes).

---

## Decision List

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | Should generated artifacts be version-controlled (history preserved) or is silent overwrite acceptable in V1? | Founder | Product | Open | WO-001 | Overwrite is simpler operationally, but version history changes the value proposition and affects re-run semantics materially. The Artifact Store isolates this to one change point, but the policy must be set before the store is built to its final contract. Blast radius: re-run UX, user trust, artifact naming scheme. |
| D-002 | How strict should structural validation be on the founder's Product Input? | Product | Product | Assumed | — | Default: validate that all required section headers are present and non-empty; emit a clear error and halt. Deep semantic validation deferred. Reversible and low-cost to tighten later. |
| D-003 | When does coherence between artifacts require active verification rather than relying on each agent reading its upstream input? | Architect | Technical | Deferred | — | Passive read-upstream is the V1 default. Active coherence checking is a post-V1 candidate once the artifact pipeline is proven. |
| D-004 | Which Anthropic model ID backs each agent? | Architect | Technical | Assumed | — | Default: `claude-opus-4-5` for all agents. Anthropic is the named provider; model ID is a reversible parameter, override-able per-agent via environment variable without code change. |
| D-005 | Where does Foundry write output artifacts, and is the path configurable? | Architect | Technical | Assumed | — | Default output directory: `./artifacts/` relative to the working directory at invocation. Override-able via `--output-dir` CLI flag. Reversible and low blast-radius. |
| D-006 | How should the CLI represent stage selection — named stages, numeric index, or re-run-from-stage flag? | Architect | Technical | Assumed | — | Default: `--from <stage>` flag accepting one of `vision`, `architecture`, `roadmap`, `work_orders`. Runs the named stage and all downstream stages. Reversible UX decision; simple to change before first release. |
| D-007 | Should per-agent Anthropic API parameters (temperature, max_tokens) be configurable by the founder or hardcoded? | Architect | Technical | Assumed | — | Default: hardcoded sensible defaults per agent (temperature 1.0 per Anthropic guidance; max_tokens 4096). Override-able via environment variables per agent. A full config surface is not warranted in V1. |
| D-008 | Should the CLI provide a dry-run mode that validates inputs and renders prompts without calling the Anthropic API? | Architect | Technical | Deferred | — | Useful for development and prompt iteration but not blocking V1 delivery. Deferring avoids premature interface commitment. |
| D-009 | In which phase must D-001 (overwrite vs. version history) be resolved? | Founder | Product | Open | WO-001 | The Artifact Store must be implemented in WO-001. Without a resolved overwrite policy, the store cannot be built to its final contract. This decision blocks WO-001 completion and cannot be deferred further. |
| D-010 | Is a passing dogfood run (Foundry producing its own artifacts) the sole integration acceptance criterion for Phase 1, or are additional validation criteria required? | Founder | Product | Assumed | — | Default: the dogfood run is the primary WO-001 acceptance gate. It exercises the full pipeline on real inputs against the live API and produces human-reviewable artifacts. Additional criteria (e.g., structured output schema checks) are deferred to WO-002 as part of validation and test coverage work. |
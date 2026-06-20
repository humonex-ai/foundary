# Architecture — foundry

## Overview

Foundry is a single-process Python CLI that drives four sequential AI agents — Vision, Architecture, Roadmap, Work Orders — each of which reads a structured markdown input, calls the Anthropic API once, and writes a structured markdown artifact to disk. The pipeline is linear: each agent's output becomes the next agent's input, making the dependency chain explicit and re-runnable from any stage. State lives entirely in markdown files on the local filesystem; there is no daemon, no server, and no background process.

## Components

**CLI Entry Point (`foundry/cli.py`)**
Parses the command issued by the user, resolves the starting stage and any named options, validates that required upstream artifacts exist before any agent runs, and dispatches to the Pipeline Orchestrator. It is the only executable surface.

**Pipeline Orchestrator (`foundry/pipeline.py`)**
Owns the ordered sequence of stages: `vision → architecture → roadmap → work_orders`. Given a starting stage, it runs every stage from that point forward in order, passing the output path of each completed stage as the input to the next. It enforces the linearity of the chain and is the single place that knows the stage ordering.

**Input Validator (`foundry/validator.py`)**
Accepts a file path and a list of required section headers. Parses the markdown file and asserts that every required section header is present and non-empty. Halts with a structured error message if validation fails. Used on the Product Input before Vision runs, and may be applied to any upstream artifact before a downstream agent consumes it.

**Agent Base (`foundry/agents/base.py`)**
Abstract class defining the contract every agent fulfills: receive an input artifact path, load and validate it, render a prompt using its Jinja2 template, call the Anthropic API once, and write the resulting markdown to the designated output path. Error handling (API failures, malformed responses) lives here so each concrete agent inherits it.

**Vision Agent (`foundry/agents/vision.py`)**
Concrete agent. Input: Product Input (founder-supplied structured markdown). Output: `vision.md`. Responsible only for producing a Vision artifact conforming to the Vision template.

**Architecture Agent (`foundry/agents/architecture.py`)**
Concrete agent. Input: `vision.md`. Output: `architecture.md`. Responsible only for producing an Architecture artifact that derives from the Vision.

**Roadmap Agent (`foundry/agents/roadmap.py`)**
Concrete agent. Input: `architecture.md` (and `vision.md` passed as context). Output: `roadmap.md`. Responsible only for producing a Roadmap artifact traceable to Vision and Architecture.

**Work Orders Agent (`foundry/agents/work_orders.py`)**
Concrete agent. Input: `roadmap.md` (and `vision.md`, `architecture.md` passed as context). Output: `work_orders.md`. Responsible only for decomposing the Roadmap into actionable Work Orders.

**Prompt Templates (`foundry/templates/*.j2`)**
One Jinja2 template per agent. Each template structures the full prompt: it embeds the upstream artifact content, states the agent's role and rules, and specifies the required output format by name. Templates are the primary lever on output quality and are versioned as code.

**Artifact Store (`foundry/store.py`)**
Thin filesystem abstraction. Provides `read(path) → str` and `write(path, content: str)` operations. All file I/O is routed through this module so overwrite behavior, path resolution, and any future versioning policy change in exactly one place.

## Data & Control Flow

```
Founder
  │
  ▼
[Product Input — founder-authored markdown on disk]
  │
  ▼
CLI Entry Point
  │  validates flags, resolves starting stage
  ▼
Pipeline Orchestrator
  │
  ├─ stage: vision
  │    Input Validator ── checks Product Input headers
  │    Vision Agent ── renders prompt (Jinja2) ── Anthropic API call ── writes vision.md
  │
  ├─ stage: architecture
  │    Input Validator ── checks vision.md headers
  │    Architecture Agent ── renders prompt (vision.md) ── Anthropic API call ── writes architecture.md
  │
  ├─ stage: roadmap
  │    Input Validator ── checks architecture.md headers
  │    Roadmap Agent ── renders prompt (vision.md + architecture.md) ── Anthropic API call ── writes roadmap.md
  │
  └─ stage: work_orders
       Input Validator ── checks roadmap.md headers
       Work Orders Agent ── renders prompt (vision.md + architecture.md + roadmap.md) ── Anthropic API call ── writes work_orders.md
```

State between stages is entirely the markdown file written to disk after each agent completes. The Orchestrator reads back the file the previous agent wrote; no in-memory artifact is passed between stages. This makes each artifact independently inspectable and re-runnable from any mid-point.

All Anthropic API calls are synchronous and blocking. One call per agent, no streaming required in V1. The Anthropic API key is read from the environment at startup; the CLI halts with an actionable message if it is absent.

## Boundaries

**No version history / artifact diffing.** Artifacts are overwritten on each run. Version control of artifacts is a deliberate V1 exclusion pending D-001; the Artifact Store module is the single change point if a history policy is later adopted.

**No web service or HTTP API.** CLI only. A web interface would add operational surface the Vision explicitly rejects.

**No inter-agent communication or deliberation.** Agents are isolated; each reads only its designated upstream files. No shared memory, no message bus, no agent-to-agent calls.

**No active coherence verification.** Downstream agents trust that their upstream artifact is valid because the Input Validator confirmed structure. Semantic coherence checking across artifacts is excluded per D-003.

**No repository or codebase interaction.** Foundry reads and writes only its own markdown artifacts. No Git operations, no code parsing.

**No scheduling, ticketing, or external integrations.** Work Orders are markdown on disk; no push to Jira, Linear, GitHub Issues, or any other system.

**No multi-project or multi-user workspace.** One project directory, one founder at a time. Directory isolation for concurrent projects is out of scope for V1.

**No streaming or partial-artifact display.** The CLI waits for each API call to complete before writing and proceeding. Progress indication is a plain status line to stdout, not a streaming display.

## Tech Stack

| Technology | Role | Notes |
|---|---|---|
| Python 3.12 | Runtime language | Specified by Vision. |
| `uv` | Dependency and environment management | Specified by Vision. |
| Anthropic SDK | LLM API client — one call per agent | Specified by Vision. Model ID: `claude-opus-4-5` (Assumed, override-able via config or env var; see D-004). |
| `pydantic` | Structured configuration and input validation models | Specified by Vision. Used for CLI config, validated settings, and Input Validator schema. |
| `jinja2` | Prompt templating — one `.j2` template per agent | Specified by Vision. Template directory: `foundry/templates/` (Assumed). |
| `pytest` | Test runner | Specified by Vision. Unit tests for Validator, Orchestrator stage logic, and Artifact Store; integration tests for full pipeline with mocked Anthropic responses. |
| Markdown (plain text files) | Artifact storage format | Specified by Vision. All artifacts are `.md` files on disk. Output directory: `./artifacts/` relative to working directory (Assumed, override-able via CLI flag; see D-005). |

## Assumptions

- The Anthropic API is reachable from the machine running Foundry and the caller holds a valid API key. No offline or local-model mode is provided.
- A single synchronous API call per agent, with no retries beyond what the Anthropic SDK provides by default, is sufficient reliability for V1 single-founder use.
- The founder's working directory is the project root; relative paths for artifact input/output resolve correctly from that location.
- Prompt templates (`.j2` files) are correct and stable enough to produce well-structured output without runtime template validation beyond Jinja2 rendering itself.
- The founder provides a Product Input that meets the structural requirements validated by Input Validator; the quality of that input is the primary determinant of artifact quality, as stated in the Vision.
- One project per invocation is the operative usage shape; no concurrency or locking mechanism is needed.
- Markdown section headers are the sufficient structural contract between agents; no richer schema (JSON, YAML front matter) is needed to pass context between stages in V1.

## Decision List

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | Should generated artifacts be version-controlled (history preserved) or is silent overwrite acceptable in V1? | Founder | Product | Open | D-005 | Overwrite is simpler operationally, but version history changes the value proposition and affects re-run semantics materially. The Artifact Store module isolates this decision to one change point, but the policy must be set before the store is implemented. Blast radius: re-run UX, user trust, and artifact naming scheme. |
| D-002 | How strict should structural validation be on the founder's Product Input? | Product | Product | Assumed | — | Default: validate that all required section headers are present and non-empty; emit a clear error and halt. Deep semantic validation deferred. Reversible and low-cost to tighten later. |
| D-003 | When does coherence between artifacts require active verification rather than relying on each agent reading its upstream input? | Architect | Technical | Deferred | — | Passive read-upstream is the V1 default. Active coherence checking is a post-V1 candidate once the artifact pipeline is proven. |
| D-004 | Which Anthropic model ID backs each agent? | Architect | Technical | Assumed | — | Default: `claude-opus-4-5` for all agents. Anthropic is the named provider; model ID is a reversible parameter. Override-able per-agent via environment variable or a config file without code change. |
| D-005 | Where does Foundry write output artifacts, and is the path configurable? | Architect | Technical | Assumed | D-001 | Default output directory: `./artifacts/` relative to the working directory at invocation. Override-able via a `--output-dir` CLI flag. Reversible and low blast-radius; chosen to keep artifacts co-located with the project without polluting the working directory root. |
| D-006 | How should the CLI represent stage selection — named stages, numeric index, or re-run-from-stage flag? | Architect | Technical | Assumed | — | Default: `--from <stage>` flag accepting one of `vision`, `architecture`, `roadmap`, `work_orders`. Runs the named stage and all downstream stages. Reversible UX decision; simple to change before first release. |
| D-007 | Should per-agent Anthropic API parameters (temperature, max_tokens) be configurable by the founder or hardcoded? | Architect | Technical | Assumed | — | Default: hardcoded sensible defaults per agent (temperature 1.0 per Anthropic guidance for extended thinking; max_tokens 4096, Assumed). Override-able via environment variables per agent if needed. Reversible; complexity of a full config surface is not warranted in V1. |
| D-008 | Should the CLI provide a dry-run mode that validates inputs and renders prompts without calling the Anthropic API? | Architect | Technical | Deferred | — | Useful for development and prompt iteration but not blocking V1 delivery. Deferring avoids premature interface commitment. |
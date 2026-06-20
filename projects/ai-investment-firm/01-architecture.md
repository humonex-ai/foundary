# Architecture — ai-investment-firm

## Overview

The system is a server-side pipeline with a thin web front-end that takes a ticker and a research question as input, retrieves and snapshots licensed source documents (SEC filings, earnings transcripts, fundamental data), passes non-MNPI-flagged content through an LLM to extract structured claims with inline citations, assembles those claims into a templated investment memo, and persists the full provenance record (sources, passages, model interactions, timestamps, analyst edits) in an append-only store that compliance can query without engineering help. Every component is deployed on infrastructure the team controls; no document content crosses a third-party boundary until a mandatory MNPI gate has cleared it. The architecture is deliberately narrow and low-operational-burden, sized for one part-time engineer.

---

## Components

### 1. Ingestion Service
Single responsibility: fetch, validate, and snapshot source documents from licensed APIs (SEC EDGAR, transcript provider, fundamental data feed) on demand. Writes an immutable snapshot to the Document Store and emits an ingestion event with source URL, license identifier, and timestamp. Never modifies a snapshot after it is written.

### 2. MNPI Gate
Single responsibility: inspect every document chunk before it is forwarded to any external model call. Applies a rule-based and keyword heuristic screen (e.g., detection of non-public deal terms, unannounced material events, restricted-list tickers). On a positive flag: blocks the chunk from leaving the controlled environment, writes a quarantine record to the Audit Log, and surfaces a review task to the compliance-designated reviewer. Content passes downstream only after explicit clearance. This gate is the single chokepoint between ingested content and any external API.

### 3. Extraction Engine
Single responsibility: send cleared document passages to the configured LLM (provider determined by D-004) with a structured prompt that requires the model to return every claim paired with the source document ID, passage offset, and verbatim quoted text. Stores raw model responses alongside prompt metadata in the Audit Log. Produces a set of typed, cited claims (numeric figures, qualitative assertions, management guidance items).

### 4. Memo Assembler
Single responsibility: arrange extracted claims into the canonical memo template (D-005 default: thesis summary, key assumptions, supporting evidence with citations, bear case, decision/outcome log), producing a structured draft document. Each section cell references the claim IDs from which it was populated. Does not generate new factual content; it only arranges already-extracted, already-cited claims.

### 5. Document Store
Single responsibility: hold immutable snapshots of every ingested source document. Write-once; no update or delete path in the normal operation flow (legal-hold and retention policy per D-002). Addressed by a content hash so a citation can permanently resolve to the exact bytes that existed at ingestion time.

### 6. Audit Log
Single responsibility: record every system event in append-only, structured form — ingestion events (source, timestamp, license tag), MNPI gate decisions (pass/quarantine, reviewer, timestamp), model interactions (prompt hash, response hash, model id, timestamp), memo versions (author, diff, timestamp), and analyst edits. This is the artifact compliance reads directly via the Provenance UI.

### 7. Provenance UI
Single responsibility: provide a read-only, search-and-browse interface over the Audit Log and Document Store. Lets a compliance officer retrieve the complete record for any memo — which sources were ingested when, what the MNPI gate decided, what the model was sent and returned, and every analyst edit — without writing queries or involving engineering.

### 8. Analyst Workspace
Single responsibility: present analysts with the draft memo, inline citations, and tools to accept, edit, or reject individual claims. Saves every edit as a versioned delta to the Audit Log. Provides the ticker + question intake form that triggers the pipeline.

### 9. Orchestrator
Single responsibility: sequence the pipeline steps — Ingestion → MNPI Gate → Extraction Engine → Memo Assembler — handle retries, and surface status to the Analyst Workspace. Stateless between runs; all durable state lives in the Document Store and Audit Log.

---

## Data & Control Flow

```
Analyst enters ticker + research question
        │
        ▼
[Orchestrator] triggers Ingestion Service
        │
        ▼
[Ingestion Service] fetches source docs from licensed APIs
  → writes immutable snapshot to [Document Store] (content-addressed)
  → emits ingestion event to [Audit Log]
        │
        ▼
[MNPI Gate] receives each document chunk
  → PASS: chunk proceeds; gate decision logged to [Audit Log]
  → FLAG: chunk quarantined; review task raised; pipeline pauses
          until compliance reviewer explicitly clears or rejects
        │ (cleared chunks only)
        ▼
[Extraction Engine] sends cleared passages to LLM (D-004)
  → prompt + response hash logged to [Audit Log]
  → returns typed claims, each with: source_doc_id, passage_offset,
    verbatim_quote, claim_type, extracted_value
        │
        ▼
[Memo Assembler] maps claims → memo template sections
  → produces draft memo referencing claim IDs (not raw text)
  → draft saved as v0 to [Audit Log]
        │
        ▼
[Analyst Workspace] presents draft + inline citations to analyst
  → analyst accepts / edits / rejects claims
  → each edit saved as versioned delta to [Audit Log]
  → analyst marks memo ready for PM review
        │
        ▼
[Portfolio Manager] reads final memo in Analyst Workspace
  → any PM annotation saved to [Audit Log]

[Compliance Officer] uses [Provenance UI] at any time
  → queries [Audit Log] + [Document Store]
  → reconstructs full provenance without engineering involvement
```

State lives in two places only: the Document Store (source snapshots) and the Audit Log (all events and memo versions). The Orchestrator and all processing components are stateless.

---

## Boundaries

**Excluded: Automated order placement or signal generation.** The system produces memos; it has no brokerage connectivity, no position-management interface, and no output path that could influence trade execution. This is a hard product boundary, not a phased omission.

**Excluded: Real-time market data display or ticker-streaming.** The system ingests point-in-time snapshots of licensed data on demand. It is not a market-data terminal and does not maintain live feeds or display streaming prices.

**Excluded: Multi-user role-based access beyond the three defined roles (Analyst, PM, Compliance).** Adding a richer permission model would materially increase operational burden disproportionate to team size.

**Excluded: Asset classes beyond long/short equities in V1.** The memo template, data-source integrations, and claim taxonomy are scoped to equities. Expansion is gated on D-003.

**Excluded: Self-serve data-source onboarding.** Analysts cannot add new licensed data connectors without an engineer. Keeping connector code in the Ingestion Service under engineering control is the primary mechanism for enforcing license-compliance.

**Excluded: Local/on-premises LLM hosting as a built component.** Whether a local model is required is determined by D-001 and D-004. If those decisions require it, the Extraction Engine's model-call interface accommodates a local endpoint, but the architecture does not pre-build local model infrastructure.

**Excluded: Synchronous compliance approval in the normal pipeline.** Compliance uses the Provenance UI for retrospective review; they are only inserted into the active pipeline when the MNPI Gate raises a flag. This preserves the sub-one-hour cycle time goal for non-flagged content.

---

## Tech Stack

The Vision names no specific technologies by name in its Constraints section — the Constraints are regulatory, operational, and architectural in nature, not technology choices. Therefore the technology decisions required to implement this architecture are recorded in the Decision List. The components and their responsibilities are defined above; the implementing technologies are open (or assumed with defaults) as documented in the Decision List.

The following are technology-class requirements derived directly from the architecture:

| Technology Class | Requirement Source | Default / Note |
|---|---|---|
| LLM provider / model | Extraction Engine | Determined by D-004 (blocked on D-001). Model id: Assumed once provider is decided — see D-007. |
| Append-only structured log store | Audit Log | Must support compliance querying without code. See D-008. |
| Immutable object store | Document Store | Write-once, content-addressed. See D-006 (Deferred) and D-009. |
| MNPI heuristic implementation | MNPI Gate | Rule-based keyword screen; specifics per D-001. |
| Web application framework | Analyst Workspace + Provenance UI | See D-010. |
| Orchestration mechanism | Orchestrator | See D-011. |

No technologies are named in the Vision's Constraints section, so no specific vendor is mandated. All technology selections are recorded in the Decision List below for explicit decision-making, sized to one part-time engineer.

---

## Assumptions

- Licensed API access to SEC EDGAR, at least one earnings-call transcript provider, and at least one fundamental data feed is either already active or will be secured before build begins, as stated in the Vision.
- The team produces a tractable number of memos per week (estimated low tens) — no horizontal scaling or high-throughput queue architecture is required.
- A single deployment environment (e.g., a single cloud account or on-premises server) under the team's direct control is available and sufficient; multi-region or high-availability infrastructure is not required.
- Analysts have browser access to an internal web application; no mobile or offline client is needed.
- The compliance officer has sufficient technical literacy to use a structured search-and-browse UI without requiring natural-language querying or custom report generation.
- The part-time engineer has sufficient familiarity with web application development, API integration, and basic cloud infrastructure to build and maintain the described components.
- The MNPI Gate's heuristic will produce a manageable false-positive rate that does not unacceptably slow the pipeline; the acceptable rate is subject to calibration with compliance (per D-001).
- Earnings call transcripts are available via the licensed transcript API in machine-readable text form (not audio requiring transcription).
- A single canonical memo template (D-005 default) covers the large majority of theses; the architecture does not need to support arbitrary template types at launch.

---

## Decision List

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | How is MNPI detected before content is sent to any third-party model, and what happens when a flag is triggered? | Compliance | Compliance | Open | D-004, D-007 | High blast radius: getting this wrong creates regulatory exposure and potential legal liability. The detection heuristic, the containment action (block, quarantine, route to local model), and the review workflow must all be defined before any external model integration is built. Cannot be assumed or deferred. |
| D-002 | What is the retention policy for memos and their source document snapshots? | Compliance / Legal | Compliance | Open | D-009 | Retention period, storage jurisdiction, deletion triggers, and legal-hold procedures carry regulatory and data-safety implications. Irreversible if data is deleted prematurely or stored in violation of policy. Must be decided before storage architecture is finalized. |
| D-003 | Should V1 support asset classes beyond long/short equities (e.g., credit, macro)? | Product | Product | Open | — | Expands scope and target users if yes; changes the memo template model, data source requirements, and potentially the user base. High blast radius on scope — cannot be assumed away with a default without explicit product sign-off. |
| D-004 | Which third-party LLM provider(s), if any, are approved for use given the MNPI constraint? | Architect / Compliance | Technical | Open | D-007 | Depends on resolution of D-001. Provider selection determines data processing agreements, model isolation options, and feasibility of on-premises or private deployment for sensitive content. Cannot be decided until MNPI control policy is established. |
| D-005 | What is the canonical memo template structure for V1? | Product | Product | Assumed | — | Low blast radius and fully reversible through iteration. Default: a structured template covering thesis summary, key assumptions, supporting evidence (with citations), bear case, and decision/outcome log. Analysts refine drafts against this structure. Can be adjusted without architectural change. |
| D-006 | How are source document snapshots stored to support long-term citation integrity (i.e., source content does not mutate after ingestion)? | Architect | Technical | Deferred | — | Important for audit trail durability but does not block initial scoping. Needs resolution before production deployment; the constraint is known and the options (immutable object store, content-addressed storage) are low-controversy once MNPI storage policy is settled via D-002. |
| D-007 | Which specific LLM model id will be used by the Extraction Engine? | Architect | Technical | Open | — | Blocked on D-004 (provider selection) and D-001 (MNPI policy). Once provider is approved, a default model id will be selected and recorded as Assumed. Cannot be assumed before the provider is known. |
| D-008 | What technology implements the Audit Log (append-only structured store queryable by compliance without engineering)? | Architect | Technical | Deferred | — | Real but non-blocking at this stage. The requirement is clear (append-only, structured, compliance-queryable). Options include a managed database with a read-only compliance role and a simple UI, or a dedicated log store. Reversible choice; can be decided when provider landscape (D-004) and retention policy (D-002) are clearer. One part-time engineer constraint favors a managed service over a custom solution. |
| D-009 | What technology implements the Document Store (immutable, content-addressed object storage)? | Architect | Technical | Deferred | D-002 | Blocked in practice on D-002 (retention and jurisdiction policy). Options include a managed object store with object-lock enabled. Reversible and low-controversy; deferred until retention policy is settled. |
| D-010 | What web application framework implements the Analyst Workspace and Provenance UI? | Architect | Technical | Deferred | — | Real but non-blocking. Choice is reversible and should be sized to what the one part-time engineer is most productive with. No framework is mandated by the Vision. |
| D-011 | What mechanism implements the Orchestrator (pipeline sequencing, retry, status)? | Architect | Technical | Deferred | — | Real but non-blocking. Options range from a simple task queue to a lightweight workflow library. Should be the simplest option that handles retry and pause-on-MNPI-flag reliably, consistent with one part-time engineer operational burden. |
| D-012 | How are analyst and compliance user identities managed and authenticated? | Architect / Compliance | Technical / Compliance | Open | — | Authentication and access control have compliance and data-safety implications (who can read MNPI-flagged quarantine records, who can clear flags). Cannot be assumed; requires explicit decision with compliance input. Blast radius: incorrect access control could expose quarantined content. |
| D-013 | What serialization format is used for claims produced by the Extraction Engine and stored in the Audit Log? | Architect | Technical | Assumed | — | Reversible parameter of the Audit Log and Extraction Engine components. Default: JSON with a defined schema (source_doc_id, passage_offset, verbatim_quote, claim_type, extracted_value, timestamp). Human-readable, tool-portable, and sufficient for the expected memo volume. Override-able without architectural change. |
| D-014 | What content-hashing algorithm is used for Document Store content-addressing? | Architect | Technical | Assumed | — | Reversible parameter with no material blast radius. Default: SHA-256. Ubiquitous, collision-resistant, and supported by all candidate object stores. Override-able if a storage provider mandates a different scheme. |
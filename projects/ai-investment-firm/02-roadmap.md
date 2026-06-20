# Roadmap — ai-investment-firm

## Goal

Deliver, in the fewest phases that preserve safety and trust, a system where analysts go from a ticker and a research question to a structured, fully-cited draft memo in under one hour, with every source traceable and every compliance officer empowered to inspect that trail without engineering help — and where no content reaches an external model before a mandatory MNPI gate has cleared it.

---

## Phases

### Phase 1 — Auditable Document Vault with MNPI Gate

**Capability delivered:** An analyst can submit a ticker and a research question, and the system will fetch, snapshot, and store the relevant licensed source documents (SEC filings, earnings transcripts, fundamental data). Every ingested document is held in an immutable, content-addressed store with a permanent audit record of what was fetched, from which source, under which license, and at what time. Before any document chunk can proceed further in the system, it passes through the MNPI gate: flagged content is quarantined, a review task is surfaced to the compliance-designated reviewer, and the pipeline pauses until explicit clearance is recorded. Non-flagged content is logged as cleared and held ready. Nothing crosses an external model boundary in this phase.

The Provenance UI is live at this phase in its foundational form: compliance can already search and browse ingestion events, MNPI gate decisions (pass or quarantine, reviewer identity, timestamp), and document snapshots — without engineering involvement.

**Done when:**
- An analyst submits a ticker and question and the system retrieves and snapshots all relevant source documents without manual intervention.
- Every ingested document chunk has been evaluated by the MNPI gate, with the decision (pass/quarantine), timestamp, and reviewer logged to the audit record.
- Quarantined content is inaccessible to downstream processing and visible to the compliance reviewer as a pending task.
- A compliance officer can open the Provenance UI, search for any ticker, and see the complete ingestion and gate record for that ticker without asking an engineer.
- The Document Store is write-once and content-addressed; no snapshot can be modified or silently deleted through normal operation.

---

### Phase 2 — AI Extraction with Full Citation Chain

**Capability delivered:** Cleared document passages are sent to the approved LLM (D-004/D-007) with a prompt that requires every returned claim to carry the source document ID, passage offset, and verbatim quoted text. The system produces a set of typed, cited claims — numeric figures, qualitative assertions, management guidance — each permanently linked to the exact bytes in the Document Store from which it was drawn. Every model interaction (prompt hash, response hash, model ID, timestamp) is appended to the audit log. No claim enters the system without its citation; no model call happens without its audit record.

Analysts can inspect the raw extracted claims and their citations in the workspace at the end of this phase, even before memo assembly is complete. This gives them immediate visibility into what the AI actually said and what evidence it drew from.

**Done when:**
- Every cleared document passage results in a structured set of claims, each carrying source_doc_id, passage_offset, verbatim_quote, claim_type, and extracted_value.
- Every LLM call is recorded in the audit log with prompt hash, response hash, model ID, and timestamp.
- No content reaches the LLM without a recorded MNPI gate clearance from Phase 1.
- Compliance can open the Provenance UI and see, for any ticker, the full chain from ingestion through gate decision through model interaction through the claims that resulted.
- An analyst reviewing extracted claims can click any claim and see the source passage it was drawn from.

---

### Phase 3 — Draft Memo Assembly and Analyst Workspace

**Capability delivered:** Extracted, cited claims are assembled into the canonical memo template (thesis summary, key assumptions, supporting evidence with citations, bear case, decision/outcome log). The analyst receives a structured draft where every section cell references the claim IDs that populate it — no section contains a bare assertion without a traceable source. The analyst can accept, edit, or reject individual claims; every such action is saved as a versioned delta to the audit log. When the analyst marks the memo ready, the portfolio manager can read the final document. Any PM annotation is also logged. The complete lifecycle — from ticker submission through ingestion, gate decision, extraction, assembly, analyst edits, and PM review — is permanently readable by compliance in the Provenance UI with no engineering involvement.

The one-hour cycle time target is measurable and checkable at this phase.

**Done when:**
- An analyst can go from ticker and research question to a structured, section-complete draft memo in under one hour for non-flagged content.
- Every numeric figure and quoted claim in the memo carries an inline citation resolvable to the exact source passage.
- Analyst edits and rejections are versioned in the audit log; no edit overwrites a prior state.
- The portfolio manager can read the memo and add annotations that are also logged.
- Compliance can retrieve the full provenance record for any memo — sources, gate decisions, model interactions, memo versions, analyst edits, PM annotations — entirely through the Provenance UI.
- The PM self-reports their time shifting toward judgment and away from assembly.

---

## Sequencing Principle

**Phase 1 before anything else** because the MNPI gate is a non-negotiable hard stop: no content may reach an external model without it. Building the vault and the gate first means the team can ingest real documents, validate the gate's behavior, and calibrate its false-positive rate with compliance before any LLM integration exists. It also gives compliance the ability to see and trust the provenance system from day one, rather than retroactively. The audit log and document store established in Phase 1 are the foundation every subsequent phase writes into; they cannot be safely retrofitted later.

**Phase 2 before memo assembly** because the memo is only as trustworthy as the extraction beneath it. Validating that the claim-citation chain is complete and accurate — and that compliance can already inspect it — before the memo template is introduced keeps the trust surface small and errors easy to attribute. It also allows the extraction prompt and the claim schema to be tuned against real documents before assembly logic depends on them.

**Phase 3 last** because it is the user-facing synthesis of everything below it. Its done-when criteria (sub-one-hour cycle, inline citations, full provenance readable by compliance) are only meaningful once the vault, gate, and extraction chain are solid. Rushing to the assembled memo before the underlying chain is trusted would produce a product that looks finished but cannot be audited — inverting the priorities of the Vision.

---

## Deferred

- **Local / on-premises LLM hosting.** If D-001 and D-004 determine that certain content categories require a locally-hosted model rather than an external API, the Extraction Engine's model-call interface accommodates this — but the infrastructure to host a local model is not built as part of V1. It is a contingent extension triggered only by compliance decisions.
- **Asset classes beyond long/short equities.** Memo template, data-source integrations, and claim taxonomy are scoped to equities in V1. Expansion awaits resolution of D-003.
- **Synchronous compliance approval in the normal pipeline.** Compliance interacts through the Provenance UI for retrospective review. The only point where compliance enters the active pipeline is an MNPI flag. A richer real-time approval workflow is deferred to preserve sub-one-hour cycle time.
- **Self-serve data-source onboarding.** Analysts cannot add new licensed data connectors without an engineer. This is an intentional control, not a gap to fill later without explicit decision.
- **Richer role-based access control beyond three roles.** Multi-user permission models beyond Analyst / PM / Compliance are excluded from V1 as disproportionate to team size.
- **Natural-language querying in the Provenance UI.** Compliance uses structured search and browse. A conversational or NL query interface is deferred; it is not needed to meet the stated compliance goal.

---

## Assumptions

- D-001 (MNPI detection policy) and D-012 (identity and authentication) will be resolved by compliance before Phase 1 build begins; Phase 1 cannot be completed without them.
- D-004 (approved LLM provider) and D-007 (model ID) will be resolved before Phase 2 build begins; the extraction engine has no implementation without them.
- D-002 (retention policy) and D-006 (citation-integrity storage) will be resolved before Phase 3 is promoted to production; the audit and document store can be built to accommodate the likely options, but production deployment requires these to be locked.
- Licensed API access to SEC EDGAR, at least one earnings-call transcript provider, and at least one fundamental data feed is either already active or will be secured before Phase 1 begins, as stated in the Vision.
- The compliance officer and at least one analyst are available for review and feedback at the end of each phase; their sign-off gates the transition to the next phase.
- The part-time engineer is available for continuous (if part-time) work across all three phases; a gap or change in engineering availability would re-sequence the roadmap.
- The MNPI gate's heuristic will achieve a manageable false-positive rate after calibration with compliance during Phase 1; an unacceptably high rate would extend Phase 1 until the rate is acceptable.
- Earnings call transcripts are available in machine-readable text form from the licensed provider; audio transcription is not required.
- The expected memo volume (estimated low tens per week) does not require horizontal scaling; a single controlled deployment environment is sufficient throughout V1.

---

## Decision List

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | How is MNPI detected before content is sent to any third-party model, and what happens when a flag is triggered? | Compliance | Compliance | Open | D-004, D-007, Phase 1 completion | High blast radius: getting this wrong creates regulatory exposure and potential legal liability. The detection heuristic, the containment action (block, quarantine, route to local model), and the review workflow must all be defined before any external model integration is built. Cannot be assumed or deferred. |
| D-002 | What is the retention policy for memos and their source document snapshots? | Compliance / Legal | Compliance | Open | D-009, Phase 3 production deployment | Retention period, storage jurisdiction, deletion triggers, and legal-hold procedures carry regulatory and data-safety implications. Irreversible if data is deleted prematurely or stored in violation of policy. Must be decided before storage architecture is finalized. |
| D-003 | Should V1 support asset classes beyond long/short equities (e.g., credit, macro)? | Product | Product | Open | — | Expands scope and target users if yes; changes the memo template model, data source requirements, and potentially the user base. High blast radius on scope — cannot be assumed away with a default without explicit product sign-off. |
| D-004 | Which third-party LLM provider(s), if any, are approved for use given the MNPI constraint? | Architect / Compliance | Technical | Open | D-007, Phase 2 start | Depends on resolution of D-001. Provider selection determines data processing agreements, model isolation options, and feasibility of on-premises or private deployment for sensitive content. Cannot be decided until MNPI control policy is established. |
| D-005 | What is the canonical memo template structure for V1? | Product | Product | Assumed | — | Low blast radius and fully reversible through iteration. Default: a structured template covering thesis summary, key assumptions, supporting evidence (with citations), bear case, and decision/outcome log. Analysts refine drafts against this structure. Can be adjusted without architectural change. |
| D-006 | How are source document snapshots stored to support long-term citation integrity (i.e., source content does not mutate after ingestion)? | Architect | Technical | Deferred | — | Important for audit trail durability but does not block initial scoping. Needs resolution before production deployment; the constraint is known and the options (immutable object store, content-addressed storage) are low-controversy once MNPI storage policy is settled via D-002. |
| D-007 | Which specific LLM model ID will be used by the Extraction Engine? | Architect | Technical | Open | Phase 2 start | Blocked on D-004 (provider selection) and D-001 (MNPI policy). Once provider is approved, a default model ID will be selected and recorded as Assumed. Cannot be assumed before the provider is known. |
| D-008 | What technology implements the Audit Log (append-only structured store queryable by compliance without engineering)? | Architect | Technical | Deferred | — | Real but non-blocking at this stage. The requirement is clear (append-only, structured, compliance-queryable). Options include a managed database with a read-only compliance role and a simple UI, or a dedicated log store. Reversible choice; can be decided when provider landscape (D-004) and retention policy (D-002) are clearer. One part-time engineer constraint favors a managed service over a custom solution. |
| D-009 | What technology implements the Document Store (immutable, content-addressed object storage)? | Architect | Technical | Deferred | D-002 | Blocked in practice on D-002 (retention and jurisdiction policy). Options include a managed object store with object-lock enabled. Reversible and low-controversy; deferred until retention policy is settled. |
| D-010 | What web application framework implements the Analyst Workspace and Provenance UI? | Architect | Technical | Deferred | — | Real but non-blocking. Choice is reversible and should be sized to what the one part-time engineer is most productive with. No framework is mandated by the Vision. |
| D-011 | What mechanism implements the Orchestrator (pipeline sequencing, retry, status)? | Architect | Technical | Deferred | — | Real but non-blocking. Options range from a simple task queue to a lightweight workflow library. Should be the simplest option that handles retry and pause-on-MNPI-flag reliably, consistent with one part-time engineer operational burden. |
| D-012 | How are analyst and compliance user identities managed and authenticated? | Architect / Compliance | Technical / Compliance | Open | Phase 1 completion | Authentication and access control have compliance and data-safety implications (who can read MNPI-flagged quarantine records, who can clear flags). Cannot be assumed; requires explicit decision with compliance input. Blast radius: incorrect access control could expose quarantined content to unauthorized users. Must be resolved before Phase 1 is complete. |
| D-013 | What serialization format is used for claims produced by the Extraction Engine and stored in the Audit Log? | Architect | Technical | Assumed | — | Reversible parameter of the Audit Log and Extraction Engine components. Default: JSON with a defined schema (source_doc_id, passage_offset, verbatim_quote, claim_type, extracted_value, timestamp). Human-readable, tool-portable, and sufficient for the expected memo volume. Override-able without architectural change. |
| D-014 | What content-hashing algorithm is used for Document Store content-addressing? | Architect | Technical | Assumed | — | Reversible parameter with no material blast radius. Default: SHA-256. Ubiquitous, collision-resistant, and supported by all candidate object stores. Override-able if a storage provider mandates a different scheme. |
| D-015 | At what phase boundary does compliance formally sign off before the next phase begins? | Product / Compliance | Operational | Open | Phase transitions | Compliance sign-off at the end of Phase 1 (gate behavior validated) and Phase 2 (extraction and citation chain validated) is assumed in the sequencing, but the formal sign-off criteria and who has authority to grant it have not been defined. Incorrect sequencing here could mean production deployment proceeds before compliance is satisfied with the audit chain. Must be agreed before Phase 1 begins. |
| D-016 | Will Phase 1 be deployed in a production-equivalent environment or a controlled staging environment? | Architect / Compliance | Operational | Open | Phase 1 start | Real documents (potentially containing sensitive financial content) will be ingested and MNPI-screened during Phase 1. Whether this happens in a production environment with full data controls or a sandboxed staging environment with synthetic or anonymized data has compliance and data-safety implications. Cannot be assumed; must be decided with compliance before Phase 1 ingests live documents. |
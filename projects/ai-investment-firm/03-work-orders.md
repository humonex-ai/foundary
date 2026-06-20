# Work Orders — ai-investment-firm

## Format
_Each Work Order has: an ID, a goal, scope (in/out), dependencies, a done-when check, and metadata — Complexity (S/M/L) and Risk (Low/Medium/High). No time estimates._

## Work Orders
_One block per shippable outcome, in dependency order._

---

### WO-001 — Auditable Document Vault with MNPI Gate
- **Goal:** An analyst can submit a ticker and research question and the system will fetch, snapshot, and store all relevant licensed source documents (SEC filings, earnings transcripts, fundamental data) in an immutable, content-addressed vault. Every document chunk is evaluated by the MNPI gate before it can proceed anywhere; flagged content is quarantined and surfaces a pending review task to the compliance reviewer; non-flagged content is logged as cleared. Nothing crosses an external model boundary. The pipeline pauses on any quarantine until explicit clearance is recorded by the designated reviewer.
- **In scope:**
  - Ingestion connectors for SEC EDGAR, licensed earnings-call transcript provider, and licensed fundamental data feed; each connector fetches documents relevant to the submitted ticker and question without manual intervention.
  - Content-addressed, write-once document store: every snapshot stored with its SHA-256 hash as its address; no snapshot can be modified or silently deleted through normal operation.
  - Audit log record per ingested chunk: source URL/API, license identifier, fetch timestamp, content hash, and gate decision.
  - MNPI gate: evaluates every ingested chunk per the detection policy resolved in D-001; emits pass (logged as cleared) or quarantine (chunk withheld from downstream, review task created).
  - Quarantine queue: holds flagged chunks inaccessible to any downstream step; surfaces them as pending tasks to the compliance-designated reviewer; records reviewer identity, decision, and timestamp on clearance.
  - Pipeline pause-and-resume: any quarantined chunk for a given submission pauses that submission's downstream processing; clearance resumes it.
  - Role-scoped access control per D-012: Analyst, PM, and Compliance roles enforced from day one; quarantine records accessible only to Compliance role.
  - User authentication per D-012.
  - Provenance UI — foundational view: compliance can search by ticker and see the complete ingestion record (documents fetched, sources, licenses, timestamps, gate decisions, reviewer identity) without engineering involvement; structured search and browse only.
  - End-to-end tests: a submission with only clean content clears fully; a submission with flagged content quarantines correctly, blocks downstream, surfaces the review task, and resumes only after recorded clearance; the document store rejects any mutation attempt.
- **Out of scope:**
  - Any LLM or external model call.
  - Claim extraction, memo assembly, or analyst workspace beyond the Provenance UI.
  - Asset classes beyond long/short equities.
  - Self-serve data-source onboarding by analysts.
  - Natural-language querying in the Provenance UI.
  - Local/on-premises model hosting infrastructure.
  - Roles beyond Analyst / PM / Compliance.
- **Depends on:** None (first Work Order).
- **Done when:**
  - An analyst submits a ticker and question; the system retrieves and snapshots all relevant source documents without manual steps.
  - Every chunk has an audit log entry with source, license, timestamp, content hash, and gate decision (pass or quarantine).
  - A chunk flagged by the MNPI gate cannot be retrieved by any downstream process; it appears as a pending task to the Compliance-role reviewer.
  - A compliance officer opens the Provenance UI, searches a ticker, and sees the complete ingestion and gate record — no engineer required.
  - Attempting to overwrite or delete any stored snapshot through the application's normal operation fails and is logged.
  - A quarantined submission remains paused; after the compliance reviewer records clearance, the pipeline resumes and the clearance is in the audit log.
  - Access-control tests confirm a non-Compliance user cannot read quarantine records; a non-Analyst user cannot submit tickers.
  - Compliance formally signs off on gate behavior per D-015 criteria before WO-002 begins.
- **Complexity:** L. **Risk:** High.

---

### WO-002 — AI Extraction with Full Citation Chain
- **Goal:** Every MNPI-cleared document passage is sent to the approved LLM and returns a structured, typed claim carrying the exact source document ID, passage offset, and verbatim quoted text. Every model interaction is recorded in the audit log. No model call happens without a recorded gate clearance. Analysts can inspect the raw extracted claims and click any claim to see the source passage it came from.
- **In scope:**
  - Extraction engine: takes cleared document passages from WO-001's vault, constructs a prompt that mandates per-claim citation fields (source_doc_id, passage_offset, verbatim_quote, claim_type, extracted_value), and calls the approved LLM (D-004/D-007).
  - Gate-clearance enforcement: the extraction engine verifies a recorded MNPI clearance exists for every passage before constructing any prompt; no bypass path.
  - Audit log record per LLM call: prompt hash, response hash, model ID, timestamp, and the submission/ticker context.
  - Claim store: structured records (JSON per D-013 schema) linked to the source chunk in the document store via content hash.
  - Citation integrity check: after each extraction call, verify that every returned claim's verbatim_quote is a byte-exact substring of the source passage at the stated offset; reject and log any claim that fails.
  - Analyst workspace — claims view: analysts can list extracted claims for a submission, click any claim, and see the source passage highlighted in the stored document snapshot.
  - Provenance UI — extraction layer: compliance can see, for any ticker, the chain from ingestion → gate decision → LLM call record → resulting claims.
  - End-to-end tests: a cleared passage produces correctly structured claims with verified citations; a passage without a recorded clearance is rejected before any prompt is sent; a claim whose verbatim_quote does not match the source bytes is rejected and logged; all LLM calls appear in the audit log.
- **Out of scope:**
  - Memo template assembly or the full analyst workspace.
  - Analyst accept/reject/edit of individual claims (that is part of WO-003).
  - Local/on-premises LLM hosting infrastructure.
  - PM annotations.
  - Asset classes beyond equities.
- **Depends on:** WO-001.
- **Done when:**
  - Every cleared passage for a submission produces a structured claim set; each claim carries source_doc_id, passage_offset, verbatim_quote, claim_type, and extracted_value.
  - Every LLM call has an audit log entry with prompt hash, response hash, model ID, and timestamp.
  - No prompt is constructed for a passage without a recorded MNPI gate clearance; this is verified by a test that attempts to bypass the gate and confirms rejection.
  - Any claim whose verbatim_quote is not a byte-exact match to the source passage is rejected and appears in the audit log as a citation failure.
  - An analyst opens the claims view for a submission, clicks a claim, and the source passage is shown; the claim is visually linked to the correct document and offset.
  - Compliance opens the Provenance UI and sees the full chain: ingestion → gate decision → model interaction → claims produced.
  - Compliance formally signs off on the extraction and citation chain per D-015 criteria before WO-003 begins.
- **Complexity:** L. **Risk:** High.

---

### WO-003 — Draft Memo Assembly and Analyst Workspace
- **Goal:** Extracted, cited claims are assembled into a structured draft memo following the canonical template (D-005). Every section contains only claims with traceable citations; no bare assertions. Analysts can accept, edit, or reject individual claims; every action is a versioned, append-only delta in the audit log. Portfolio managers can read the final memo and add logged annotations. The complete lifecycle — submission through ingestion, gate, extraction, assembly, analyst edits, and PM annotations — is readable by compliance in the Provenance UI with no engineering involvement. The sub-one-hour cycle time is measurable for non-flagged submissions.
- **In scope:**
  - Memo assembler: maps typed claims from the claim store into the canonical template sections (thesis summary, key assumptions, supporting evidence with inline citations, bear case, decision/outcome log); every section cell references the claim IDs that populate it.
  - Inline citations: every numeric figure and quoted claim in the rendered memo carries a citation resolvable to the exact source passage in the document store.
  - Analyst workspace — memo view: analysts can read the draft, and accept, edit, or reject individual claims; the current memo state is always the result of the base extraction plus the ordered delta log; no edit overwrites a prior state.
  - Versioned delta audit log: every analyst accept/edit/reject and every PM annotation is appended to the audit log with actor identity, timestamp, and the prior and new values.
  - PM access: portfolio managers can open the final memo (after analyst marks it ready), read it, and add annotations that are logged.
  - Provenance UI — full lifecycle view: compliance can retrieve, for any memo, the complete record — source documents, gate decisions, LLM call records, claim extraction, memo versions, analyst edits, PM annotations — through structured search and browse, without engineering.
  - Cycle-time instrumentation: the system records submission timestamp and memo-ready timestamp; compliance and analysts can see elapsed time per submission in the Provenance UI.
  - End-to-end tests: a non-flagged submission produces a section-complete draft memo with all inline citations resolving to source passages; analyst edits appear in the audit log without overwriting prior state; PM annotations are logged; compliance can retrieve the full provenance chain for the memo; cycle time is recorded and visible.
- **Out of scope:**
  - Synchronous compliance approval in the normal pipeline (only MNPI flag triggers compliance in the active pipeline).
  - Richer RBAC beyond Analyst / PM / Compliance.
  - Natural-language querying in the Provenance UI.
  - Asset classes beyond equities.
  - Self-serve data-source connector onboarding.
  - Local/on-premises LLM hosting.
- **Depends on:** WO-001, WO-002.
- **Done when:**
  - An analyst can go from ticker and research question to a structured, section-complete draft memo in under one hour for a non-flagged submission; elapsed time is recorded and visible in the Provenance UI.
  - Every numeric figure and quoted claim in the memo has an inline citation that resolves to the exact source passage in the document store.
  - Analyst accept/edit/reject actions are in the audit log as versioned deltas; reading back the delta sequence reproduces the current memo state; no prior state is lost.
  - A portfolio manager can open the analyst-ready memo, read it, and add an annotation; the annotation appears in the audit log.
  - Compliance opens the Provenance UI and retrieves the full provenance record for any memo — sources, gate decisions, model interactions, claim extraction, memo versions, analyst edits, PM annotations — without engineering help.
  - The PM self-reports their time shifting toward judgment and away from assembly (qualitative sign-off collected at phase end).
- **Complexity:** L. **Risk:** Medium.

---

## Deferred
- **Local / on-premises LLM hosting:** Not built in V1. Contingent on D-001 and D-004 determining that certain content categories require a locally-hosted model. The extraction engine's model-call interface is designed to accommodate this if triggered.
- **Asset classes beyond long/short equities:** Memo template, data-source integrations, and claim taxonomy are scoped to equities. Expansion awaits D-003.
- **Synchronous compliance approval in the normal pipeline:** Compliance enters the active pipeline only at an MNPI flag. A richer real-time approval workflow is deferred to preserve sub-one-hour cycle time.
- **Self-serve data-source onboarding:** Analysts cannot add new licensed data connectors without an engineer. Intentional control; not a gap.
- **RBAC beyond three roles:** Multi-user permission models beyond Analyst / PM / Compliance are excluded from V1.
- **Natural-language querying in the Provenance UI:** Compliance uses structured search and browse. Conversational / NL query interface is deferred; not needed to meet the stated compliance goal.

---

## Assumptions
- D-001 (MNPI detection policy) and D-012 (identity and authentication) are resolved by compliance before WO-001 build begins; WO-001 cannot be completed without them.
- D-004 (approved LLM provider) and D-007 (model ID) are resolved before WO-002 build begins; the extraction engine has no implementation without them.
- D-002 (retention policy) and D-006 (citation-integrity storage) are resolved before WO-003 is promoted to production; the audit log and document store can be built to accommodate likely options, but production deployment requires these to be locked.
- Licensed API access to SEC EDGAR, at least one earnings-call transcript provider, and at least one fundamental data feed is active or will be secured before WO-001 begins.
- The compliance officer and at least one analyst are available for review and feedback at the end of each Work Order; their sign-off per D-015 gates the start of the next Work Order.
- The part-time engineer is available for continuous (if part-time) work across all three Work Orders; a gap or change in engineering availability would re-sequence the plan.
- The MNPI gate's heuristic will achieve a manageable false-positive rate after calibration with compliance during WO-001; an unacceptably high rate extends WO-001 until the rate is acceptable.
- Earnings call transcripts are available in machine-readable text from the licensed provider; audio transcription is not required.
- The expected memo volume (low tens per week) does not require horizontal scaling; a single controlled deployment environment is sufficient throughout V1.
- D-005 (canonical memo template) is assumed as: thesis summary, key assumptions, supporting evidence with citations, bear case, and decision/outcome log. This is a reversible default; analysts refine drafts against this structure and it can be adjusted without architectural change.
- D-013 (claim serialization format) is assumed as: JSON with fields source_doc_id, passage_offset, verbatim_quote, claim_type, extracted_value, timestamp. Human-readable, tool-portable, and sufficient for expected volume.
- D-014 (content-hashing algorithm) is assumed as: SHA-256. Ubiquitous, collision-resistant, and supported by all candidate object stores.

---

## Decision List

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | How is MNPI detected before content is sent to any third-party model, and what happens when a flag is triggered? | Compliance | Compliance | Open | WO-001 | High blast radius: getting this wrong creates regulatory exposure and potential legal liability. The detection heuristic, the containment action (block, quarantine, route to local model), and the review workflow must all be defined before any external model integration is built. Cannot be assumed or deferred. |
| D-002 | What is the retention policy for memos and their source document snapshots? | Compliance / Legal | Compliance | Open | WO-003 (production deployment) | Retention period, storage jurisdiction, deletion triggers, and legal-hold procedures carry regulatory and data-safety implications. Irreversible if data is deleted prematurely or stored in violation of policy. Must be decided before storage architecture is finalized. |
| D-003 | Should V1 support asset classes beyond long/short equities (e.g., credit, macro)? | Product | Product | Open | — | Expands scope and target users if yes; changes the memo template model, data source requirements, and potentially the user base. High blast radius on scope — cannot be assumed away with a default without explicit product sign-off. |
| D-004 | Which third-party LLM provider(s), if any, are approved for use given the MNPI constraint? | Architect / Compliance | Technical | Open | WO-002 | Depends on resolution of D-001. Provider selection determines data processing agreements, model isolation options, and feasibility of on-premises or private deployment for sensitive content. Cannot be decided until MNPI control policy is established. |
| D-005 | What is the canonical memo template structure for V1? | Product | Product | Assumed | — | Low blast radius and fully reversible through iteration. Default: a structured template covering thesis summary, key assumptions, supporting evidence (with citations), bear case, and decision/outcome log. Analysts refine drafts against this structure. Can be adjusted without architectural change. |
| D-006 | How are source document snapshots stored to support long-term citation integrity (i.e., source content does not mutate after ingestion)? | Architect | Technical | Deferred | — | Important for audit trail durability but does not block initial scoping. Needs resolution before production deployment; the constraint is known and the options (immutable object store, content-addressed storage) are low-controversy once MNPI storage policy is settled via D-002. |
| D-007 | Which specific LLM model ID will be used by the Extraction Engine? | Architect | Technical | Open | WO-002 | Blocked on D-004 (provider selection) and D-001 (MNPI policy). Once provider is approved, a default model ID will be selected and recorded as Assumed. Cannot be assumed before the provider is known. |
| D-008 | What technology implements the Audit Log (append-only structured store queryable by compliance without engineering)? | Architect | Technical | Deferred | — | Real but non-blocking at this stage. The requirement is clear (append-only, structured, compliance-queryable). Options include a managed database with a read-only compliance role and a simple UI, or a dedicated log store. Reversible choice; can be decided when provider landscape (D-004) and retention policy (D-002) are clearer. One part-time engineer constraint favors a managed service over a custom solution. |
| D-009 | What technology implements the Document Store (immutable, content-addressed object storage)? | Architect | Technical | Deferred | — | Blocked in practice on D-002 (retention and jurisdiction policy). Options include a managed object store with object-lock enabled. Reversible and low-controversy; deferred until retention policy is settled. |
| D-010 | What web application framework implements the Analyst Workspace and Provenance UI? | Architect | Technical | Deferred | — | Real but non-blocking. Choice is reversible and should be sized to what the one part-time engineer is most productive with. No framework is mandated by the Vision. |
| D-011 | What mechanism implements the Orchestrator (pipeline sequencing, retry, status)? | Architect | Technical | Deferred | — | Real but non-blocking. Options range from a simple task queue to a lightweight workflow library. Should be the simplest option that handles retry and pause-on-MNPI-flag reliably, consistent with one part-time engineer operational burden. |
| D-012 | How are analyst and compliance user identities managed and authenticated? | Architect / Compliance | Technical / Compliance | Open | WO-001 | Authentication and access control have compliance and data-safety implications (who can read MNPI-flagged quarantine records, who can clear flags). Cannot be assumed; requires explicit decision with compliance input. Blast radius: incorrect access control could expose quarantined content to unauthorized users. Must be resolved before WO-001 is complete. |
| D-013 | What serialization format is used for claims produced by the Extraction Engine and stored in the Audit Log? | Architect | Technical | Assumed | — | Reversible parameter of the Audit Log and Extraction Engine components. Default: JSON with a defined schema (source_doc_id, passage_offset, verbatim_quote, claim_type, extracted_value, timestamp). Human-readable, tool-portable, and sufficient for the expected memo volume. Override-able without architectural change. |
| D-014 | What content-hashing algorithm is used for Document Store content-addressing? | Architect | Technical | Assumed | — | Reversible parameter with no material blast radius. Default: SHA-256. Ubiquitous, collision-resistant, and supported by all candidate object stores. Override-able if a storage provider mandates a different scheme. |
| D-015 | At what phase boundary does compliance formally sign off before the next Work Order begins? | Product / Compliance | Operational | Open | WO-001 → WO-002 transition; WO-002 → WO-003 transition | Compliance sign-off at the end of WO-001 (gate behavior validated) and WO-002 (extraction and citation chain validated) is assumed in the sequencing, but the formal sign-off criteria and who has authority to grant it have not been defined. Incorrect sequencing here could mean production deployment proceeds before compliance is satisfied with the audit chain. Must be agreed before WO-001 begins. |
| D-016 | Will WO-001 be deployed in a production-equivalent environment or a controlled staging environment? | Architect / Compliance | Operational | Open | WO-001 | Real documents (potentially containing sensitive financial content) will be ingested and MNPI-screened during WO-001. Whether this happens in a production environment with full data controls or a sandboxed staging environment with synthetic or anonymized data has compliance and data-safety implications. Cannot be assumed; must be decided with compliance before WO-001 ingests live documents. |
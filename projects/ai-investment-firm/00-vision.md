# Vision — ai-investment-firm

## Problem

A small discretionary equity investment team loses a disproportionate share of its analytical week to mechanical work: pulling SEC filings, transcribing earnings calls, reconciling figures across spreadsheets, and writing the same memo scaffolding repeatedly. By the time a polished investment thesis reaches the portfolio manager, the informational edge that motivated the idea has often narrowed or vanished. The problem is not the quality of the team's judgment — it is the time tax that mechanical assembly places on that judgment.

Compounding the speed problem is an auditability problem. There is no consistent, machine-readable trail connecting raw source material to the claims in a memo to the final allocation decision. When a position goes wrong, the team cannot reliably reconstruct what they believed, what evidence supported it, and what assumptions proved incorrect. This hampers learning, weakens compliance posture, and makes post-mortems guesswork.

## Users

**Primary — Portfolio Manager** at a sub-$200M long/short equity fund. Makes all final allocation decisions and is accountable to investors and compliance. Needs decision-ready, sourced material quickly and needs to trust that every figure in a memo can be traced to its origin.

**Secondary — Junior Analysts (one or two)** who conduct primary research, pull source documents, and draft investment memos for the PM to review. They are the system's main day-to-day operators and the primary beneficiaries of time saved on mechanical data-gathering.

## Goals

- Compress the cycle from "new ticker and a question" to "decision-ready draft memo" from days to hours, preserving analytical edge while it still exists.
- Produce a consistent, auditable chain from source documents through extracted claims to the investment thesis, so any position's original reasoning is permanently retrievable.
- Shift analyst time from mechanical assembly to judgment, interpretation, and challenge of the AI-drafted material.
- Give compliance the ability to inspect the full provenance of any memo — who produced it, from which sources, at which point in time — without engineering involvement.

## Non-Goals

- Not an automated or algorithmic trading system; the product does not place orders, generate signals for execution, or move capital in any form.
- Not a robo-advisor or any product directed at retail investors.
- Not a substitute for the portfolio manager's judgment; the system surfaces and organizes evidence, it does not make allocation decisions.
- Not a market-data terminal or data redistributor; it consumes licensed data feeds under their existing terms and does not repackage or resell them.

## Constraints

- **Full audit trail required:** every factual claim or figure in a generated memo must be traceable to a specific source document and passage. This is non-negotiable.
- **Regulatory:** all outputs are internal research only, not published investment advice. Compliance must be able to review the provenance of any memo without engineering help.
- **MNPI handling:** material non-public information must not be transmitted to third-party systems (including external LLM APIs) without explicit prior review and approval. A control mechanism for MNPI detection and containment is required before any third-party model call is made with potentially sensitive content.
- **Data licensing:** all ingested data sources are licensed; every usage pattern must conform to the per-source license terms. No derived redistribution.
- **Team size:** at most one part-time engineer available to build and maintain the system. Architecture and operational burden must be proportionate to this constraint.

## Success Criteria

- An analyst can go from a ticker and a research question to a structured, sourced draft memo in under one hour.
- Every numeric figure or quoted claim in a memo carries a citation linking to the exact source document from which it was extracted.
- Compliance can retrieve the full provenance of any memo — sources, extraction timestamps, model interactions — without requiring an engineer to run queries or reconstruct logs.
- The portfolio manager self-reports a meaningful shift of their time toward judgment and away from assembly and reconciliation.

## Assumptions

- Licensed API access to SEC filings, earnings call transcripts, and price/fundamental data is already in place or will be secured before build begins.
- Analysts will treat AI-drafted memos as a starting point requiring their review, correction, and judgment — not as finished work product to be shipped raw.
- A standardized memo structure covers the large majority of equity long/short theses the team produces, making templating tractable.

## Decision List

| ID | Decision | Owner | Type | Status | Blocks | Rationale |
|----|----------|-------|------|--------|--------|-----------|
| D-001 | How is MNPI detected before content is sent to any third-party model, and what happens when a flag is triggered? | Compliance | Compliance | Open | — | High blast radius: getting this wrong creates regulatory exposure and potential legal liability. The detection heuristic, the containment action (block, quarantine, route to local model), and the review workflow must all be defined before any external model integration is built. Cannot be assumed or deferred. |
| D-002 | What is the retention policy for memos and their source document snapshots? | Compliance / Legal | Compliance | Open | — | Retention period, storage jurisdiction, deletion triggers, and legal-hold procedures carry regulatory and data-safety implications. Irreversible if data is deleted prematurely or stored in violation of policy. Must be decided before storage architecture is finalized. |
| D-003 | Should V1 support asset classes beyond long/short equities (e.g., credit, macro)? | Product | Product | Open | — | Expands scope and target users if yes; changes the memo template model, data source requirements, and potentially the user base. High blast radius on scope — cannot be assumed away with a default without explicit product sign-off. |
| D-004 | Which third-party LLM provider(s), if any, are approved for use given the MNPI constraint? | Architect / Compliance | Technical | Open | D-001 | Depends on resolution of D-001. Provider selection determines data processing agreements, model isolation options, and feasibility of on-premises or private deployment for sensitive content. Cannot be decided until MNPI control policy is established. |
| D-005 | What is the canonical memo template structure for V1? | Product | Product | Assumed | — | Low blast radius and fully reversible through iteration. Default: a structured template covering thesis summary, key assumptions, supporting evidence (with citations), bear case, and decision/outcome log. Analysts refine drafts against this structure. Can be adjusted without architectural change. |
| D-006 | How are source document snapshots stored to support long-term citation integrity (i.e., source content does not mutate after ingestion)? | Architect | Technical | Deferred | — | Important for audit trail durability but does not block initial scoping. Needs resolution before production deployment; the constraint is known and the options (immutable object store, content-addressed storage) are low-controversy once MNPI storage policy is settled via D-002. |
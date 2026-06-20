# Product Input — ai-investment-firm

## Problem
A small discretionary investment team spends most of its week on manual work:
pulling filings, transcribing earnings calls, reconciling numbers across
spreadsheets, and writing the same memo structure over and over. By the time a
thesis is written, the edge has often decayed. There is no consistent, auditable
trail from raw source material to the investment decision, so when a position
goes wrong the team cannot reconstruct what they believed and why.

## Users
Primary: a portfolio manager at a sub-$200M long/short equity fund who makes the
final allocation decisions and is accountable to investors.
Secondary: one or two junior analysts who do primary research and draft memos
for the PM to review.

## Goals
- Cut the time from "new idea" to "decision-ready memo" from days to hours.
- Produce a consistent, auditable trail from source documents to thesis to
  decision.
- Free analysts from mechanical data-gathering so they spend time on judgment.
- Make every position's original thesis and assumptions retrievable later.

## Non-Goals
- Not an automated trading system: it does not place orders or move capital.
- Not a robo-advisor for retail investors.
- Not a replacement for the PM's judgment — it informs decisions, it does not
  make them.
- Not a market-data terminal; it consumes data, it does not redistribute it.

## Constraints
- Must keep a full audit trail: every claim traceable to a source document.
- Regulatory: outputs are internal research, not published advice; compliance
  must be able to review any memo's provenance.
- Cannot store material non-public information in third-party systems without
  review.
- Small team: at most one engineer maintaining it part-time.
- Data sources are licensed; usage must respect per-source license terms.

## Success Criteria
- An analyst goes from a ticker and a question to a structured, sourced draft
  memo in under an hour.
- Every figure in a memo links back to the document it came from.
- Compliance can audit the provenance of any memo without engineering help.
- The PM reports spending more time on judgment and less on assembly.

## Assumptions
- Licensed access to filings, transcripts, and price data is available via API.
- Analysts will review and correct AI-drafted memos rather than ship them raw.
- A memo structure can be standardized across most equity theses.

## Open Questions
- How is material non-public information detected and kept out of third-party
  model calls?
- What is the retention policy for memos and their source snapshots?
- Should the system support asset classes beyond equities (credit, macro), or
  stay equity-only for V1?

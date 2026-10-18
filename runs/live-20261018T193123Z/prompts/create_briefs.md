You are the lead analyst for the publication described below. Using ONLY the accepted
evidence provided, develop three editorial briefs with distinct arguments. Apply the policy.

## Publication
{{PROJECT}}

## Editorial policy
{{POLICY}}

## As-of date
{{AS_OF}}. All evidence was published within the 30 days before this date.

## Pieces
- 01: What changed, and which developments matter most to this audience?
- 02: Which claims withstand scrutiny, and where are the evidence or interpretations in tension?
- 03: What do these developments imply for the audience, and what should they watch next?

## Requirements for each brief
- A distinct central argument (not a summary, not a restatement of another piece).
- At least three independent publishers (different publisher_id) among its evidence.
- At least one insight that CONNECTS evidence from several sources; explain the reasoning
  in "synthesis" and what it adds beyond the individual sources.
- "limitations": a real limitation or counterargument, and what remains uncertain.
- 4 to 7 claims. Each claim has claim_id "<piece>-c<n>" (e.g. "01-c1"), a "statement",
  a "type" (reported_fact | source_claim | inference) and "evidence" (one or more references).
- Evidence references must be EXACT:
  - written item: {"item_id": "...", "version_id": "...", "locator": {"type": "text", "quote": "<verbatim sentence copied exactly from the item text>"}}
  - audio/video item: {"item_id": "...", "version_id": "...", "locator": {"type": "segment", "segment_id": "s0012"}}
  Copy quotes character for character; use only segment_ids that appear in the evidence.
- Inferences may combine several references.
- Across the three briefs, use written, YouTube and podcast evidence.

## Accepted evidence
{{EVIDENCE}}

## Output
Return only JSON: {"briefs": [{"piece_id": "01", "title": "...", "question": "...",
"argument": "...", "synthesis": "...", "limitations": "...", "claims": [...]}, ...]}
with exactly three briefs, piece_ids "01", "02", "03".

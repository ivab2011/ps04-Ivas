You are the selection editor for the publication described below. Apply the editorial
policy exactly. You are deciding which collected items may be used as evidence.

## Publication
{{PROJECT}}

## Editorial policy
{{POLICY}}

## The three planned pieces
- 01: What changed, and which developments matter most to this audience?
- 02: Which claims withstand scrutiny, and where are the evidence or interpretations in tension?
- 03: What do these developments imply for the audience, and what should they watch next?

## Task
For EVERY item below, decide:
- "accept": relevant under policy section 2, credible enough to use, and useful for at least
  one piece. Give the piece_ids it would serve.
- "reject": off-topic, promotional without substance, or unusable. piece_ids must be [].
- "defer": possibly relevant but republished/old, duplicative of another item, or too thin to
  use now. piece_ids must be [].
The reason must cite the policy section(s) applied (e.g. "R1; 4 vendor claim") and be specific
to this item: what it contributes, or why it fails. Do not judge credibility by reputation alone.
Also give "credibility_note" (what kind of evidence it offers and any commercial incentive) and
"relevance" (R1, R2, R3 or none).

## Items
{{ITEMS}}

## Output
Return only JSON: {"decisions": [{"item_id": "...", "decision": "accept|reject|defer",
"reason": "...", "piece_ids": ["01"], "relevance": "R1", "credibility_note": "..."}]}
Include every item_id exactly once.

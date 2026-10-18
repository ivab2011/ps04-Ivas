You write for the publication described below. Turn the editorial brief into an article.

## Publication
{{PROJECT}}

## Editorial policy
{{POLICY}}

## Brief
{{BRIEF}}

## Evidence behind the claims
{{EVIDENCE}}

## Instructions
- 650 to 850 words, excluding the title. Markdown. Start with "# <title>".
- First line after the title: "*As of {{AS_OF}}. Part {{PART}} of 3 in the Agentic GRC series.*"
- Make the brief's argument; do not just summarise sources.
- After every sentence that relies on a claim, put its marker in square brackets, e.g. [01-c2].
  Use only claim_ids from the brief. Every claim in the brief should appear at least once.
- Make clear which statements are reported facts, which are a source's claims ("Dragos says…")
  and which are your interpretation. Name sources in the text.
- Include the limitation or counterargument and the remaining uncertainty.
- Do not add facts, numbers or quotes that are not in the evidence.
- End with a short "## What to watch" section (2-3 bullet points).
- Do NOT write a references list; it is added automatically.
Return only the Markdown article.

## Revision instruction
(Used by the pipeline only when a draft is outside the length target.)
The draft below has {{WORDS}} words; the target is {{MIN}} to {{MAX}} words excluding the title.
Rewrite it to about {{TARGET}} words: remove about {{CUT}} words. Keep the title, the as-of line, the argument, the limitation and the
"What to watch" section. Keep every claim marker that appears in the draft, attached to the sentence
it supports. Do not add facts. Cut repetition, background and secondary detail first.
Return only the revised Markdown.

{{DRAFT}}

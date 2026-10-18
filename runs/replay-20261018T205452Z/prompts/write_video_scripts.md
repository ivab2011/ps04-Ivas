You write narration for a short explainer video for the publication described below.
The video presents the same argument as the article, from the same brief and evidence.

## Publication
{{PROJECT}}

## Editorial policy
{{POLICY}}

## Brief
{{BRIEF}}

## Evidence behind the claims
{{EVIDENCE}}

## Instructions
- 450 to 650 spoken words (about 3 to 5 minutes). Markdown. Start with "# <title>".
- Structure: hook (one question), 3 to 4 short sections, closing "what to watch".
- Write for the ear: short sentences, no bullet lists inside narration, no abbreviations
  without explaining them once.
- Before each section put a visual direction line: "[VISUAL: ...]" describing a simple slide
  (a heading, a key number or a short quote, the source name).
- After a sentence that relies on a claim, put its marker, e.g. [02-c3]. Use only claim_ids
  from the brief and keep facts identical to the brief. Say the source name aloud.
- Say clearly when something is a company's claim or your interpretation.
- Final line of narration: "This video was narrated with AI text-to-speech. Sources are in the description."
- Do NOT write a source list; it is added automatically.
Return only the Markdown script.

## Revision instruction
(Used by the pipeline only when a script is outside the length target.)
The script below has {{WORDS}} spoken words; the target is {{MIN}} to {{MAX}} words (3 to 5 minutes).
Rewrite it to about {{TARGET}} words: remove about {{CUT}} words. Keep the hook, the [VISUAL: ...] lines, the closing "what to watch" and the
final AI-narration sentence. Keep every claim marker that appears in the script, attached to the sentence
it supports. Do not add facts. Cut repetition and secondary detail first.
Return only the revised Markdown.

{{DRAFT}}

# Editorial review sample: live run 1 (live-20261018T193123Z, as of 2026-10-18)

Reviewer: Iva Biscanic. Policy in force: editorial_policy.md version 1.
Sample: 3 accepted and 3 rejected/deferred items. AI reasons are in runs/live-20261018T193123Z/decisions.jsonl;
the full prompts and responses are in runs/live-20261018T193123Z/llm_calls/.

| # | Item | AI decision | My judgment | Agree? |
|---|------|-------------|-------------|--------|
| 1 | Industrial Cyber: Singapore prioritizes critical infrastructure in quantum-safe push | accept (labelled R3, AI data centres) | The article does not mention AI (checked: 0 mentions in the retained text), so the R3 label is wrong. It is still useful: it shows how a regulator turns a future technology risk into concrete requirements (exposure assessment, migration planning, deadlines, verifiable readiness criteria) for critical infrastructure. That is a model for an AI policy framework, usable as an analogy, not as evidence about AI. | Agree with accept, disagree with the label |
| 2 | Dragos: xOT Defense Lab Episode 1 (passive monitoring of OT networks) | accept (R1). The same video was **rejected** as vendor promotion in a test call earlier the same day, with the same policy. | **Human correction: reject.** After watching it: it is primarily a vendor presenting its own platform, and AI is not mentioned anywhere (checked: 0 mentions in the transcript). Policy v1 already excluded product promotion; the model did not apply its own policy consistently. | Disagree |
| 3 | Utility Dive: Reliability standards for AI data centers, crypto miners move… | accept (R3) | Shows that AI governance includes the physical infrastructure that enables it, especially the effect of large computing loads on grid reliability. Justifies including infrastructure dependencies, service continuity and sector requirements in an AI readiness assessment. | Agree |
| 4 | Atlantic Council: What Ukraine's Starlink disruptions reveal about military commercial dependencies | reject | Primarily about military dependence on commercial communication services; its link to AI agent readiness in critical infrastructure is indirect, and defence is excluded by policy section 2. | Agree |
| 5 | Lawfare: The New Command Economy | defer: "No valid decision returned by the model; needs human review." | Not an editorial decision: the model returned the ID without its "podcast:" prefix, so the pipeline could not match it. **Human decision: reject.** It discusses the state's growing role in company operations, national security and accountability: broader technology-policy context, not operational readiness for AI agents. | Human correction (AI made no decision) |
| 6 | Lawfare Archive episodes (2) | defer: same ID problem | Policy v1 section 3 defers republished material. Archive episodes are poorly suited to tracking new regulatory change because a new publication date does not mean updated content. They passed the 30-day filter because the feed shows the republication date: only the editorial layer can catch this. | Agree with defer, reached for the wrong reason |

## Findings
1. **Inconsistent application of the policy.** The model accepted a vendor platform walkthrough with no AI content (item 2) that policy v1 already excluded, after rejecting the same video in an earlier call. Selection reasons are decisions to inspect, not proof of relevance.
2. **Category stretching.** When an item fits no category, the model stretches one (item 1 labelled "AI data centres"). The policy must say: reject rather than stretch, and name the one non-AI category I do want.
3. **Pipeline failure.** The model altered three IDs. Fixed: IDs are repaired only when unambiguous (recorded as id_repaired_from), missing decisions get one retry, and anything still missing is deferred for human review.
4. **Verification method.** I checked AI relevance against the retained text (keyword search plus watching the video), not against titles.

## Policy revision (v1 to v2)
See config/editorial_policy.md "Change log": stricter vendor rule (own-platform walkthroughs are promotional),
an explicit R4 for governance precedents with a guardrail, a rule against stretching categories, and a concrete
republication rule. The series stages were rerun on the same evidence (runs/replay-…) to compare decisions and
synthesis: see docs/policy_revision.md.

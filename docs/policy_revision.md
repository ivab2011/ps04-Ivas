# Policy revision: v1 to v2

## Why
The review of live run 1 (docs/review_run1.md) found that the selection model (gpt-5.4-mini):
- accepted a Dragos vendor platform walkthrough with no AI content, which v1 already excluded as promotion,
  after rejecting the same video in an earlier call with the same policy;
- stretched categories to fit non-AI items (Singapore quantum-safe mandate labelled "AI data centres");
- returned three Lawfare IDs without their "podcast:" prefix, so those items received no decision.

## What changed in the policy (config/editorial_policy.md, Change log)
- R1-R3 now require explicit AI content; new R4 for governance precedents (non-AI regulatory examples),
  usable only as a labelled analogy, never as sole evidence about AI.
- Vendor rule: a vendor presenting its own platform or product series is promotional and rejected,
  unless it reports specific, checkable results about AI in operations.
- "Do not stretch a category"; military dependencies and industrial-policy debates added to the reject list.
- Concrete republication signals ("Archive", "Rewind", "Encore", "Rebroadcast").
Code fix (not policy): altered IDs are repaired only when unambiguous, missing decisions get one retry.

## Rerun on the same evidence
- runs/live-20261018T193123Z: policy v1 (11 accept, 27 reject, 3 defer)
- runs/replay-20261018T203841Z: policy v2, no human overrides (11 accept, 30 reject)
- runs/replay-20261018T205452Z: policy v2 + human overrides (11 accept, 26 reject, 4 defer). This is the approved run.

### Decisions that changed from v1 to v2 (model only)
| Item | v1 | v2 | Assessment |
|------|----|----|------------|
| Dragos: xOT Defense Lab Episode 1 | accept | reject | Intended effect of the vendor rule |
| Dragos: Introduction to xOT Defense Lab | accept | reject | Intended effect of the vendor rule |
| IBM: Context Engineering for AI Agents: 4 Failure Modes | reject | accept | Educational content about AI agents; consistent with v2 |
| Lawfare: The New Command Economy | defer (ID error) | reject | Correct; ID repair worked |
| Lawfare Archive x2 | defer (ID error) | reject | Policy says defer: model error |
| Atlantic Council: Starlink disruptions | reject | accept | Model ignored the explicit v2 rule on military dependencies |
| Atlantic Council: Ukrainian drone strikes on Russia's data centers | reject | accept | Military story; model stretched R3 |
| CSIS: OpenAI Agents Hack Australian Government | accept | reject | Central agentic-AI incident; model swung the other way |

### Human overrides (config/editorial_overrides.json)
The revision fixed the targeted errors but the model introduced new ones. Five items were therefore decided
by the editor: Starlink and drone strikes rejected, the OpenAI agents incident accepted (R1), both Lawfare
Archive episodes deferred. The decision records keep the model's own decision and reason next to the human one
(decided_by, model_decision, model_reason).

## What I learned
A clearer policy corrects specific, foreseeable errors, but it does not make an LLM selector consistent:
the same item can flip between runs. Human review must be part of the system, not an afterthought. Here
that means an overrides file that every later run applies automatically, with both decisions visible.

## Effect on the synthesis (brief titles)

| Piece | v1 (live-20261018T193123Z) | v2 + overrides (replay-20261018T205452Z) |
|-------|----|----|
| 01 | The governance perimeter moved: from AI policies to operational obligations | AI governance has moved from policy debate to control evidence |
| 02 | The evidence supports narrower AI risks than the loudest claims suggest | The real risk is not magic autonomy; it is unmanaged agency at scale |
| 03 | What leaders should do next: assign ownership before autonomy expands | What operators should do next: make AI governable before it becomes operationally normal |

Piece 01 moved beyond describing how the scope of governance is changing to asking what evidence operators need to show that their controls actually work. 
Piece 02 changed the most. Rather than arguing that the risks are “narrower than the loudest claims suggest,” it now focuses on what happens when AI agents operate at scale without adequate oversight. 
It shows on the OpenAI agents incident, which I included through a manual override.
Also, included IBM’s discussion of agent failure modes. 
Both sources were accepted only in v2, while the Dragos vendor videos no longer shape the argument. 
Piece 03 moved from asking who is responsible to asking how we make AI governable before its use becomes routine

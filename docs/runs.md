# Repeatability: what changed between runs

Full numbers for every run: [run_table.md](run_table.md) (generated from each run's run.json and summary.json).

## Live run 1: `runs/live-20261018T193123Z` (as of 2026-10-18)
First collection: 42 items from 8 sources and 7 independent publishers, all new. 41 eligible; 1 excluded as
`outside_window` (a Dragos video published 2026-08-14). Policy v1. Whisper was needed for every podcast episode (cost in run_table.md).

## Live run 2: `runs/live-20261019T140450Z` (as of 2026-10-19, a different day)
- **New material:** 12 new items.
- **Changed material:** 1 item, Atlantic Council "Saudi Arabia has more security partners than ever…". Its content
  changed after first collection, so the store saved a new version and kept the old one (both retrievable with
  `bash data/store.sh get ITEM_ID VERSION_ID`). It was rejected in both runs (geopolitics), so it had no
  editorial consequence.
- **Unchanged:** 29 items were recognized and not duplicated; **15 transcripts were reused** from the store, so
  Whisper ran only on new episodes ($0.87, compared with run 1 in run_table.md).
- **Window re-check:** 53 items eligible. Items stored by run 1 were checked again against the new window
  (2026-09-20 to 2026-10-19), as the architecture requires.
- **Editorial effect of the new material:** among the new items the model accepted "Need for enforceable AI
  accountability, zero-trust security…" (Industrial Cyber), "AI in nuclear operations: the shift from adoption to
  operation" (Utility Dive) and "What Is Loop Engineering? Building Better AI Agents" (IBM). The briefs changed
  accordingly; most visibly, piece 03 became a concrete recommendation: "Build an agent-access register before
  the rules harden".
- **My review of three questionable acceptances in run 2:**
  - Claroty Team82, "AI can rebuild Danfoss controller exploit": **accept** (agree with the model, R1). Researchers used an AI coding agent to reproduce known vulnerabilities in refrigeration controllers in about 28 minutes; it shows how AI accelerates security research and lowers the cost of attacks, while the article also states the limits (no new flaws found, human guidance still needed). Vendor research reported by trade press, so used as a source claim.
  - Unit 42, "Peerstitch malware / FortiOS vulnerability": **reject** (human correction; the model accepted it as R2). It describes attackers compromising a central management platform, stealing data and deploying malware: a cybersecurity story with no AI content (0 AI mentions in the retained text) and no regulatory precedent. Policy v2 requires explicit AI content for R1-R3 and forbids stretching a category; the model still did so after the revision, which confirms that human review stays necessary.
  - Nozomi, "IT and OT security priorities ahead of India…": **accept as R4** (label corrected; the model said R2). It sets out preparations for India's April 2027 power-sector cybersecurity deadline (CEA): a regulator turning a technology risk into concrete operator and vendor obligations. Not AI-focused, but useful context and a governance precedent for AI tools in critical infrastructure, consistent with my decision on the Singapore quantum-safe item. Framed through a vendor (Nozomi), so used only as a labelled analogy.
- Run 2's drafts were not published: the published series comes from the approved replay of run 1 (below);
  run 2 demonstrates how the system responds to new information.

## Labelled simulated failure: `runs/live-20261019T143701Z` (as of 2026-10-19)
Started with `SIMULATE_FAIL_SOURCE=atlanticcouncil`, which makes that one source raise
"SIMULATED FAILURE (deliberate test)". The run records `simulated_failure` in run.json and summary.json, the
fetch_feeds receipt has status `incomplete` with the error, `collection_status.json` says `complete: false`, and
the run **continued** with the other 7 sources and still produced checked drafts.
Atlantic Council items stored in earlier runs remained eligible: the failure blocks discovery of *new*
material from that source, which the summary reports as incomplete coverage.

## Replay without duplicates
The simulated-failure run, collected minutes after run 2, is also the replay test: 34 items discovered,
**0 new, 0 changed, 34 unchanged**, 18 transcripts reused, Whisper cost $0. No duplicate records or versions
were created and no media was re-processed. The store's version logic is also covered by the official
fixtures (`examples/items.jsonl` + `examples/replay_items.jsonl`: 3 new; then 4 unchanged + 1 changed).

## Policy replays (same evidence, new policy)
- `runs/replay-20261018T203841Z`: policy v2, no human overrides.
- `runs/replay-20261018T205452Z`: policy v2 + human overrides. **Approved and published.**
See [policy_revision.md](policy_revision.md).

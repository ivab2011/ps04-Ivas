"""Build reader-facing source notes from brief claims (used by content generators and packaging).
References are produced by code from the brief's evidence, never by the model."""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
import evidence

LABEL = {"reported_fact": "Reported fact", "source_claim": "Source claim", "inference": "Our interpretation"}


def get_item(item_id, version_id):
    """Fetch the exact evidence version through the store interface."""
    r = subprocess.run(["bash", "data/store.sh", "get", item_id, version_id], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else None


def evidence_for_prompt(brief):
    """Show the model the passages behind each claim (quote or transcript segment)."""
    out = []
    for c in brief["claims"]:
        for ref in c.get("evidence", []):
            item = get_item(ref["item_id"], ref["version_id"])
            if not item:
                continue
            loc = ref.get("locator", {})
            if loc.get("type") == "segment":
                segs = evidence.load_segments(item) or []
                seg = next((s for s in segs if s["segment_id"] == loc.get("segment_id")), None)
                passage = f"[{loc.get('segment_id')} at {evidence.clock(seg['start_seconds'])}] {seg['text']}" if seg else "(segment not found)"
            else:
                passage = f"\"{loc.get('quote', '')}\""
            out.append(f"{c['claim_id']} | {item['publisher_id']} | {item['kind']} | \"{item['title']}\" "
                       f"({(item['published_at'] or '')[:10]})\n{passage}")
    return "\n\n".join(out)


def source_notes(brief, heading="## Sources"):
    lines = [heading, ""]
    for c in brief["claims"]:
        refs = []
        for ref in c.get("evidence", []):
            item = get_item(ref["item_id"], ref["version_id"])
            if not item:
                refs.append(f"(unresolved evidence {ref.get('item_id')})")
                continue
            link, at = evidence.reference_link(item, ref.get("locator", {}), evidence.load_segments(item))
            when = f", at {at}" if at else ""
            refs.append(f"{item['publisher_id']}, \"{item['title']}\" ({(item['published_at'] or 'undated')[:10]}{when}): {link}")
        lines.append(f"- **[{c['claim_id']}]** {LABEL.get(c.get('type'), c.get('type'))}: {c['statement']}  ")
        for r in refs:
            lines.append(f"  {r}  ")
    return "\n".join(lines) + "\n"

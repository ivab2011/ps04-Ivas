"""Shared helpers for formatting retained evidence for prompts and for building references."""
import json


def load_text(item):
    with open(item["text_path"], encoding="utf-8") as f:
        return f.read()


def load_segments(item):
    if not item.get("segments_path"):
        return None
    with open(item["segments_path"], encoding="utf-8") as f:
        return json.load(f)


def clock(seconds):
    s = int(seconds)
    return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60}:{s % 60:02d}"


def header(item, sources=None):
    persp = ""
    if sources:
        persp = next((s.get("perspective", "") for s in sources if s["source_id"] == item["source_id"]), "")
    return (f"item_id: {item['item_id']}\nversion_id: {item['version_id']}\nkind: {item['kind']}\n"
            f"publisher_id: {item['publisher_id']} ({persp})\ntitle: {item['title']}\n"
            f"published_at: {item['published_at']}\nurl: {item['url']}")


def body(item, max_words):
    """Article text, or transcript lines '[s0012 12:34] text', cut to about max_words."""
    segs = load_segments(item)
    out, words = [], 0
    if segs:
        for s in segs:
            line = f"[{s['segment_id']} {clock(s['start_seconds'])}] {s['text']}"
            words += len(line.split())
            if words > max_words:
                out.append("[... transcript truncated ...]")
                break
            out.append(line)
        return "\n".join(out)
    text = load_text(item).split()
    return " ".join(text[:max_words]) + (" [... truncated ...]" if len(text) > max_words else "")


def reference_link(item, locator, segments=None):
    """Reader-facing link: URL, with a timestamp for video/audio segments."""
    if locator.get("type") == "segment" and segments:
        seg = next((s for s in segments if s["segment_id"] == locator.get("segment_id")), None)
        if seg:
            t = int(seg["start_seconds"])
            if item["kind"] == "youtube":
                return f"{item['url']}&t={t}s", clock(t)
            return item["url"], clock(t)
    return item["url"], None

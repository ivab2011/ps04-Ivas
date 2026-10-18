"""Shared discovery helper for the three collectors (RSS 2.0 and Atom, standard library only).

Usage (called by collectors/fetch_*.sh):
    python3 collectors/collect.py KIND RUN_DIR
KIND is feed, youtube or podcast. Reads RUN_DIR/config/sources.json (the run's snapshot),
prints one candidate JSON record per line to stdout, diagnostics to stderr.
Exit 0 = all sources read; exit 1 = at least one source failed (partial results still printed).

Stable identities:
  feed:     feed:<source_id>:<sha256 of canonical article URL, first 16 chars>
  youtube:  youtube:<native video id>
  podcast:  podcast:<source_id>:<sha256 of episode guid (or audio URL), first 16 chars>
"""
import hashlib, json, os, re, sys, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode

KIND, RUN_DIR = sys.argv[1], sys.argv[2]
DEFAULT_MAX = {"feed": 8, "youtube": 4, "podcast": 3}   # newest N entries per source
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AgenticGRC-pipeline/1.0"
NS = {"atom": "http://www.w3.org/2005/Atom",
      "yt": "http://www.youtube.com/xml/schemas/2015",
      "media": "http://search.yahoo.com/mrss/"}


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def to_iso(value):
    """Convert an RSS (RFC 822) or Atom (ISO 8601) date to ISO 8601 UTC, or None."""
    if not value:
        return None
    value = value.strip()
    try:
        dt = parsedate_to_datetime(value)                       # RSS style
    except (TypeError, ValueError, IndexError):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))  # Atom style
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def canonical(url):
    """Drop tracking parameters and fragments so the same article keeps one identity."""
    p = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(p.query) if not k.lower().startswith(("utm_", "fbclid", "gclid"))]
    return urlunsplit((p.scheme, p.netloc.lower(), p.path, urlencode(query), ""))


def short_hash(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def text(el, path):
    found = el.find(path, NS)
    return found.text.strip() if found is not None and found.text else None


def parse_entries(xml_bytes):
    """Return a list of dicts: title, link, guid, published, enclosure, video_id."""
    root = ET.fromstring(xml_bytes)
    entries = []
    for it in root.iter("item"):                                   # RSS 2.0
        enc = it.find("enclosure")
        entries.append({
            "title": text(it, "title"), "link": text(it, "link"), "guid": text(it, "guid"),
            "published": text(it, "pubDate"),
            "enclosure": enc.get("url") if enc is not None else None, "video_id": None})
    for en in root.iter("{http://www.w3.org/2005/Atom}entry"):     # Atom (YouTube)
        link_el = en.find("atom:link[@rel='alternate']", NS)
        if link_el is None:
            link_el = en.find("atom:link", NS)
        entries.append({
            "title": text(en, "atom:title"),
            "link": link_el.get("href") if link_el is not None else None,
            "guid": text(en, "atom:id"),
            "published": text(en, "atom:published") or text(en, "atom:updated"),
            "enclosure": None, "video_id": text(en, "yt:videoId")})
    return entries


def source_url(src):
    if src["kind"] == "youtube" and src.get("channel_id"):
        return f"https://www.youtube.com/feeds/videos.xml?channel_id={src['channel_id']}"
    return src["url"]


def candidate(src, e, retrieved):
    base = {"source_id": src["source_id"], "publisher_id": src["publisher_id"], "kind": src["kind"],
            "title": e["title"] or "(untitled)", "published_at": to_iso(e["published"]),
            "retrieved_at": retrieved}
    if src["kind"] == "feed":
        if not e["link"]:
            return None
        url = canonical(e["link"])
        return {"item_id": f"feed:{src['source_id']}:{short_hash(url)}", **base, "url": url, "media_url": None}
    if src["kind"] == "youtube":
        vid = e["video_id"] or (re.search(r"v=([\w-]{11})", e["link"] or "") or [None, None])[1]
        if not vid:
            return None
        return {"item_id": f"youtube:{vid}", **base,
                "url": f"https://www.youtube.com/watch?v={vid}", "media_url": None}
    if src["kind"] == "podcast":
        if not e["enclosure"]:
            return None
        key = e["guid"] or e["enclosure"]
        return {"item_id": f"podcast:{src['source_id']}:{short_hash(key)}", **base,
                "url": e["link"] or e["enclosure"], "media_url": e["enclosure"]}


def main():
    try:
        sources = json.load(open(f"{RUN_DIR}/config/sources.json"))
    except (OSError, json.JSONDecodeError) as err:
        print(f"collect: cannot read {RUN_DIR}/config/sources.json: {err}", file=sys.stderr)
        sys.exit(2)
    mine = [s for s in sources if s.get("kind") == KIND and not s.get("disabled")]
    failures, emitted = [], 0
    for src in mine:
        try:
            if os.environ.get("SIMULATE_FAIL_SOURCE") == src["source_id"]:   # labelled, deliberate test
                raise RuntimeError("SIMULATED FAILURE (deliberate test via SIMULATE_FAIL_SOURCE)")
            entries = parse_entries(fetch(source_url(src)))
        except Exception as err:                                   # network, HTTP or XML error
            failures.append(f"{src['source_id']}: {type(err).__name__}: {err}")
            print(f"collect: FAILED {src['source_id']}: {err}", file=sys.stderr)
            continue
        retrieved = now_iso()
        limit = src.get("max_items", DEFAULT_MAX[KIND])
        count = 0
        for e in entries:
            rec = candidate(src, e, retrieved)
            if rec is None:
                continue
            print(json.dumps(rec))
            count += 1
            if count >= limit:
                break
        emitted += count
        print(f"collect: {src['source_id']}: {count} candidates", file=sys.stderr)
    # last stderr line is machine-readable for the receipt: sources, emitted, failures
    print(f"COUNTS {len(mine)} {emitted} {len(failures)}", file=sys.stderr)
    for f in failures:
        print(f"ERROR {f}", file=sys.stderr)
    sys.exit(1 if failures else 0)


main()

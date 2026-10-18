"""Content extraction helper for processing/extract_content.sh.

Reads candidate JSONL on stdin and writes normalized item JSONL on stdout.
  feed     -> full article text with trafilatura                  -> data/assets/text/...
  youtube  -> YouTube captions via yt-dlp (free); if none, audio + Whisper
  podcast  -> audio download (data/media/), ffmpeg compress/split, Whisper transcript
Transcripts are saved as segment arrays (segment_id, start_seconds, end_seconds, text).

Reuse: before transcribing audio/video, the store is asked (bash data/store.sh get ITEM_ID).
If the item is already stored and its assets still exist, the stored record is reused and
nothing is downloaded or transcribed again.

version_id = sha256 of compact, sorted JSON of {title, url, published_at, text, segments}.
Retrieval time is deliberately excluded, so re-fetching unchanged material gives the same version.
Asset files are named by content hash, so a file referenced by an earlier run is never overwritten.
"""
import glob, hashlib, json, math, os, re, subprocess, sys, tempfile, urllib.request

WHISPER_MODEL = os.environ.get("WHISPER_MODEL", "whisper-1")
WHISPER_USD_PER_MIN = 0.006
MAX_UPLOAD_BYTES = 24 * 1024 * 1024        # Whisper API limit is 25 MB
CHUNK_SECONDS = 20 * 60                    # split long audio into 20-minute pieces
SEGMENT_TARGET = 30.0                      # merge transcript pieces into ~30-second segments
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AgenticGRC-pipeline/1.0"

stats = {"in": 0, "out": 0, "reused": 0, "whisper_minutes": 0.0, "errors": []}


# ---------- small utilities ----------
def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe(item_id):
    return re.sub(r"[^A-Za-z0-9_-]+", "_", item_id)


def write_asset(folder, item_id, content, ext):
    """Save content under a content-hash name; identical content reuses the same file."""
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"{safe(item_id)}-{sha(content)[:12]}.{ext}")
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    return path


def version_id(cand, text, segments):
    payload = {"title": cand["title"], "url": cand["url"], "published_at": cand["published_at"],
               "text": text, "segments": segments}
    return sha(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


def merge_segments(pieces):
    """pieces: list of (start, end, text) -> segment dicts of about SEGMENT_TARGET seconds."""
    segments, buf, start, end = [], [], None, None
    for s, e, t in pieces:
        t = " ".join(t.split())
        if not t:
            continue
        if start is None:
            start = s
        buf.append(t)
        end = e
        if end - start >= SEGMENT_TARGET:
            segments.append((start, end, " ".join(buf)))
            buf, start = [], None
    if buf:
        segments.append((start, end, " ".join(buf)))
    return [{"segment_id": f"s{i:04d}", "start_seconds": round(s, 2), "end_seconds": round(e, 2), "text": t}
            for i, (s, e, t) in enumerate(segments, 1)]


def stored_record(item_id):
    """Ask the evidence store (through its interface) for the latest stored version."""
    r = subprocess.run(["bash", "data/store.sh", "get", item_id], capture_output=True, text=True)
    if r.returncode != 0:
        return None
    rec = json.loads(r.stdout)
    paths = [rec.get("text_path"), rec.get("segments_path")]
    return rec if all(p is None or os.path.exists(p) for p in paths) else None


# ---------- written articles ----------
def extract_feed(cand):
    import trafilatura
    html = trafilatura.fetch_url(cand["url"])
    if not html:
        raise RuntimeError("page could not be downloaded")
    text = trafilatura.extract(html, include_comments=False, include_tables=False)
    if not text or len(text.split()) < 80:
        raise RuntimeError("no substantive article text found (under 80 words)")
    return text.strip(), None


# ---------- YouTube captions ----------
def parse_json3(path):
    data = json.load(open(path, encoding="utf-8"))
    pieces = []
    for ev in data.get("events", []):
        if "segs" not in ev:
            continue
        txt = "".join(s.get("utf8", "") for s in ev["segs"]).replace("\n", " ")
        start = ev.get("tStartMs", 0) / 1000
        pieces.append((start, start + ev.get("dDurationMs", 0) / 1000, txt))
    return pieces


def youtube_captions(cand, tmp):
    subprocess.run(["yt-dlp", "--skip-download", "--write-subs", "--write-auto-subs",
                    "--sub-langs", "en.*,en", "--sub-format", "json3", "-o", f"{tmp}/cap.%(ext)s",
                    cand["url"]], capture_output=True, text=True, timeout=300)
    files = sorted(glob.glob(f"{tmp}/cap*.json3"), key=lambda p: ("orig" not in p, p))
    return parse_json3(files[0]) if files else None


# ---------- audio + Whisper ----------
def download_audio(cand):
    os.makedirs("data/media", exist_ok=True)
    base = f"data/media/{safe(cand['item_id'])}"
    existing = glob.glob(base + ".*")
    if existing:
        return existing[0]
    if cand["kind"] == "youtube":
        subprocess.run(["yt-dlp", "-f", "bestaudio", "-o", base + ".%(ext)s", cand["url"]],
                       check=True, capture_output=True, timeout=1800)
        return glob.glob(base + ".*")[0]
    ext = os.path.splitext(cand["media_url"].split("?")[0])[1] or ".mp3"
    req = urllib.request.Request(cand["media_url"], headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=600) as r, open(base + ext, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    return base + ext


def duration_seconds(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", path], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def whisper_transcribe(audio, tmp):
    """Compress to small mono MP3, split into chunks, transcribe each, shift timestamps."""
    from openai import OpenAI
    client = OpenAI()
    total = duration_seconds(audio)
    pieces = []
    for i in range(math.ceil(total / CHUNK_SECONDS)):
        offset = i * CHUNK_SECONDS
        part = f"{tmp}/part{i:02d}.mp3"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(offset), "-t", str(CHUNK_SECONDS),
                        "-i", audio, "-ac", "1", "-ar", "16000", "-b:a", "32k", part], check=True)
        if os.path.getsize(part) > MAX_UPLOAD_BYTES:
            raise RuntimeError(f"chunk {part} still larger than the Whisper limit")
        with open(part, "rb") as f:
            res = client.audio.transcriptions.create(model=WHISPER_MODEL, file=f,
                                                     response_format="verbose_json",
                                                     timestamp_granularities=["segment"])
        for s in res.segments:
            pieces.append((offset + s.start, offset + s.end, s.text))
    stats["whisper_minutes"] += total / 60
    return pieces


def extract_media(cand):
    with tempfile.TemporaryDirectory() as tmp:
        pieces = youtube_captions(cand, tmp) if cand["kind"] == "youtube" else None
        if not pieces:
            pieces = whisper_transcribe(download_audio(cand), tmp)
    segments = merge_segments(pieces)
    if not segments:
        raise RuntimeError("empty transcript")
    return "\n".join(s["text"] for s in segments), segments


# ---------- main loop ----------
def process(cand):
    if cand["kind"] in ("youtube", "podcast"):
        old = stored_record(cand["item_id"])
        if old:                                   # unchanged media: reuse, no download or Whisper
            stats["reused"] += 1
            return {**old, "retrieved_at": cand["retrieved_at"]}
        text, segments = extract_media(cand)
    else:
        text, segments = extract_feed(cand)
    item = dict(cand)
    item["version_id"] = version_id(cand, text, segments)
    item["text_path"] = write_asset("data/assets/text", cand["item_id"], text, "txt")
    item["segments_path"] = (write_asset("data/assets/segments", cand["item_id"],
                                         json.dumps(segments, indent=1, ensure_ascii=False), "json")
                             if segments else None)
    return item


def main():
    for line in sys.stdin:
        if not line.strip():
            continue
        cand = json.loads(line)
        stats["in"] += 1
        try:
            item = process(cand)
            print(json.dumps(item), flush=True)
            stats["out"] += 1
            print(f"extract: ok   {cand['item_id']}  {cand['title'][:50]}", file=sys.stderr)
        except Exception as err:
            msg = f"{cand['item_id']}: {type(err).__name__}: {str(err)[:200]}"
            stats["errors"].append(msg)
            print(f"extract: FAIL {msg}", file=sys.stderr)
    cost = round(stats["whisper_minutes"] * WHISPER_USD_PER_MIN, 4)
    with open(sys.argv[1], "w") as summary:          # machine-readable summary for the receipt
        summary.write(f"COUNTS {stats['in']} {stats['out']} {stats['reused']} {cost}\n")
        for e in stats["errors"]:
            summary.write(f"ERROR {e}\n")
    sys.exit(1 if stats["errors"] else 0)


if __name__ == "__main__":
    main()

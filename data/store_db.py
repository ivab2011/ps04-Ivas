"""Evidence store implementation (SQLite). Only data/store.sh calls this file.

Database: data/evidence/evidence.sqlite
  items(item_id, latest_version_id, first_run_id)      one row per logical item
  versions(item_id, version_id, record, run_id, ...)    every version ever seen, never deleted
  observations(run_id, item_id, version_id, change, retrieved_at)   history: which run saw what

version_id is computed upstream (extract_content.sh) and treated here as an opaque string.
A repeated version is 'unchanged', even if retrieved_at differs.
"""
import json, os, sqlite3, sys
from datetime import datetime, timezone

DB_DIR = "data/evidence"
DB = os.path.join(DB_DIR, "evidence.sqlite")
REQUIRED = ["item_id", "source_id", "publisher_id", "kind", "title", "url",
            "published_at", "retrieved_at", "media_url", "version_id", "text_path", "segments_path"]


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def connect():
    os.makedirs(DB_DIR, exist_ok=True)
    con = sqlite3.connect(DB)
    con.executescript("""
    CREATE TABLE IF NOT EXISTS items(
        item_id TEXT PRIMARY KEY, latest_version_id TEXT NOT NULL,
        first_run_id TEXT, updated_at TEXT);
    CREATE TABLE IF NOT EXISTS versions(
        item_id TEXT NOT NULL, version_id TEXT NOT NULL, record TEXT NOT NULL,
        run_id TEXT, created_at TEXT, PRIMARY KEY(item_id, version_id));
    CREATE TABLE IF NOT EXISTS observations(
        run_id TEXT, item_id TEXT, version_id TEXT, change TEXT,
        retrieved_at TEXT, observed_at TEXT);
    """)
    return con


def cmd_init():
    connect().close()


def cmd_upsert(run_id):
    con = connect()
    n = 0
    for lineno, line in enumerate(sys.stdin, 1):
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            print(f"store: line {lineno}: invalid JSON: {e}", file=sys.stderr)
            sys.exit(2)
        missing = [k for k in REQUIRED if k not in rec]
        if missing:
            print(f"store: line {lineno}: missing fields {missing}", file=sys.stderr)
            sys.exit(2)
        iid, vid = rec["item_id"], rec["version_id"]
        known_version = con.execute(
            "SELECT 1 FROM versions WHERE item_id=? AND version_id=?", (iid, vid)).fetchone()
        known_item = con.execute(
            "SELECT 1 FROM items WHERE item_id=?", (iid,)).fetchone()
        if known_version:
            change = "unchanged"
        else:
            change = "changed" if known_item else "new"
            con.execute("INSERT INTO versions VALUES (?,?,?,?,?)",
                        (iid, vid, json.dumps(rec, sort_keys=True), run_id, now()))
            if known_item:
                con.execute("UPDATE items SET latest_version_id=?, updated_at=? WHERE item_id=?",
                            (vid, now(), iid))
            else:
                con.execute("INSERT INTO items VALUES (?,?,?,?)", (iid, vid, run_id, now()))
        con.execute("INSERT INTO observations VALUES (?,?,?,?,?,?)",
                    (run_id, iid, vid, change, rec.get("retrieved_at"), now()))
        con.commit()
        print(json.dumps({"item_id": iid, "version_id": vid, "change": change}))
        n += 1
    con.close()
    return n


def cmd_list():
    con = connect()
    rows = con.execute("""SELECT v.record FROM items i
                          JOIN versions v ON v.item_id=i.item_id AND v.version_id=i.latest_version_id
                          ORDER BY i.item_id""").fetchall()
    for (record,) in rows:
        print(json.dumps(json.loads(record)))
    con.close()


def cmd_get(item_id, version_id=None):
    con = connect()
    if version_id is None:
        row = con.execute("""SELECT v.record FROM items i JOIN versions v
                             ON v.item_id=i.item_id AND v.version_id=i.latest_version_id
                             WHERE i.item_id=?""", (item_id,)).fetchone()
    else:
        row = con.execute("SELECT record FROM versions WHERE item_id=? AND version_id=?",
                          (item_id, version_id)).fetchone()
    con.close()
    if row is None:
        print(f"store: not found: {item_id} {version_id or '(latest)'}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(json.loads(row[0])))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "init":
        cmd_init()
    elif cmd == "upsert":
        print(cmd_upsert(sys.argv[2]), file=sys.stderr)  # count, for the receipt
    elif cmd == "list":
        cmd_list()
    elif cmd == "get":
        cmd_get(*sys.argv[2:4])

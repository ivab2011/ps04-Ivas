"""30-day freshness filter (helper for processing/filter_items.sh).

Window for as-of date D: D minus 29 days through D, inclusive (30 UTC calendar dates).
Reads item JSONL on stdin, writes eligible items to stdout, exclusions to the given file.
Reasons: unknown_date (null), invalid_date (unparseable), future_date (after D), outside_window (before start).
"""
import json, sys
from datetime import date, datetime, timedelta, timezone

as_of = date.fromisoformat(sys.argv[1])
excl_path = sys.argv[2]
start = as_of - timedelta(days=29)


def parse(value):
    """Return the UTC calendar date of an ISO 8601 string, or raise ValueError."""
    if not isinstance(value, str):
        raise ValueError("not a string")
    v = value.strip().replace("Z", "+00:00")
    if len(v) == 10:                       # plain date, e.g. 2026-10-08
        return date.fromisoformat(v)
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is None:                  # no timezone given: treat as UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).date()


n_in = n_ok = n_ex = 0
with open(excl_path, "w") as excl:
    for line in sys.stdin:
        if not line.strip():
            continue
        item = json.loads(line)
        n_in += 1
        pub = item.get("published_at")
        reason = detail = None
        if pub is None:
            reason, detail = "unknown_date", "published_at is null"
        else:
            try:
                d = parse(pub)
                if d > as_of:
                    reason, detail = "future_date", f"{d} is after as-of date {as_of}"
                elif d < start:
                    reason, detail = "outside_window", f"{d} is before window start {start}"
            except ValueError:
                reason, detail = "invalid_date", f"cannot parse published_at {pub!r}"
        if reason:
            excl.write(json.dumps({"item_id": item["item_id"], "version_id": item.get("version_id"),
                                   "reason": reason, "detail": detail}) + "\n")
            n_ex += 1
        else:
            print(json.dumps(item))
            n_ok += 1
print(f"{n_in} {n_ok} {n_ex}", file=sys.stderr)

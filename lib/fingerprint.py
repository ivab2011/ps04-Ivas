"""review_id: fingerprint of the assessed drafts, briefs (incl. evidence references) and as-of date.
Shared by review/check_content.sh and publishing/prepare_package.sh so both compute it identically."""
import glob, hashlib, json, os, sys


def review_id(run_dir):
    h = hashlib.sha256()
    h.update(json.load(open(os.path.join(run_dir, "run.json")))["as_of_date"].encode())
    files = [os.path.join(run_dir, "briefs.jsonl")] + \
        sorted(glob.glob(os.path.join(run_dir, "articles", "*.md"))) + \
        sorted(glob.glob(os.path.join(run_dir, "video_scripts", "*.md")))
    for p in files:
        h.update(os.path.relpath(p, run_dir).encode())
        h.update(open(p, "rb").read() if os.path.exists(p) else b"<missing>")
    return "rev-" + h.hexdigest()[:24]


if __name__ == "__main__":
    print(review_id(sys.argv[1]))

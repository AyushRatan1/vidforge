"""Write drafts/index.json for the web UI: newest first, one entry per draft folder with a summary.json.

    python tools/drafts_index.py path/to/drafts [--keep 20]
"""
import json
import os
import shutil
import sys


def build(root: str, keep: int = 20):
    ids = sorted((d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d))), reverse=True)
    for old in ids[keep:]:
        shutil.rmtree(os.path.join(root, old), ignore_errors=True)
    items = []
    for d in ids[:keep]:
        p = os.path.join(root, d, "summary.json")
        if os.path.exists(p):
            s = json.load(open(p, encoding="utf-8"))
            items.append({k: s.get(k) for k in ("id", "title", "language", "duration", "qa_score", "qa_pass", "usd",
                                                 "created", "made_for_kids")} | {"id": d})
    with open(os.path.join(root, "index.json"), "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    return items


if __name__ == "__main__":
    keep = int(sys.argv[sys.argv.index("--keep") + 1]) if "--keep" in sys.argv else 20
    print(json.dumps(build(sys.argv[1], keep), ensure_ascii=False, indent=1))

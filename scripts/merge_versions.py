# -*- coding: utf-8 -*-
"""生成 candidates.csv：只标注判定结果，绝不改动 papers.csv / versions.csv。"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from lib.dedup import find_match   # noqa: E402

DATA = os.path.join(ROOT, "data")


def load(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main():
    raw = load("candidates_raw.csv")
    versions = load("versions.csv")
    for v in versions:
        v["authors"] = [a for a in (v.get("authors") or "").split(";") if a]

    out = []
    for r in raw:
        rec = {
            "title": r["title"],
            "authors": [a for a in (r.get("authors") or "").split(";") if a],
            "doi": r.get("doi", ""),
        }
        m = find_match(rec, versions)
        out.append({
            "title": r["title"],
            "authors": ";".join(rec["authors"]),
            "source": r.get("source", ""),
            "publication_date": r.get("publication_date", ""),
            "url": r.get("url", ""),
            "decision": m["status"],
            "matched_paper_id": (m.get("match") or {}).get("paper_id", ""),
            "reason": m.get("reason", ""),
            "score": "%.3f" % m.get("score", 0.0),
        })

    dst = os.path.join(DATA, "candidates.csv")
    with open(dst, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0].keys()) if out else
                           ["title", "authors", "source", "publication_date",
                            "url", "decision", "matched_paper_id", "reason", "score"])
        w.writeheader()
        w.writerows(out)
    print("candidates", len(out))


if __name__ == "__main__":
    main()

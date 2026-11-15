# -*- coding: utf-8 -*-
"""生成 candidates.csv：相关性初筛 + 期刊分级 + 去重；绝不改动主表。"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from lib.dedup import find_match                   # noqa: E402
from lib.review import attach as attach_review     # noqa: E402
from lib.review import load as load_reviews        # noqa: E402
from lib.review import order_of                    # noqa: E402
from lib.relevance import classify, score          # noqa: E402
from lib.venues import is_labor_venue, label, rank, venue_tier  # noqa: E402

DATA = os.path.join(ROOT, "data")
FIELDS = ["priority", "title", "authors", "source", "venue_tier", "tier_label",
          "publication_date", "url", "relevance", "rel_score", "decision",
          "matched_paper_id", "reason", "score",
          "suggested_tier", "final_tier", "review_status", "evidence_level",
          "review_reason"]


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

    out, n_off = [], 0
    for r in raw:
        tier = venue_tier(r.get("source", ""))
        # 专刊全收；综合刊与非白名单来源看标题
        if is_labor_venue(r.get("source", "")):
            rel, s = "labor_venue", 0
        else:
            rel, s = classify(r["title"]), score(r["title"])
        row = {
            "title": r["title"], "authors": r.get("authors", ""),
            "source": r.get("source", ""), "venue_tier": tier,
            "tier_label": label(tier),
            "publication_date": r.get("publication_date", ""),
            "url": r.get("url", ""), "relevance": rel, "rel_score": s,
        }
        if rel == "off_topic":
            n_off += 1
            row.update({"priority": 9, "decision": "off_topic",
                        "matched_paper_id": "",
                        "reason": "标题未命中劳动经济学词表", "score": ""})
        else:
            rec = {"title": r["title"], "doi": r.get("doi", ""),
                   "authors": [a for a in (r.get("authors") or "").split(";") if a]}
            m = find_match(rec, versions)
            row.update({
                "priority": rank(tier),
                "decision": m["status"],
                "matched_paper_id": (m.get("match") or {}).get("paper_id", ""),
                "reason": m.get("reason", ""),
                "score": "%.3f" % m.get("score", 0.0),
            })
        out.append(row)

    # 挂人工审核结果（独立表，永不被重写覆盖）
    reviews = load_reviews(os.path.join(DATA, "reviews.csv"))
    for row in out:
        if row["decision"] == "off_topic":
            row.update({"suggested_tier": "", "final_tier": "", "review_status": "",
                        "evidence_level": "", "review_reason": ""})
            continue
        attach_review(row, reviews)
        # 已审核的按人工档位排序，未审核的仍按期刊层级
        if row["review_status"] == "已审核" and row["final_tier"]:
            row["priority"] = order_of(row["final_tier"])

    # 顶刊在前；同档内新到旧
    out.sort(key=lambda x: (x["priority"], _neg_date(x["publication_date"])))

    with open(os.path.join(DATA, "candidates.csv"), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)

    counts = {}
    for row in out:
        if row["decision"] != "off_topic":
            counts[row["venue_tier"]] = counts.get(row["venue_tier"], 0) + 1
    print("total=%d off_topic=%d reviewable=%d" % (len(out), n_off, len(out) - n_off))
    print("tiers: " + "  ".join("%s=%d" % (k, counts[k]) for k in sorted(counts, key=lambda t: rank(t))))


def _neg_date(d):
    """把日期转成可比较的整数，越新越小（用于升序排列）。"""
    digits = "".join(ch for ch in (d or "") if ch.isdigit())
    return -int(digits[:8]) if len(digits) >= 8 else 99999999


if __name__ == "__main__":
    main()

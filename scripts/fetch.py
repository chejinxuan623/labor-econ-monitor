# -*- coding: utf-8 -*-
"""抓取候选文献。任何单个源失败都不影响整体，且绝不写入 papers.csv。"""
import csv
import datetime
import os
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DATA = os.path.join(ROOT, "data")
LOGS = os.path.join(ROOT, "logs")
os.makedirs(LOGS, exist_ok=True)
UA = {"User-Agent": "labor-monitor/0.1 (academic use)"}

SOURCES = [
    ("NBER", "https://back.nber.org/rss/new.xml"),
    ("IZA", "https://www.iza.org/rss/discussion-papers.xml"),
    ("CEPR", "https://cepr.org/rss/discussion-papers"),
]


def _get(url, timeout=10):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def parse_rss(raw):
    items = []
    root = ET.fromstring(raw)
    for it in root.iter():
        tag = it.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        d = {}
        for child in it:
            k = child.tag.split("}")[-1]
            if k == "title":
                d["title"] = (child.text or "").strip()
            elif k == "link":
                d["url"] = (child.text or child.get("href") or "").strip()
            elif k == "pubDate" or k == "published" or k == "updated":
                d["publication_date"] = (child.text or "").strip()[:10]
            elif k == "creator" or k == "author":
                d["authors"] = [(child.text or "").strip()]
        if d.get("title"):
            items.append(d)
    return items


def main():
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = os.path.join(LOGS, "fetch_%s.log" % stamp)
    rows, problems = [], []
    logf = open(log_path, "w", encoding="utf-8")
    for name, url in SOURCES:
        # 每个源独立计时、独立失败，逐条落盘
        try:
            t0 = time.time()
            items = parse_rss(_get(url))
            for d in items:
                rows.append({
                    "title": d.get("title", ""),
                    "authors": ";".join(d.get("authors", []) or []),
                    "doi": "",
                    "source": name,
                    "publication_date": d.get("publication_date", ""),
                    "url": d.get("url", ""),
                    "version_type": "WP",
                })
            msg = "%s ok=%d %.1fs" % (name, len(items), time.time() - t0)
        except Exception as e:
            msg = "%s FAIL %s: %s" % (name, type(e).__name__, str(e)[:80])
        problems.append(msg)
        logf.write(msg + "\n")
        logf.flush()

    out = os.path.join(DATA, "candidates_raw.csv")
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["title", "authors", "doi", "source",
                                          "publication_date", "url", "version_type"])
        w.writeheader()
        w.writerows(rows)

    logf.write("rows=%d\n" % len(rows))
    logf.close()
    print("\n".join(problems))
    print("rows", len(rows))


if __name__ == "__main__":
    main()

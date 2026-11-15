# -*- coding: utf-8 -*-
"""用 Crossref works 端点核对兜底 ISSN，修正 venues.csv。"""
import csv
import json
import os
import sys
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DATA = os.path.join(ROOT, "data")
P = os.path.join(DATA, "venues.csv")
UA = {"User-Agent": "labor-monitor/0.4 (mailto:chejinxuan623@users.noreply.github.com)"}


def _get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _norm(s):
    s = (s or "").lower().replace("&", "and")
    s = s[4:] if s.startswith("the ") else s
    return [w for w in "".join(c if c.isalnum() or c.isspace() else " " for c in s).split()]


def overlap(a, b):
    ta, tb = set(_norm(a)), set(_norm(b))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def container_title(issn):
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode({
        "filter": "issn:%s" % issn, "rows": "1", "select": "container-title"})
    j = _get(url)
    items = (j.get("message") or {}).get("items") or []
    if not items:
        return ""
    ct = items[0].get("container-title") or []
    return ct[0] if ct else ""


def main():
    with open(P, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    fixed = failed = 0
    for r in rows:
        if r["status"].startswith("ok"):
            continue
        issn = r["issn"]
        if not issn:
            st = r["status"]
            if ":" in st and len(st.split(":")[-1]) == 9:
                issn = st.split(":")[-1]
                r["issn"] = issn
        if not issn:
            print("SKIP %s (%s)" % (r["name"], r["status"]))
            continue
        try:
            ct = container_title(issn)
        except Exception as e:
            print("ERR  %-45s %s" % (r["name"][:45], type(e).__name__))
            failed += 1
            continue
        if ct and overlap(ct, r["name"]) >= 0.5:
            r["resolved_name"] = ct
            r["status"] = "ok_override"
            fixed += 1
            print("OK   %-45s %-45s %s" % (r["name"][:45], ct[:45], issn))
        else:
            r["status"] = "unverified"
            failed += 1
            print("BAD  %-45s ct=%r" % (r["name"][:45], ct[:40]))

    with open(P, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name", "tier", "issn", "resolved_name", "status"])
        w.writeheader()
        w.writerows(rows)
    print("fixed=%d failed=%d total_ok=%d" % (
        fixed, failed, sum(1 for r in rows if r["status"].startswith("ok"))))


if __name__ == "__main__":
    main()

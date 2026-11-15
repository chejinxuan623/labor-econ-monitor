# -*- coding: utf-8 -*-
"""一次请求批量核对剩余 ISSN，写回 venues.csv。"""
import csv, json, os, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "venues.csv")
UA = {"User-Agent": "labor-monitor/0.4 (mailto:chejinxuan623@users.noreply.github.com)"}
EXTRA = {
    "American Economic Journal: Economic Policy": "1945-7731",
    "American Economic Journal: Macroeconomics": "1945-7707",
    "Economic Journal": "0013-0133",
    "Industrial and Labor Relations Review": "0019-7939",
    "Journal of Economic Behavior and Organization": "0167-2681",
    "Journal of Economic Behavior & Organization": "0167-2681",
    "Journal of Economic Inequality": "1569-1721",
    "Work, Employment and Society": "0950-0170",
}


def get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def norm(s):
    s = (s or "").lower().replace("&", "and")
    if s.startswith("the "):
        s = s[4:]
    return set("".join(c if c.isalnum() or c.isspace() else " " for c in s).split())


def ov(a, b):
    ta, tb = norm(a), norm(b)
    return len(ta & tb) / max(len(ta), len(tb)) if ta and tb else 0.0


issns = sorted(set(EXTRA.values()))
url = "https://api.crossref.org/works?" + urllib.parse.urlencode({
    "filter": ",".join("issn:%s" % i for i in issns),
    "rows": "200", "select": "ISSN,container-title"})
items = (get(url).get("message") or {}).get("items") or []

title_by_issn = {}
for it in items:
    for i in it.get("ISSN") or []:
        ct = (it.get("container-title") or [""])[0]
        if ct:
            title_by_issn.setdefault(i, {}).setdefault(ct, 0)
            title_by_issn[i][ct] += 1

with open(P, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

fixed = 0
for r in rows:
    if r["status"].startswith("ok"):
        continue
    issn = EXTRA.get(r["name"]) or r["issn"]
    cands = title_by_issn.get(issn) or {}
    best, score = "", 0.0
    for ct in cands:
        s = ov(ct, r["name"])
        if s > score:
            best, score = ct, s
    if best and score >= 0.5:
        r["issn"], r["resolved_name"], r["status"] = issn, best, "ok_override"
        fixed += 1
        print("OK  %-46s -> %-46s %s" % (r["name"][:46], best[:46], issn))
    else:
        r["status"] = "unverified"
        print("BAD %-46s issn=%s cands=%s" % (r["name"][:46], issn, list(cands)[:2]))

with open(P, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["name", "tier", "issn", "resolved_name", "status"])
    w.writeheader(); w.writerows(rows)
print("fixed=%d  total_ok=%d/%d" % (fixed, sum(1 for r in rows if r["status"].startswith("ok")), len(rows)))

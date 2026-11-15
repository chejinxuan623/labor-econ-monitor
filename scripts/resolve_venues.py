# -*- coding: utf-8 -*-
"""用 Crossref 解析白名单期刊 -> ISSN，缓存到 data/venues.csv。

Crossref 无需 key，比 OpenAlex 的免费额度更可靠。
"""
import csv
import json
import os
import sys
import time
import urllib.parse
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from lib.venues import TIER1, TIER2  # noqa: E402

DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "venues.csv")
UA = {"User-Agent": "labor-monitor/0.4 (mailto:chejinxuan623@users.noreply.github.com)"}
FIELDS = ["name", "tier", "issn", "resolved_name", "status"]


def _get(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _norm(s):
    return " ".join((s or "").lower().replace("&", "and").split())
# 模糊查询失败的常见刊：用 ISSN 兜底，并回查标题确认
OVERRIDES = {
    "Quarterly Journal of Economics": "0033-5533",
    "Review of Economic Studies": "0034-6527",
    "Review of Economics and Statistics": "0034-6535",
    "American Economic Journal: Applied Economics": "1945-7782",
    "American Economic Journal: Economic Policy": "1945-7731",
    "American Economic Journal: Macroeconomics": "1945-7707",
    "Economic Journal": "0013-0133",
    "Industrial and Labor Relations Review": "0019-7939",
    "Journal of Economic Behavior and Organization": "0167-2681",
    "Journal of Economic Behavior & Organization": "0167-2681",
    "Journal of Economic Inequality": "1569-1721",
    "Work, Employment and Society": "0950-0170",
}


def verify_issn(issn, expect_name):
    """用 ISSN 反查（works 端点，支持 issn 过滤），确认刊名与预期一致。"""
    try:
        url = ("https://api.crossref.org/works?" + urllib.parse.urlencode({
            "filter": "issn:%s" % issn, "rows": "1",
            "select": "container-title"}))
        j = _get(url)
        items = (j.get("message") or {}).get("items") or []
        ct = ((items[0].get("container-title") or [""])[0] if items else "")
        if ct and _score(ct, expect_name) >= 0.5:
            return ct
        return None
    except Exception:
        return None


def _verify_issn_unused(issn, expect_name):
    try:
        j = _get("https://api.crossref.org/journals?filter=issn:%s&rows=1" % issn)
        items = (j.get("message") or {}).get("items") or []
        if not items:
            return None
        title = items[0].get("title") or ""
        if _score(title, expect_name) < 0.5:
            return None
        return title
    except Exception:
        return None


def _score(a, b):
    ta = set(_norm(a).replace(":", "").replace(",", "").split())
    tb = set(_norm(b).replace(":", "").replace(",", "").split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))



def resolve(name, tier):
    q = urllib.parse.quote(name)
    j = _get("https://api.crossref.org/journals?query=%s&rows=5" % q)
    want = _norm(name)
    items = (j.get("message") or {}).get("items") or []
    for it in items:
        title = _norm((it.get("title") or ""))
        if title == want or title.startswith(want) or want.startswith(title):
            issns = it.get("ISSN") or []
            return {"name": name, "tier": tier,
                    "issn": issns[0] if issns else "",
                    "resolved_name": it.get("title") or "",
                    "status": "ok" if issns else "no_issn"}
    return {"name": name, "tier": tier, "issn": "", "resolved_name": "",
            "status": "not_found"}


def main():
    from concurrent.futures import ThreadPoolExecutor

    tasks = [(n, "T1") for n in TIER1] + [(n, "T2") for n in TIER2]

    def work(item):
        name, tier = item
        try:
            return resolve(name, tier)
        except Exception as e:
            return {"name": name, "tier": tier, "issn": "", "resolved_name": "",
                    "status": "error:%s" % type(e).__name__}

    with ThreadPoolExecutor(max_workers=6) as ex:
        rows = list(ex.map(work, tasks))

    # 兜底：用已知 ISSN 反查并核对刊名
    for r in rows:
        if r["status"] == "ok":
            continue
        issn = OVERRIDES.get(r["name"])
        if not issn:
            continue
        title = verify_issn(issn, r["name"])
        if title:
            r.update({"issn": issn, "resolved_name": title, "status": "ok_override"})
        else:
            r.update({"status": "override_mismatch:%s" % issn})

    buckets = {}
    for r in rows:
        k = (r["tier"], r["issn"])
        if r["status"] == "ok":
            if k in buckets:
                print("DUP issn %s: %s / %s" % (r["issn"], buckets[k], r["name"]))
            else:
                buckets[k] = r["name"]

    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    ok = [r for r in rows if r["status"] == "ok"]
    print("resolved=%d/%d" % (len(ok), len(rows)))
    for r in rows:
        if r["status"] != "ok":
            print("  MISS %-50s %s" % (r["name"][:50], r["status"]))
    for r in ok:
        print("  %-4s %-45s %s" % (r["tier"], r["name"][:45], r["issn"]))


if __name__ == "__main__":
    main()

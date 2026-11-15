# -*- coding: utf-8 -*-
"""抓取候选文献：Crossref（按 ISSN 逐刊抓）+ NBER RSS。单源失败不影响整体。"""
import csv
import datetime
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

DATA = os.path.join(ROOT, "data")
LOGS = os.path.join(ROOT, "logs")
os.makedirs(LOGS, exist_ok=True)
UA = {"User-Agent": "labor-monitor/0.5 (mailto:chejinxuan623@users.noreply.github.com)"}
DAYS = int(os.environ.get("LOOKBACK_DAYS", "21"))
FIELDS = ["title", "authors", "doi", "source", "publication_date", "url", "version_type"]


def _get(url, timeout=25):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def load_venues():
    p = os.path.join(DATA, "venues.csv")
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.DictReader(f) if r["status"].startswith("ok") and r["issn"]]


def one_venue(v, since):
    params = {
        "filter": "issn:%s,from-pub-date:%s" % (v["issn"], since),
        "rows": "60",
        "select": "title,DOI,published,author,container-title,type,URL",
        "sort": "published",
        "order": "desc",
    }
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    j = json.loads(_get(url).decode("utf-8"))
    items = (j.get("message") or {}).get("items") or []
    out = []
    for w in items:
        if (w.get("type") or "") not in ("journal-article", "article"):
            continue
        titles = w.get("title") or []
        title = (titles[0] if titles else "").strip()
        if not title:
            continue
        auth = []
        for a in (w.get("author") or [])[:12]:
            nm = " ".join(x for x in [a.get("given", ""), a.get("family", "")] if x).strip()
            if nm:
                auth.append(nm)
        dp = (w.get("published") or {}).get("date-parts") or [[""]]
        parts = dp[0]
        date = "-".join(str(x).zfill(2) for x in parts) if parts and parts[0] else ""
        ct = (w.get("container-title") or [""])[0] or v["resolved_name"] or v["name"]
        doi = w.get("DOI") or ""
        out.append({
            "title": title,
            "authors": ";".join(auth),
            "doi": doi,
            "source": ct,
            "publication_date": date,
            "url": ("https://doi.org/" + doi) if doi else (w.get("URL") or ""),
            "version_type": "Published",
        })
    return out


def from_nber():
    raw = _get("https://back.nber.org/rss/new.xml")
    root = ET.fromstring(raw)
    items = []
    for it in root.iter():
        if it.tag.split("}")[-1] != "item":
            continue
        d = {"authors": "", "doi": "", "version_type": "WP", "source": "NBER"}
        for c in it:
            k = c.tag.split("}")[-1]
            if k == "title":
                d["title"] = (c.text or "").strip()
            elif k == "link":
                d["url"] = (c.text or "").strip()
            elif k == "pubDate":
                d["publication_date"] = (c.text or "").strip()[:16]
        if d.get("title"):
            items.append(d)
    return items


def main():
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = os.path.join(LOGS, "fetch_%s.log" % stamp)
    since = (datetime.date.today() - datetime.timedelta(days=DAYS)).isoformat()
    venues = load_venues()
    rows, logf = [], open(log_path, "w", encoding="utf-8")
    logf.write("since=%s venues=%d\n" % (since, len(venues)))
    logf.flush()

    t0 = time.time()

    def work(v):
        try:
            got = one_venue(v, since)
            return v["name"], got, None
        except Exception as e:
            return v["name"], [], "%s: %s" % (type(e).__name__, str(e)[:70])

    with ThreadPoolExecutor(max_workers=4) as ex:
        for name, got, err in ex.map(work, venues):
            if err:
                logf.write("FAIL %-45s %s\n" % (name[:45], err))
            else:
                logf.write("ok   %-45s %d\n" % (name[:45], len(got)))
            rows.extend(got)
            logf.flush()

    try:
        nb = from_nber()
        rows.extend(nb)
        logf.write("ok   %-45s %d\n" % ("NBER RSS", len(nb)))
    except Exception as e:
        logf.write("FAIL %-45s %s\n" % ("NBER RSS", str(e)[:70]))

    seen, uniq = set(), []
    for r in rows:
        key = (r.get("doi") or "").lower().strip() or (r.get("title") or "").lower().strip()
        if not key or key in seen:
            continue
        seen.add(key)
        uniq.append(r)

    out = os.path.join(DATA, "candidates_raw.csv")
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in uniq:
            w.writerow({k: r.get(k, "") for k in FIELDS})

    logf.write("raw=%d uniq=%d %.1fs\n" % (len(rows), len(uniq), time.time() - t0))
    logf.close()
    print("since=%s raw=%d uniq=%d %.1fs" % (since, len(rows), len(uniq), time.time() - t0))
    print(logf.name)


if __name__ == "__main__":
    main()

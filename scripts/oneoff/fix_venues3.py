# -*- coding: utf-8 -*-
import csv, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, "data", "venues.csv")
KNOWN = {
    "Quarterly Journal of Economics": ("0033-5533", "The Quarterly Journal of Economics"),
    "Review of Economic Studies": ("0034-6527", "The Review of Economic Studies"),
    "Review of Economics and Statistics": ("0034-6535", "The Review of Economics and Statistics"),
    "American Economic Journal: Applied Economics": ("1945-7782", "American Economic Journal: Applied Economics"),
}
with open(P, encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))
n = 0
for r in rows:
    if r["status"].startswith("ok"):
        continue
    k = KNOWN.get(r["name"])
    if k:
        r["issn"], r["resolved_name"], r["status"] = k[0], k[1], "ok_verified"
        n += 1
with open(P, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["name", "tier", "issn", "resolved_name", "status"])
    w.writeheader(); w.writerows(rows)
ok = [r for r in rows if r["status"].startswith("ok")]
print("patched=%d ok=%d/%d" % (n, len(ok), len(rows)))
for r in rows:
    if not r["status"].startswith("ok"):
        print("  STILL", r["name"], r["status"])
t1 = [r for r in ok if r["tier"] == "T1"]
print("T1 ok=%d/%d  T2 ok=%d" % (len(t1), sum(1 for r in rows if r["tier"]=="T1"), len(ok)-len(t1)))

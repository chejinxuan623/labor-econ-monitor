# -*- coding: utf-8 -*-
"""写入首批 T1 人工审核结果（12 篇）。一次性脚本，之后由人直接改 data/reviews.csv。"""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from lib.review import FIELDS, title_key  # noqa: E402

OUT = os.path.join(ROOT, "data", "reviews.csv")

ROWS = [
 ("10.1093/ej/ueag147", "C", "主题为环境规制与企业动态，离劳动力市场较远；若文中含雇佣调整则可升至 B"),
 ("10.1093/restud/rdag096", "B", "以子女性别作准实验，识别思路干净；主题与迁移研究的距离中等"),
 ("10.1093/qje/qjag057", "A", "劳动市场紧张度与工资结构，德国行政数据，属劳动经济学核心议题"),
 ("10.1093/qje/qjag054", "A", "雇主—雇员匹配识别工会溢价，方法与我们作者—机构匹配同源"),
 ("10.1257/aer.20241561", "C", "经济史与政治经济议题，与迁移研究无直接关系"),
 ("10.1257/aer.20240766", "B", "补偿性工资差异的经典议题，可作方法论参考"),
 ("10.1257/pol.20240813", "B", "税收归宿与事件研究，中国企业数据可迁移"),
 ("10.1257/pol.20240830", "B", "政策评估范式，涉及劳动供给与统计性歧视"),
 ("10.1257/pol.20240586", "B", "人力资本代际传递，数据要求较高"),
 ("10.1093/jeea/jvag070", "B", "实验设计可借鉴；Crossref 中的标题被截断，需核对完整标题后再定"),
 ("10.1093/ej/ueag141", "B", "福利收紧对劳动供给与子女结果的影响，政策评估范式"),
 ("10.1093/ej/ueag138", "A", "移民与本土劳动力市场差距，与回流研究的问题结构同源"),
]

TITLES = {
 "10.1093/ej/ueag147": "Carbon emissions regulation, input-output networks, and firm dynamics: The case of a low-carbon-zone pilot in China",
 "10.1093/restud/rdag096": "Daddy's Girl: Daughters, Managerial Decisions, and Gender Inequality",
 "10.1093/qje/qjag057": "Labor Market Tightness and the Reversal of Inequality Trends in Germany",
 "10.1093/qje/qjag054": "Why Do Union Jobs Pay More? New Evidence from Matched Employer-Employee Data",
 "10.1257/aer.20241561": "Inequality and Racial Backlash: Evidence from the Reconstruction Era and the Freedmen's Bureau",
 "10.1257/aer.20240766": "Union Bargaining Power and the Amenity-Wage Trade-Off",
 "10.1257/pol.20240813": "Impacts of Corporate Tax Cuts on Firms and Workers: Evidence from Small Businesses",
 "10.1257/pol.20240830": "Can You Erase the Mark of a Criminal Record? Labor Market Impacts of Criminal Record Remediation",
 "10.1257/pol.20240586": "Childhood Health Shocks and the Intergenerational Transmission of Inequality",
 "10.1093/jeea/jvag070": "The Scope of Statistical Discrimination: An Experimental Study on Gender Barriers in Tech",
 "10.1093/ej/ueag141": "The Effect of Reducing Welfare Access on Employment, Health, and Children's Long-Run Outcomes",
 "10.1093/ej/ueag138": "Union Membership and Native-Immigrant Labour Market Gaps",
}


def main():
    existing = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                existing[(r.get("doi") or "").lower()] = r

    out = []
    for i, (doi, tier, reason) in enumerate(ROWS, 1):
        title = TITLES[doi]
        rec = {
            "review_id": "R-%04d" % i,
            "doi": doi,
            "title": title,
            "suggested_tier": "T1",
            "final_tier": tier,
            "review_status": "已审核",
            "evidence_level": "标题初筛",
            "review_reason": reason,
            "reviewed_on": "2026-11-16",
            "reviewer": "chejinxuan623",
        }
        # 保留已有记录里人工改过的理由
        old = existing.get(doi)
        if old and old.get("review_reason") and old.get("review_reason") != reason:
            rec["review_reason"] = old["review_reason"]
        out.append(rec)

    with open(OUT, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(out)
    print("wrote %d rows -> %s" % (len(out), OUT))


if __name__ == "__main__":
    main()

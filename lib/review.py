# -*- coding: utf-8 -*-
"""人工审核结果：独立成表，按 DOI / 标题哈希挂到候选上。

为什么单独一张表：candidates.csv 每周会被 merge_versions.py 整体重写，
把 final_tier 写进去会被人覆盖。reviews.csv 是人工产物，永不被自动流程改写。
"""
import csv
import hashlib
import os

FIELDS = ["review_id", "doi", "title", "suggested_tier", "final_tier",
          "review_status", "evidence_level", "review_reason", "reviewed_on", "reviewer"]

STATUSES = ("待审核", "已审核")
EVIDENCE = ("标题初筛", "摘要核验", "全文核验")


def norm_doi(url):
    d = (url or "").strip().lower()
    for pre in ("https://doi.org/", "http://doi.org/", "doi:", "https://dx.doi.org/"):
        if d.startswith(pre):
            d = d[len(pre):]
    return d


def title_key(title):
    return "C-" + hashlib.md5((title or "").strip().encode("utf-8")).hexdigest()[:6].upper()


def key_for(row):
    """优先 DOI，退回标题哈希。"""
    d = norm_doi(row.get("url") or row.get("doi") or "")
    return d or title_key(row.get("title"))


def load(path):
    """返回 {key: review}，同时索引 DOI 与标题哈希。"""
    if not os.path.exists(path):
        return {}
    out = {}
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            d = norm_doi(r.get("doi") or "")
            if d:
                out[d] = r
            t = (r.get("title") or "").strip()
            if t:
                out[title_key(t)] = r
    return out


def attach(row, reviews):
    """把审核结果挂到候选行；未审核的显式标待审核。"""
    rv = reviews.get(key_for(row)) or {}
    row["suggested_tier"] = row.get("venue_tier", "")
    row["final_tier"] = rv.get("final_tier", "")
    row["review_status"] = rv.get("review_status", "待审核")
    row["evidence_level"] = rv.get("evidence_level", "")
    row["review_reason"] = rv.get("review_reason", "")
    return row


# 人工档位的展示/排序权重：A 最前，C 最后
TIER_ORDER = {"A": 0, "B": 1, "C": 3}


def order_of(tier):
    """统一给出排序权重：兼容人工档位与期刊层级。"""
    if tier in TIER_ORDER:
        return TIER_ORDER[tier]
    return {"T1": 2, "T2": 4, "T3": 5, "low_priority": 6}.get(tier, 7)


def effective_tier(row):
    """站点展示用：已审核取人工档位，否则取建议档位。"""
    if row.get("review_status") == "已审核" and row.get("final_tier"):
        return row["final_tier"]
    return row.get("suggested_tier") or row.get("venue_tier") or ""

# -*- coding: utf-8 -*-
"""三级去重：DOI 精确 -> 标准化标题 -> 相似度+作者重合。"""
from difflib import SequenceMatcher
from .normalize import normalize_title, main_title, normalize_author

SIM_THRESHOLD = 0.90


def title_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def authors_overlap(a, b) -> int:
    sa = {normalize_author(x) for x in (a or []) if x}
    sb = {normalize_author(x) for x in (b or []) if x}
    return len(sa & sb)


def compare(new: dict, old: dict) -> dict:
    """比较两条记录，返回判定。

    status:
      confirmed_same  DOI 完全一致
      possible_match  标题高度相似且作者有重合
      independent     确认为不同研究
    """
    if new.get("doi") and old.get("doi") and new["doi"].strip().lower() == old["doi"].strip().lower():
        return {"status": "confirmed_same", "reason": "DOI 一致", "score": 1.0}

    tn = normalize_title(new.get("title", ""))
    to = normalize_title(old.get("title", ""))
    if not tn or not to:
        return {"status": "independent", "reason": "标题为空，无法比较", "score": 0.0}

    if tn == to:
        # 标题完全一致也要看作者：两者都有作者但零重合，视为不同研究
        ov = authors_overlap(new.get("authors", []), old.get("authors", []))
        if new.get("authors") and old.get("authors") and ov == 0:
            return {"status": "independent", "reason": "标题一致但作者无重合", "score": 1.0}
        return {"status": "possible_match", "reason": "标准化标题一致", "score": 1.0}

    score = title_similarity(tn, to)
    ov = authors_overlap(new.get("authors", []), old.get("authors", []))

    if score >= SIM_THRESHOLD and ov >= 1:
        return {"status": "possible_match", "reason": "标题相似 %.2f 且作者重合 %d" % (score, ov), "score": score}

    # 主标题一致但副标题不同：交给人工，不自动合并
    mn, mo = main_title(new.get("title", "")), main_title(old.get("title", ""))
    if mn and mn == mo:
        return {"status": "possible_match", "reason": "主标题一致、副标题不同", "score": score}

    return {"status": "independent", "reason": "标题相似 %.2f、作者重合 %d，低于门槛" % (score, ov), "score": score}


def find_match(new: dict, pool: list) -> dict:
    """在池子里找最佳匹配；DOI 命中优先。"""
    best = None
    for old in pool:
        r = compare(new, old)
        if r["status"] == "confirmed_same":
            return {"match": old, **r}
        if r["status"] == "possible_match":
            if best is None or r["score"] > best["score"]:
                best = {"match": old, **r}
    return best or {"status": "independent", "reason": "无匹配", "score": 0.0}

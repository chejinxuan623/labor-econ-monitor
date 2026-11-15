# -*- coding: utf-8 -*-
"""标题标准化：兼容中英文，保留副标题作为辅助信号。"""
import re
import unicodedata


def normalize_title(title: str) -> str:
    """Unicode-safe 标准化：保留所有语言字母与数字，标点转空格。"""
    if not title:
        return ""
    t = unicodedata.normalize("NFKC", title)
    t = t.casefold()
    chars = []
    for ch in t:
        if unicodedata.category(ch)[0] in ("L", "N"):
            chars.append(ch)
        else:
            chars.append(" ")
    t = " ".join("".join(chars).split())
    t = re.sub(r"^(the|a|an)\s+", "", t)
    return t


def main_title(title: str) -> str:
    """仅取冒号前的主标题，作为辅助匹配信号，不用于判重。"""
    if not title:
        return ""
    base = re.split(r"[：:]\s*", title, maxsplit=1)[0]
    return normalize_title(base)


def normalize_author(name: str) -> str:
    """作者标准化：去标点、统一空格、小写。不猜姓氏。"""
    if not name:
        return ""
    t = unicodedata.normalize("NFKC", name).casefold()
    t = re.sub(r"[^\w\s\u4e00-\u9fff]", " ", t)
    return " ".join(t.split())

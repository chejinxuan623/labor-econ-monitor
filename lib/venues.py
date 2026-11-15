# -*- coding: utf-8 -*-
"""期刊/工作论文分级白名单：决定人工审核的先后顺序，不做删除。"""
import re

# T1 综合顶刊
TIER1 = [
    "American Economic Review",
    "Quarterly Journal of Economics",
    "Journal of Political Economy",
    "Journal of Political Economy Macroeconomics",
    "Review of Economic Studies",
    "Econometrica",
    "Review of Economics and Statistics",
    "American Economic Journal: Applied Economics",
    "American Economic Journal: Economic Policy",
    "American Economic Journal: Macroeconomics",
    "Journal of the European Economic Association",
    "Economic Journal",
]

# T2 领域刊
TIER2 = [
    "Journal of Labor Economics",
    "Journal of Human Resources",
    "Labour Economics",
    "ILR Review",
    "Industrial and Labor Relations Review",
    "Journal of Public Economics",
    "Journal of Econometrics",
    "Management Science",
    "Journal of Economic Behavior and Organization",
    "Journal of Economic Behavior & Organization",
    "European Economic Review",
    "Journal of Population Economics",
    "Demography",
    "Journal of Development Economics",
    "China Economic Review",
    "Journal of Comparative Economics",
    "Oxford Bulletin of Economics and Statistics",
    "Scandinavian Journal of Economics",
    "Journal of Economic Perspectives",
    "Brookings Papers on Economic Activity",
    "World Development",
    "Journal of Economic Growth",
    "Journal of Health Economics",
    "Journal of Urban Economics",
    "Regional Science and Urban Economics",
    "Economics of Education Review",
    "Journal of Economic Inequality",
    "Industrial Relations",
    "British Journal of Industrial Relations",
    "Work, Employment and Society",
]

# T3 工作论文系列（按子串匹配）
TIER3_SUBSTR = [
    "nber", "iza", "cepr", "ssrn", "arxiv", "cesifo",
    "federal reserve", "world bank policy research", "oecd",
]

LOW_LABEL = "low_priority"


def _norm(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\([^)]*\)", " ", s)          # 去掉括号注释
    s = s.replace("&", " and ")
    s = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def _tokens(s: str):
    return _norm(s).split()


def _contains_seq(hay, needle) -> bool:
    """needle 的每个词必须作为独立词、连续出现在 hay 中。

    避免 'iza' 命中 'organization' 这类子串误判。
    """
    if not needle:
        return False
    n = len(needle)
    for i in range(len(hay) - n + 1):
        if hay[i:i + n] == needle:
            return True
    return False


_T1 = [_tokens(x) for x in TIER1]
_T2 = [_tokens(x) for x in TIER2]
_T3 = [_tokens(x) for x in TIER3_SUBSTR]


def venue_tier(source: str) -> str:
    """返回 T1 / T2 / T3 / low_priority。"""
    hay = _tokens(source)
    if not hay:
        return LOW_LABEL
    if any(_contains_seq(hay, e) for e in _T1):
        return "T1"
    if any(_contains_seq(hay, e) for e in _T2):
        return "T2"
    if any(_contains_seq(hay, e) for e in _T3):
        return "T3"
    return LOW_LABEL


_RANK = {"T1": 0, "T2": 1, "T3": 2, LOW_LABEL: 3}
_LABEL = {
    "T1": "顶刊·优先看",
    "T2": "领域刊·值得看",
    "T3": "工作论文·快速扫",
    LOW_LABEL: "其他来源·可略过",
}


# 劳动/人口/教育类专刊：本领域的论文默认相关，不再看标题
LABOR_VENUES = [
    "Journal of Labor Economics",
    "Journal of Human Resources",
    "Labour Economics",
    "ILR Review",
    "Industrial and Labor Relations Review",
    "Industrial Relations",
    "British Journal of Industrial Relations",
    "Work, Employment and Society",
    "Journal of Population Economics",
    "Demography",
    "Economics of Education Review",
    "Journal of Economic Inequality",
]

_LABOR = [_tokens(x) for x in LABOR_VENUES]


def is_labor_venue(source: str) -> bool:
    """是否为劳动经济学专刊。"""
    hay = _tokens(source)
    return any(_contains_seq(hay, e) for e in _LABOR)


def label(tier: str) -> str:
    return _LABEL.get(tier, tier)


def rank(tier: str) -> int:
    return _RANK.get(tier, 9)

# -*- coding: utf-8 -*-
"""标题级相关性初筛：命中劳动经济学词表才进入人工审核。"""
import csv
import os
import re

from .normalize import normalize_title

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BASE_TERMS = [
    "labor", "labour", "wage", "wages", "employment", "unemployment", "employer",
    "employee", "worker", "workers", "job", "jobs", "earnings", "hiring", "hire",
    "skill", "skills", "occupation", "occupational", "migration", "immigrant",
    "immigration", "migrant", "firm", "firms", "payroll", "union", "discrimination",
    "human capital", "education", "schooling", "school", "pension", "retirement",
    "childcare", "fertility", "gender", "age", "minimum wage", "monopsony",
    "automation", "artificial intelligence", "ai", "robot", "task", "commute",
    "self-employment", "informal", "inequality", "mobility", "return migration",
    # 中文词表：否则中文标题会全部判为 off_topic
    "劳动力", "劳动", "工资", "就业", "失业", "雇佣", "雇员", "雇主", "招聘",
    "技能", "职业", "收入", "不平等", "人力资本", "教育", "学校", "培训",
    "迁移", "移民", "流动", "回流", "性别", "年龄", "歧视", "生育", "育儿",
    "退休", "养老", "企业", "工会", "最低工资", "自动化", "人工智能", "算法",
    "平台", "零工", "通勤", "户籍", "断点回归", "教育回报",
]


def load_keywords():
    terms = list(BASE_TERMS)
    p = os.path.join(ROOT, "data", "topics.csv")
    if os.path.exists(p):
        with open(p, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                for k in (row.get("keywords") or "").split(";"):
                    k = k.strip()
                    if k:
                        terms.append(k)
    return sorted({t.lower() for t in terms})


def score(title: str, terms=None) -> int:
    """返回命中的不同关键词个数。"""
    terms = terms or load_keywords()
    t = normalize_title(title)
    if not t:
        return 0
    hits = 0
    for term in terms:
        if re.search(r"(?<![a-z])" + re.escape(term) + r"(?![a-z])", t):
            hits += 1
    return hits


CORE_TERMS = {
    "labor", "labour", "wage", "wages", "employment", "unemployment", "employer",
    "employee", "worker", "workers", "earnings", "hiring", "minimum wage",
    "monopsony", "human capital", "return migration", "劳动力", "劳动", "工资",
    "就业", "失业", "雇佣", "招聘", "人力资本", "最低工资",
}


def classify(title: str, terms=None) -> str:
    """核心词命中，或一般词命中 >=2 个，才算相关。"""
    t = normalize_title(title)
    if not t:
        return "off_topic"
    terms = terms or load_keywords()
    core = 0
    total = 0
    for term in terms:
        if re.search(r"(?<![a-z])" + re.escape(term) + r"(?![a-z])", t):
            total += 1
            if term in CORE_TERMS:
                core += 1
    if core >= 1 or total >= 2:
        return "relevant"
    return "off_topic"

# -*- coding: utf-8 -*-
"""从 data/*.csv 生成 MkDocs 页面。只读数据，不改主表。"""
import csv
import datetime
import hashlib
import html
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
DOCS = os.path.join(ROOT, "docs")
TODAY = datetime.date.today()


def load(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def esc(s):
    return html.escape((s or "").strip())


def pid(c):
    mid = (c.get("matched_paper_id") or "").strip()
    if mid:
        return mid
    h = hashlib.md5((c.get("title") or "").encode("utf-8")).hexdigest()[:6].upper()
    return "C-" + h


def tier_cls(t):
    return {"T1": "tier-1", "T2": "tier-2", "T3": "tier-3"}.get(t, "tier-low")


def card(c):
    t = esc(c.get("title"))
    src = esc(c.get("source"))[:60]
    date = esc(c.get("publication_date"))
    tier = esc(c.get("venue_tier"))
    cls = tier_cls(tier)
    url = (c.get("url") or "").strip()
    body = (
        '<span class="t">%s</span>'
        '<span class="m"><span class="tier %s">%s</span>%s &middot; %s</span>'
        % (t, cls, tier if tier else "&mdash;", src, date)
    )
    if url:
        return '<a class="paper" href="%s" target="_blank" rel="noopener">%s</a>' % (esc(url), body)
    return '<div class="paper">%s</div>' % body


def _neg(d):
    digits = "".join(ch for ch in (d or "") if ch.isdigit())
    return -int(digits[:8]) if len(digits) >= 8 else 99999999


def top(cands, n=12, tiers=("T1", "T2")):
    pick = [c for c in cands if c.get("venue_tier") in tiers]
    pick.sort(key=lambda c: (c.get("venue_tier") != "T1", _neg(c.get("publication_date"))))
    return pick[:n]


def write(path, text):
    full = os.path.join(DOCS, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)


def assign_topics(c, topics):
    title = (c.get("title") or "").lower()
    hits = []
    for t in topics:
        if t.get("active", "1") != "1":
            continue
        kws = [k.strip().lower() for k in (t.get("keywords") or "").split(";") if k.strip()]
        if any(k in title for k in kws):
            hits.append(t)
    return hits


def build_index(cands, topics):
    n_t1 = sum(1 for c in cands if c.get("venue_tier") == "T1")
    n_t2 = sum(1 for c in cands if c.get("venue_tier") == "T2")
    n_venues = len({c.get("source") for c in cands if c.get("source")})
    n_l2 = len({t["topic_l2"] for t in topics})

    parts = [
        '<div class="hero" markdown>',
        '<p class="hero-kicker">Labor Economics Monitor</p>',
        "",
        "# 劳动经济学研究监测",
        "",
        '<p class="hero-sub">每周从 %d 个期刊源与 NBER 工作论文中自动抓取，'
        "用期刊分级与标题词表做初筛，再由人工分 A / B / C 三档。"
        "目标不是覆盖全部文献，而是让你在 20 分钟内决定这周读哪三篇。</p>" % n_venues,
        "",
        '<div class="hero-stats">',
        '<div class="stat"><span class="num">%d</span><span class="lab">待审论文</span></div>' % len(cands),
        '<div class="stat"><span class="num">%d</span><span class="lab">顶刊 T1</span></div>' % n_t1,
        '<div class="stat"><span class="num">%d</span><span class="lab">领域刊 T2</span></div>' % n_t2,
        '<div class="stat"><span class="num">%d</span><span class="lab">二级主题</span></div>' % n_l2,
        "</div>",
        "</div>",
        "",
        "## 本周精选",
        "",
        '<div class="paper-list">',
    ]
    for c in top(cands, 12):
        parts.append(card(c))
    parts += [
        "</div>",
        "",
        "[查看全部待审论文](papers/index.md){ .md-button }",
        "",
        "## 按主题浏览",
        "",
        '<div class="topic-grid">',
    ]
    counts = {}
    for c in cands:
        for t in assign_topics(c, topics):
            counts[t["topic_l2_name"]] = counts.get(t["topic_l2_name"], 0) + 1
    for name, n in sorted(counts.items(), key=lambda kv: -kv[1])[:8]:
        parts.append(
            '<div class="topic-card"><div class="name">%s</div>'
            '<div class="count">%d 篇</div></div>' % (esc(name), n)
        )
    parts += ["</div>", "", "[全部主题](topics/index.md){ .md-button }"]
    write("index.md", "\n".join(parts) + "\n")


def build_papers(cands):
    rows = ["| 档位 | 标题 | 来源 | 日期 |", "| --- | --- | --- | --- |"]
    for c in cands:
        title = esc(c.get("title")).replace("|", "/")
        rows.append("| %s | [%s](%s.md) | %s | %s |" % (
            esc(c.get("venue_tier")) or "&mdash;", title, pid(c),
            esc(c.get("source"))[:40], esc(c.get("publication_date"))))
    write("papers/index.md", "# 论文库\n\n共 %d 篇待审，按档位排序。\n\n%s\n"
          % (len(cands), "\n".join(rows)))

    for c in cands:
        t = esc(c.get("title"))
        authors = esc(c.get("authors")).replace(";", "、") or "&mdash;"
        lines = [
            "---",
            'title: "%s"' % t.replace('"', "'"),
            "---",
            "",
            "# %s" % t,
            "",
            "| 项目 | 内容 |",
            "| --- | --- |",
            "| 编号 | %s |" % pid(c),
            "| 来源 | %s |" % esc(c.get("source")),
            "| 档位 | %s |" % (esc(c.get("venue_tier")) or "&mdash;"),
            "| 日期 | %s |" % esc(c.get("publication_date")),
            "| 作者 | %s |" % authors,
            "| 链接 | %s |" % (esc(c.get("url")) or "&mdash;"),
            "",
            "## 待填",
            "",
            "- [ ] 研究问题",
            "- [ ] 识别策略",
            "- [ ] 主要结果",
            "- [ ] 与我们研究的关系",
            "",
        ]
        write("papers/%s.md" % pid(c), "\n".join(lines))


def build_topics(cands, topics):
    groups = {}
    for t in topics:
        if t.get("active", "1") != "1":
            continue
        groups.setdefault((t["topic_l1"], t["topic_l1_name"]), []).append(t)

    out = ["# 主题", "", "按研究主题归档，每篇论文可归入多个主题。", ""]
    for (l1, l1name), subs in sorted(groups.items()):
        out += ["## %s %s" % (l1, esc(l1name)), "",
                "| 二级主题 | 关键词 | 命中 |", "| --- | --- | --- |"]
        for s in subs:
            hits = sum(1 for c in cands if s in assign_topics(c, topics))
            out.append("| %s %s | %s | %d |" % (
                s["topic_l2"], esc(s["topic_l2_name"]),
                esc(s.get("keywords", ""))[:46], hits))
        out.append("")
    write("topics/index.md", "\n".join(out))


def build_weekly(cands):
    iso = TODAY.isocalendar()
    week = "%d-W%02d" % (iso[0], iso[1])
    lines = [
        "# %s 周报" % week,
        "",
        "抓取日期：%s ・ 待审 %d 篇" % (TODAY.isoformat(), len(cands)),
        "",
        "## 本周八篇",
        "",
        '<div class="paper-list">',
    ]
    for c in top(cands, 8):
        lines.append(card(c))
    lines += ["</div>", "", "## 本周判断", "",
              "- **值得精读**：", "- **只需知道结论**：", "- **可以跳过**：", ""]
    write("weekly/%s.md" % week, "\n".join(lines))
    write("weekly/index.md",
          "# 本周精选\n\n每期从待审论文里挑出最值得读的几篇。\n\n"
          "- [%s](%s.md) — 待审 %d 篇\n" % (week, week, len(cands)))


def build_changelog():
    logs = load("weekly_log.csv")
    lines = ["# 更新日志", "",
             "| 周 | 抓取日 | 候选 | 已审 | 发布 |",
             "| --- | --- | --- | --- | --- |"]
    for r in logs:
        lines.append("| %s | %s | %s | %s | %s |" % (
            r.get("week_id", ""), r.get("fetch_date", ""), r.get("candidates_count", ""),
            r.get("reviewed_count", ""), r.get("published_count", "")))
    lines += ["", "## 管线变更", "",
              "- 2026-11-15 抓取源改为 Crossref 按 ISSN 逐刊抓取（42 本），新增期刊分级与相关性初筛",
              "- 2026-11-14 建立 schema：study_id 挂研究层、paper_id 挂版本层", ""]
    write("changelog.md", "\n".join(lines))


def main():
    cands = [c for c in load("candidates.csv") if c.get("decision") != "off_topic"]
    topics = load("topics.csv")
    build_index(cands, topics)
    build_papers(cands)
    build_topics(cands, topics)
    build_weekly(cands)
    build_changelog()
    print("generated: %d papers, %d topics" % (len(cands), len(topics)))


if __name__ == "__main__":
    main()

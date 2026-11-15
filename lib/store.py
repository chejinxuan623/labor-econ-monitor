# -*- coding: utf-8 -*-
"""CSV 读写：原子写入、自动备份、保护人工确认记录、幂等追加。"""
import csv
import os
import shutil
import tempfile
import datetime

DATA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")


def path_of(table: str) -> str:
    return os.path.join(DATA, table + ".csv")


def load(table: str):
    p = path_of(table)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def fields_of(table: str):
    p = path_of(table)
    with open(p, encoding="utf-8-sig", newline="") as f:
        return next(csv.reader(f))


def backup(table: str) -> str:
    """写入前备份，返回备份路径。"""
    src = path_of(table)
    if not os.path.exists(src):
        return ""
    d = os.path.join(DATA, "backup", datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    os.makedirs(d, exist_ok=True)
    dst = os.path.join(d, table + ".csv")
    shutil.copy2(src, dst)
    return dst


def save_atomic(table: str, rows, fields=None):
    """先写临时文件再替换，避免中途失败把原文件写坏。"""
    fields = fields or fields_of(table)
    for row in rows:
        missing = [k for k in fields if k not in row]
        if missing:
            raise ValueError("行缺少字段 %s，拒绝写入" % missing)
    backup(table)
    fd, tmp = tempfile.mkstemp(dir=DATA, suffix=".tmp")
    os.close(fd)
    try:
        with open(tmp, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, path_of(table))
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def append_idempotent(table: str, new_rows, key: str):
    """按 key 判重追加；已存在的跳过，绝不覆盖。返回实际新增数。"""
    rows = load(table)
    fields = fields_of(table)
    seen = {r[key] for r in rows}
    added = 0
    for r in new_rows:
        if r.get(key) in seen:
            continue
        full = {k: r.get(k, "") for k in fields}
        rows.append(full)
        seen.add(r.get(key))
        added += 1
    if added:
        save_atomic(table, rows)
    return added


def protect_manual(table: str):
    """占位：人工确认的记录由调用方保证不被改写。

    约定：match_status == '人工确认' 的记录，任何自动流程都不得修改其 study_id。
    """
    return [r for r in load(table) if r.get("match_status") == "人工确认"]

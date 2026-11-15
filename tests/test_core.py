# -*- coding: utf-8 -*-
"""Package 2 核心测试：7 条，覆盖中文、去重、版本、防覆盖、幂等。"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from lib.normalize import normalize_title, main_title          # noqa: E402
from lib.dedup import compare, find_match                       # noqa: E402
import lib.store as store                                       # noqa: E402


class TestNormalize(unittest.TestCase):
    def test_chinese_not_empty(self):
        t = normalize_title("年龄歧视导致了失业：一个断点回归设计")
        self.assertTrue(t)
        self.assertIn("年龄歧视", t)

    def test_english_articles_stripped(self):
        self.assertEqual(normalize_title("The Impact of AI"), "impact of ai")

    def test_subtitle_kept_in_main_normalization(self):
        t = normalize_title("The Impact of AI: Evidence from China")
        self.assertIn("evidence from china", t)

    def test_main_title_helper(self):
        self.assertEqual(main_title("The Impact of AI: Evidence from China"), "impact of ai")


class TestDedup(unittest.TestCase):
    def test_same_doi(self):
        a = {"doi": "10.1/abc", "title": "X", "authors": []}
        b = {"doi": "10.1/ABC ", "title": "Y", "authors": []}
        self.assertEqual(compare(a, b)["status"], "confirmed_same")

    def test_similar_title_different_authors_not_merged(self):
        a = {"doi": "", "title": "The Impact of AI on Employment", "authors": ["Alice Zhang"]}
        b = {"doi": "", "title": "The Impact of AI on Employment", "authors": ["Bob Li"]}
        self.assertEqual(compare(a, b)["status"], "independent")

    def test_similar_title_same_author_possible(self):
        a = {"doi": "", "title": "The Impact of AI on Employment", "authors": ["Alice Zhang"]}
        b = {"doi": "", "title": "The Impact of AI on Employment", "authors": ["alice  zhang"]}
        self.assertEqual(compare(a, b)["status"], "possible_match")

    def test_chinese_pair_not_false_positive(self):
        a = {"doi": "", "title": "人工智能如何改变企业对劳动力的需求", "authors": ["陈琳"]}
        b = {"doi": "", "title": "年龄歧视导致了失业", "authors": ["林文炼"]}
        self.assertEqual(compare(a, b)["status"], "independent")

    def test_find_match_prefers_doi(self):
        pool = [{"doi": "10.9/z", "title": "Other", "authors": []}]
        r = find_match({"doi": "10.9/z", "title": "New", "authors": []}, pool)
        self.assertEqual(r["status"], "confirmed_same")


class TestStore(unittest.TestCase):
    def test_idempotent_append(self):
        rows = [{"study_id": "T-0001", "research_title": "A"}]
        fields = ["study_id", "research_title"]
        # 临时切到测试数据目录
        old = store.DATA
        store.DATA = os.path.join(ROOT, "tests", "_tmpdata")
        os.makedirs(store.DATA, exist_ok=True)
        try:
            with open(store.path_of("t"), "w", encoding="utf-8-sig", newline="") as f:
                f.write("study_id,research_title\n")
            self.assertEqual(store.append_idempotent("t", rows, "study_id"), 1)
            self.assertEqual(store.append_idempotent("t", rows, "study_id"), 0)
            self.assertEqual(len(store.load("t")), 1)
        finally:
            store.DATA = old

    def test_failed_write_keeps_old_file(self):
        old = store.DATA
        store.DATA = os.path.join(ROOT, "tests", "_tmpdata2")
        os.makedirs(store.DATA, exist_ok=True)
        try:
            p = store.path_of("t2")
            with open(p, "w", encoding="utf-8-sig", newline="") as f:
                f.write("study_id,research_title\nS-1,Keep\n")
            with self.assertRaises(Exception):
                store.save_atomic("t2", [{"bad": 1}], fields=["study_id"])  # 缺列 -> 报错
            with open(p, encoding="utf-8-sig") as f:
                self.assertIn("Keep", f.read())
        finally:
            store.DATA = old


if __name__ == "__main__":
    unittest.main(verbosity=2)

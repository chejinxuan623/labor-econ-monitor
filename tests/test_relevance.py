# -*- coding: utf-8 -*-
"""相关性初筛测试。"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from lib.relevance import classify, score  # noqa: E402


class TestRelevance(unittest.TestCase):
    def test_labor_title_relevant(self):
        self.assertEqual(classify("The Impact of Minimum Wage on Employment"), "relevant")

    def test_chinese_labor_title_relevant(self):
        self.assertEqual(classify("人工智能如何改变企业对劳动力的需求"), "relevant")

    def test_macro_title_off_topic(self):
        self.assertEqual(classify("Unconventional Monetary Policy and Default"), "off_topic")

    def test_score_counts_distinct_terms(self):
        s = score("Wage inequality and employment")
        self.assertGreaterEqual(s, 2)

    def test_empty_title_off_topic(self):
        self.assertEqual(classify(""), "off_topic")


if __name__ == "__main__":
    unittest.main()

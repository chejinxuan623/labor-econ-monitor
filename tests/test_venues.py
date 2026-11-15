# -*- coding: utf-8 -*-
"""期刊分级测试。"""
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from lib.venues import label, rank, venue_tier  # noqa: E402


class TestVenues(unittest.TestCase):
    def test_top5_is_t1(self):
        self.assertEqual(venue_tier("Quarterly Journal of Economics"), "T1")
        self.assertEqual(venue_tier("American Economic Review"), "T1")

    def test_field_journal_is_t2(self):
        self.assertEqual(venue_tier("Journal of Labor Economics"), "T2")
        self.assertEqual(venue_tier("Journal of Human Resources"), "T2")

    def test_working_paper_series_is_t3(self):
        self.assertEqual(venue_tier("NBER Working Paper"), "T3")
        self.assertEqual(venue_tier("IZA Discussion Paper"), "T3")

    def test_obscure_journal_is_low(self):
        self.assertEqual(venue_tier("World Journal of Advanced Research"), "low_priority")
        self.assertEqual(venue_tier("Frontiers in Sustainable Food Systems"), "low_priority")

    def test_ampersand_and_parens_normalized(self):
        self.assertEqual(venue_tier("Journal of Economic Behavior & Organization"), "T2")
        self.assertEqual(venue_tier("Quarterly Journal of Economics (QJE)"), "T1")

    def test_iza_substring_not_matched_inside_word(self):
        # 回归：'iza' 曾误命中 'Organization'
        self.assertEqual(venue_tier("Frontiers in Organization Studies"), "low_priority")

    def test_journal_with_subtitle_matches(self):
        # 回归：'Industrial Relations: A Journal of Economy and Society'
        self.assertEqual(
            venue_tier("Industrial Relations: A Journal of Economy and Society"), "T2")

    def test_empty_source_is_low(self):
        self.assertEqual(venue_tier(""), "low_priority")

    def test_rank_orders_tiers(self):
        self.assertLess(rank("T1"), rank("T2"))
        self.assertLess(rank("T2"), rank("T3"))
        self.assertLess(rank("T3"), rank("low_priority"))

    def test_labels_present(self):
        for t in ("T1", "T2", "T3", "low_priority"):
            self.assertTrue(label(t))


if __name__ == "__main__":
    unittest.main()

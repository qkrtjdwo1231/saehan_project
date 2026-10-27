# 품목 묶음(월말전표/청주생산/기타)과 수요 유형(A/B/C) 판정 규칙을 검증하는 테스트
import unittest

import pandas as pd

from pipeline.classify import item_group, demand_type


class ItemGroupTest(unittest.TestCase):
    def test_ambt_items_are_month_end_group(self):
        self.assertEqual(item_group("AMBT366", produced={"TM00663"}), "월말전표")

    def test_items_with_production_record_are_cheongju(self):
        self.assertEqual(item_group("TM00663", produced={"TM00663"}), "청주생산")

    def test_other_items_without_production_are_etc(self):
        self.assertEqual(item_group("AMCP029", produced={"TM00663"}), "기타")


class DemandTypeTest(unittest.TestCase):
    def test_weekly_item_is_type_a(self):
        weekly = pd.Series([10, 12, 0, 9, 11, 10, 8, 0, 10, 12])  # 80% of weeks shipped
        self.assertEqual(demand_type(weekly), "A")

    def test_lumpy_item_is_type_b(self):
        weekly = pd.Series([0, 50, 0, 0, 60, 0, 0, 0, 55, 0])  # 30% of weeks shipped
        self.assertEqual(demand_type(weekly), "B")

    def test_rare_item_is_type_c(self):
        weekly = pd.Series([0] * 19 + [300])  # 5% of weeks shipped
        self.assertEqual(demand_type(weekly), "C")

    def test_no_shipments_is_type_c(self):
        self.assertEqual(demand_type(pd.Series([0, 0, 0])), "C")


if __name__ == "__main__":
    unittest.main()

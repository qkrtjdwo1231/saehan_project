# 주 단위 집계(월요일 시작)와 1공장 중단 구간 플래그를 검증하는 테스트
import unittest

import pandas as pd

from pipeline.aggregate import weekly_by_type_customer, plant1_outage


class WeeklyAggregateTest(unittest.TestCase):
    def setUp(self):
        self.daily = pd.DataFrame({
            "date": pd.to_datetime(["2025-01-06", "2025-01-08", "2025-01-12", "2025-01-13"]),  # 월, 수, 일, 다음 월
            "item_type": ["T1", "T1", "T1", "T1"],
            "customer": ["대상", "대상", "대상", "대상"],
            "qty": [100, 200, 300, 400],
        })

    def test_sunday_belongs_to_week_starting_previous_monday(self):
        weekly = weekly_by_type_customer(self.daily)
        first = weekly[weekly["week_start"] == pd.Timestamp("2025-01-06")]
        self.assertEqual(int(first["qty"].iloc[0]), 600)

    def test_total_quantity_is_preserved(self):
        weekly = weekly_by_type_customer(self.daily)
        self.assertEqual(int(weekly["qty"].sum()), 1000)
        self.assertEqual(len(weekly), 2)


class Plant1OutageTest(unittest.TestCase):
    def test_flags_only_window_between_fire_and_restart(self):
        dates = pd.to_datetime(["2024-07-07", "2024-07-08", "2024-12-31", "2025-01-31", "2025-02-01"])
        flags = plant1_outage(dates)
        self.assertEqual(list(flags), [False, True, True, True, False])


if __name__ == "__main__":
    unittest.main()

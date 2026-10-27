# 설·추석 연휴 달력과 주 단위 플래그(연휴 주, 연휴 전 주)를 검증하는 테스트
import unittest

import pandas as pd

from pipeline.forecast.calendar import week_flags


class WeekFlagsTest(unittest.TestCase):
    def test_week_containing_lunar_new_year_2025_is_holiday_week(self):
        weeks = pd.to_datetime(["2025-01-13", "2025-01-20", "2025-01-27", "2025-02-03"])  # 월요일들
        flags = week_flags(weeks).set_index("week_start")
        self.assertEqual(list(flags["holiday_week"]), [False, False, True, False])
        self.assertEqual(list(flags["pre_holiday_week"]), [False, True, False, False])

    def test_chuseok_2023_spanning_two_weeks_flags_both(self):
        weeks = pd.to_datetime(["2023-09-18", "2023-09-25", "2023-10-02", "2023-10-09"])
        flags = week_flags(weeks).set_index("week_start")
        self.assertEqual(list(flags["holiday_week"]), [False, True, True, False])
        self.assertEqual(list(flags["pre_holiday_week"]), [True, False, False, False])


if __name__ == "__main__":
    unittest.main()

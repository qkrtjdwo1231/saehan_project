# 외부 변수 보정(월별 계절지수, 연휴 계수, 보정 래퍼)을 검증하는 테스트
import unittest

import numpy as np
import pandas as pd

from pipeline.forecast.adjust import monthly_index, flag_factors, with_factors, deseasonalized


class MonthlyIndexTest(unittest.TestCase):
    def test_index_is_month_mean_over_overall_mean(self):
        weeks = pd.date_range("2024-01-01", periods=10, freq="W-MON")  # 1월 5주, 2월 4주, 3월 1주
        totals = pd.Series([10.0] * 5 + [30.0] * 4 + [20.0], index=weeks)
        idx = monthly_index(totals)
        overall = totals.mean()
        self.assertAlmostEqual(idx[1], 10.0 / overall)
        self.assertAlmostEqual(idx[2], 30.0 / overall)

    def test_missing_month_defaults_to_one(self):
        weeks = pd.date_range("2024-01-01", periods=4, freq="W-MON")
        idx = monthly_index(pd.Series([5.0] * 4, index=weeks))
        self.assertEqual(idx[7], 1.0)


class FlagFactorsTest(unittest.TestCase):
    def test_factor_is_ratio_of_flagged_to_unflagged_mean(self):
        weeks = pd.date_range("2024-01-01", periods=6, freq="W-MON")
        totals = pd.Series([10.0, 10.0, 10.0, 10.0, 15.0, 5.0], index=weeks)
        flags = pd.DataFrame({"week_start": weeks, "pre_holiday_week": [False] * 4 + [True, False],
                              "holiday_week": [False] * 5 + [True]})
        f = flag_factors(totals, flags)
        self.assertAlmostEqual(f["pre_holiday_week"], 1.5)
        self.assertAlmostEqual(f["holiday_week"], 0.5)


class WithFactorsTest(unittest.TestCase):
    def test_multiplies_base_forecast_by_target_week_factor(self):
        weeks = list(pd.date_range("2024-01-01", periods=6, freq="W-MON"))
        factor_by_week = pd.Series([1.0, 1.0, 1.0, 2.0, 1.0, 0.5], index=weeks)
        base = lambda history, h, valid: 100.0
        model = with_factors(base, factor_by_week)
        history = np.ones(3)  # 마지막 관측 = 인덱스 2 → h=1의 목표 주 = 인덱스 3 (계수 2.0)
        self.assertAlmostEqual(model(history, 1, np.ones(3, dtype=bool)), 200.0)
        self.assertAlmostEqual(model(history, 3, np.ones(3, dtype=bool)), 50.0)


class DeseasonalizedTest(unittest.TestCase):
    def test_divides_history_by_week_factors_before_base_model(self):
        weeks = list(pd.date_range("2024-01-01", periods=4, freq="W-MON"))
        factor_by_week = pd.Series([2.0, 2.0, 0.5, 1.0], index=weeks)
        seen = {}
        def base(history, h, valid):
            seen["history"] = list(history)
            return 1.0
        model = deseasonalized(base, factor_by_week)
        model(np.array([20.0, 40.0, 5.0]), 1, np.ones(3, dtype=bool))
        self.assertEqual(seen["history"], [10.0, 20.0, 10.0])


if __name__ == "__main__":
    unittest.main()

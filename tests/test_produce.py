# 최신 시점 기준 4주 예측과 화면용 데이터(JSON)를 만드는 produce 모듈을 검증하는 테스트
import unittest

import numpy as np
import pandas as pd

from pipeline.forecast.produce import produce


def make_weekly():
    weeks = pd.date_range("2021-01-04", "2025-12-29", freq="W-MON")
    rows = []
    for w in weeks:
        rows.append({"item_type": "T1", "customer": "대상", "week_start": w, "qty": 100 + (10 if w.month in (5, 6, 7) else 0)})
        if w.weekofyear % 4 == 0:
            rows.append({"item_type": "T2", "customer": "롯데", "week_start": w, "qty": 400})
    return pd.DataFrame(rows)


class ProduceTest(unittest.TestCase):
    def setUp(self):
        self.weekly = make_weekly()
        self.items = pd.DataFrame({"item_code": ["A1", "B1"], "item_type": ["T1", "T2"], "item_name": ["간장 500", "미림 1.8L"],
                                   "group": ["청주생산", "청주생산"], "main_dept": [1219, 1219], "main_customer": ["대상", "롯데"],
                                   "demand_type": ["A", "B"], "qty_2025": [5200, 5200]})

    def test_forecasts_four_weeks_after_last_data_week(self):
        out = produce(self.weekly, self.items)
        self.assertEqual(out["as_of"], "2025-12-29")
        self.assertEqual(out["forecast_weeks"], ["2026-01-05", "2026-01-12", "2026-01-19", "2026-01-26"])
        s = {r["series"]: r for r in out["series"]}
        self.assertEqual(len(s["T1|대상"]["forecast"]), 4)
        self.assertAlmostEqual(s["T1|대상"]["forecast_4w"], sum(s["T1|대상"]["forecast"]), places=3)
        self.assertEqual(s["T1|대상"]["demand_type"], "A")
        self.assertEqual(s["T2|롯데"]["demand_type"], "B")

    def test_totals_equal_sum_of_series(self):
        out = produce(self.weekly, self.items)
        total_pred = np.array(out["totals"]["forecast"])
        series_sum = np.sum([r["forecast"] for r in out["series"]], axis=0)
        np.testing.assert_allclose(total_pred, series_sum, rtol=1e-6)
        self.assertEqual(len(out["totals"]["recent_weeks"]), 12)

    def test_steady_series_forecast_is_near_recent_level(self):
        out = produce(self.weekly, self.items)
        s = {r["series"]: r for r in out["series"]}
        self.assertTrue(80 <= s["T1|대상"]["forecast"][0] <= 120)


if __name__ == "__main__":
    unittest.main()

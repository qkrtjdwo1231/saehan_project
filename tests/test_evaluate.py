# 검증 결과를 모델×예측구간×수요유형별 점수표로 요약하는 함수를 검증하는 테스트
import unittest

import pandas as pd

from pipeline.forecast.evaluate import summarize, series_matrix


class SummarizeTest(unittest.TestCase):
    def test_scores_grouped_by_model_horizon_and_type(self):
        result = pd.DataFrame({
            "series": ["S1", "S1", "S2", "S2"],
            "horizon": [1, 1, 1, 1],
            "actual": [100, 100, 0, 50],
            "pred": [90, 120, 10, 50],
            "model": ["ma8", "snaive", "ma8", "snaive"],
        })
        types = pd.Series({"S1": "A", "S2": "B"})
        table = summarize(result, types)
        ma8_a = table[(table["model"] == "ma8") & (table["horizon"] == 1) & (table["demand_type"] == "A")].iloc[0]
        self.assertAlmostEqual(ma8_a["wape"], 0.1)
        snaive_all = table[(table["model"] == "snaive") & (table["horizon"] == 1) & (table["demand_type"] == "전체")].iloc[0]
        self.assertAlmostEqual(snaive_all["wape"], 20 / 150)
        self.assertAlmostEqual(snaive_all["hit_rate"], 1.0)


class SeriesMatrixTest(unittest.TestCase):
    def test_builds_series_by_week_matrix_with_zero_fill(self):
        weekly = pd.DataFrame({
            "item_type": ["T1", "T1", "T2"],
            "customer": ["대상", "대상", "CJ"],
            "week_start": pd.to_datetime(["2025-01-06", "2025-01-20", "2025-01-13"]),
            "qty": [10, 30, 5],
        })
        m = series_matrix(weekly)
        self.assertEqual(m.shape, (2, 3))
        self.assertEqual(list(m.loc["T1|대상"]), [10, 0, 30])
        self.assertEqual(list(m.loc["T2|CJ"]), [0, 5, 0])


if __name__ == "__main__":
    unittest.main()

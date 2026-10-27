# 예측 점수(물량 가중 오차율 WAPE, 출고 유무 적중률)를 검증하는 테스트
import unittest

import numpy as np

from pipeline.forecast.metrics import wape, hit_rate


class WapeTest(unittest.TestCase):
    def test_perfect_forecast_is_zero(self):
        self.assertEqual(wape(np.array([10, 20, 0]), np.array([10, 20, 0])), 0.0)

    def test_weights_errors_by_actual_volume(self):
        # 오차 합 = |10-15| + |90-80| = 15, 실제 합 = 100 → 0.15
        self.assertAlmostEqual(wape(np.array([10, 90]), np.array([15, 80])), 0.15)

    def test_all_zero_actuals_returns_nan(self):
        self.assertTrue(np.isnan(wape(np.array([0, 0]), np.array([1, 0]))))


class HitRateTest(unittest.TestCase):
    def test_counts_weeks_where_shipment_presence_is_predicted_correctly(self):
        actual = np.array([0, 50, 0, 60])
        pred = np.array([0, 40, 10, 0])  # 맞음, 맞음, 틀림, 틀림
        self.assertAlmostEqual(hit_rate(actual, pred), 0.5)


if __name__ == "__main__":
    unittest.main()

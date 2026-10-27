# 기준선 예측(최근 8주 평균, 작년 같은 주)을 검증하는 테스트
import unittest

import numpy as np

from pipeline.forecast.baselines import moving_average, seasonal_naive


class MovingAverageTest(unittest.TestCase):
    def test_averages_last_eight_weeks(self):
        history = np.arange(1, 21, dtype=float)  # 1..20
        self.assertAlmostEqual(moving_average(history), np.mean(np.arange(13, 21)))

    def test_ignores_masked_weeks(self):
        history = np.array([10, 10, 10, 10, 10, 10, 10, 10, 1000, 1000], dtype=float)
        valid = np.array([True] * 8 + [False, False])
        self.assertAlmostEqual(moving_average(history, valid), 10.0)

    def test_short_history_uses_what_exists(self):
        self.assertAlmostEqual(moving_average(np.array([4.0, 6.0])), 5.0)


class SeasonalNaiveTest(unittest.TestCase):
    def test_returns_value_from_52_weeks_before_target(self):
        history = np.zeros(60)
        history[8] = 77  # 목표 주(인덱스 60)의 52주 전 = 인덱스 8
        self.assertEqual(seasonal_naive(history, horizon=1), 77)

    def test_horizon_shifts_target_week(self):
        history = np.zeros(60)
        history[10] = 55  # 목표 주 인덱스 62 (h=3) - 52 = 10
        self.assertEqual(seasonal_naive(history, horizon=3), 55)

    def test_falls_back_to_moving_average_when_reference_week_is_masked(self):
        history = np.full(60, 20.0)
        history[8] = 999
        valid = np.ones(60, dtype=bool)
        valid[8] = False
        self.assertAlmostEqual(seasonal_naive(history, horizon=1, valid=valid), 20.0)


if __name__ == "__main__":
    unittest.main()

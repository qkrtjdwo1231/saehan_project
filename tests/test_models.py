# 예측 모델(지수평활 SES, 간헐 수요 TSB)의 동작을 검증하는 테스트
import unittest

import numpy as np

from pipeline.forecast.models import ses, tsb


class SesTest(unittest.TestCase):
    def test_constant_series_returns_constant(self):
        self.assertAlmostEqual(ses(np.full(20, 10.0)), 10.0)

    def test_recent_values_weigh_more_than_old(self):
        history = np.array([100.0] * 10 + [10.0] * 10)
        self.assertLess(ses(history), 20.0)

    def test_ignores_masked_weeks(self):
        history = np.array([10.0] * 10 + [999.0, 999.0])
        valid = np.array([True] * 10 + [False, False])
        self.assertAlmostEqual(ses(history, valid=valid), 10.0)

    def test_empty_history_returns_zero(self):
        self.assertEqual(ses(np.array([])), 0.0)


class TsbTest(unittest.TestCase):
    def test_all_zero_history_returns_zero(self):
        self.assertEqual(tsb(np.zeros(10)), 0.0)

    def test_every_week_shipment_returns_lot_size(self):
        self.assertAlmostEqual(tsb(np.full(20, 50.0)), 50.0)

    def test_shipment_every_other_week_returns_about_half_lot(self):
        history = np.array([0.0, 40.0] * 20)
        f = tsb(history)
        self.assertGreater(f, 10.0)
        self.assertLess(f, 30.0)

    def test_ignores_masked_weeks(self):
        history = np.array([40.0] * 10 + [0.0] * 5)
        valid = np.array([True] * 10 + [False] * 5)
        self.assertAlmostEqual(tsb(history, valid=valid), 40.0)


if __name__ == "__main__":
    unittest.main()

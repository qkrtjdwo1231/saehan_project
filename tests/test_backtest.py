# walk-forward 검증 틀이 시점(origin)까지의 데이터만 쓰고 1~4주 앞을 평가하는지 검증하는 테스트
import unittest

import numpy as np
import pandas as pd

from pipeline.forecast.backtest import walk_forward


def last_value(history, horizon, valid):
    return history[-1]


class WalkForwardTest(unittest.TestCase):
    def setUp(self):
        weeks = pd.date_range("2024-12-02", periods=10, freq="W-MON")
        self.matrix = pd.DataFrame([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]], index=["S1"], columns=weeks, dtype=float)

    def test_prediction_uses_only_data_up_to_origin(self):
        result = walk_forward(self.matrix, {"last": last_value}, origins=[self.matrix.columns[5]], horizons=[1, 2])
        row_h1 = result[(result["horizon"] == 1)].iloc[0]
        row_h2 = result[(result["horizon"] == 2)].iloc[0]
        self.assertEqual(row_h1["pred"], 6)   # origin 값(인덱스 5)까지만 사용
        self.assertEqual(row_h1["actual"], 7)
        self.assertEqual(row_h2["actual"], 8)
        self.assertEqual(row_h2["pred"], 6)

    def test_skips_horizons_beyond_available_actuals(self):
        result = walk_forward(self.matrix, {"last": last_value}, origins=[self.matrix.columns[8]], horizons=[1, 2])
        self.assertEqual(list(result["horizon"]), [1])

    def test_passes_valid_mask_to_model(self):
        seen = {}
        def spy(history, horizon, valid):
            seen["valid"] = valid.copy()
            return 0.0
        valid = self.matrix.copy().astype(bool)
        valid.iloc[0, 3] = False
        walk_forward(self.matrix, {"spy": spy}, origins=[self.matrix.columns[5]], horizons=[1], valid=valid)
        self.assertEqual(list(seen["valid"]), [True, True, True, False, True, True])


if __name__ == "__main__":
    unittest.main()

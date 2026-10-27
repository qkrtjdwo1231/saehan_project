# 검증 결과를 네 가지 집계 수준(계열×주, 품종×주, 4주 합계, 총량)의 WAPE로 요약하는 함수를 검증하는 테스트
import unittest

import pandas as pd

from pipeline.forecast.evaluate import levels


class LevelsTest(unittest.TestCase):
    def test_reports_four_levels_per_model(self):
        result = pd.DataFrame({
            "series": ["T1|A", "T1|B", "T1|A", "T1|B"],
            "origin": ["o1"] * 4,
            "horizon": [1, 1, 2, 2],
            "target": ["w1", "w1", "w2", "w2"],
            "actual": [100, 0, 0, 100],
            "pred": [50, 50, 50, 50],
            "model": ["m"] * 4,
        })
        table = levels(result).set_index("level")
        self.assertAlmostEqual(table.loc["계열×주", "wape"], 1.0)        # h=1: |100-50|+|0-50| = 100 / 100
        self.assertAlmostEqual(table.loc["품종×주", "wape"], 0.0)        # 거래처 합산: 100 vs 100
        self.assertAlmostEqual(table.loc["총량", "wape"], 0.0)
        self.assertAlmostEqual(table.loc["계열×4주합", "wape"], 0.0)     # 계열별 h1+h2: 100 vs 100


if __name__ == "__main__":
    unittest.main()

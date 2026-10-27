# 일별 기온을 주(월요일 시작) 평균으로 집계하는 함수를 검증하는 테스트
import unittest

import pandas as pd

from pipeline.external.weather import weekly_temperature


class WeeklyTemperatureTest(unittest.TestCase):
    def test_averages_daily_temperature_by_week_start_monday(self):
        daily = pd.DataFrame({
            "date": pd.to_datetime(["2025-01-06", "2025-01-07", "2025-01-12", "2025-01-13"]),  # 월, 화, 일, 다음 월
            "temp_mean": [0.0, 2.0, 4.0, 10.0],
        })
        weekly = weekly_temperature(daily).set_index("week_start")
        self.assertAlmostEqual(weekly.loc[pd.Timestamp("2025-01-06"), "temp_mean"], 2.0)
        self.assertAlmostEqual(weekly.loc[pd.Timestamp("2025-01-13"), "temp_mean"], 10.0)


if __name__ == "__main__":
    unittest.main()

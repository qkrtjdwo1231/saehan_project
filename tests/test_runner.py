# 실험 러너(조건표 생성, 실행 기록 저장)를 검증하는 테스트
import json
import os
import shutil
import tempfile
import unittest

import pandas as pd

from pipeline.forecast.runner import grid, record_run


class GridTest(unittest.TestCase):
    def test_every_config_has_unique_id_and_all_keys(self):
        configs = grid()
        ids = [c["id"] for c in configs]
        self.assertEqual(len(ids), len(set(ids)))
        for c in configs:
            for k in ["id", "base", "alpha", "season", "holiday", "factor_years", "industry_w"]:
                self.assertIn(k, c)


class RecordRunTest(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.root)

    def test_writes_config_scores_log_and_index_row(self):
        config = {"id": "ses_a03", "base": "ses", "alpha": 0.3, "season": True, "holiday": True, "factor_years": "2021-2023", "industry_w": 0.0}
        levels = pd.DataFrame({"model": ["ses_a03"] * 2, "level": ["계열×주", "총량"], "wape": [1.1, 0.34]})
        by_type = pd.DataFrame({"demand_type": ["A", "B"], "wape_4w": [0.55, 1.05]})
        run_dir = record_run(self.root, config, levels, by_type, seconds=42.0, note="첫 실행")
        self.assertTrue(os.path.exists(os.path.join(run_dir, "config.json")))
        self.assertTrue(os.path.exists(os.path.join(run_dir, "levels.csv")))
        self.assertTrue(os.path.exists(os.path.join(run_dir, "by_type.csv")))
        index = pd.read_csv(os.path.join(self.root, "index.csv"))
        self.assertEqual(len(index), 1)
        self.assertEqual(index.loc[0, "id"], "ses_a03")
        self.assertAlmostEqual(index.loc[0, "wape_total"], 0.34)
        self.assertAlmostEqual(index.loc[0, "wape_4w_A"], 0.55)
        self.assertEqual(json.load(open(os.path.join(run_dir, "config.json"), encoding="utf8"))["alpha"], 0.3)


if __name__ == "__main__":
    unittest.main()

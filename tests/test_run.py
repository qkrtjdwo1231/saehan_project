# 전체 파이프라인(run.build)이 산출 파일을 만들고 합계를 보존하는지 검증하는 테스트
import os
import shutil
import tempfile
import unittest

import pandas as pd

from pipeline.run import build
from tests.test_load import SALES_HEADER, PROD_HEADER


def write_cp949(path, lines):
    with open(path, "wb") as f:
        f.write("\n".join(lines).encode("cp949"))


class BuildTest(unittest.TestCase):
    def setUp(self):
        self.src = tempfile.mkdtemp()
        self.out = tempfile.mkdtemp()
        write_cp949(os.path.join(self.src, "2025년 판매실적.xls"), [
            SALES_HEADER,
            "2025-01-06\tK1\t정상\t내수\tTM00663\tTSA00500P1\t대상 간장 500\t대상주식회사\t500\t박스\t100\t0\t1000\t1\t기사\tK1",
            "2025-01-12\tK2\t정상\t내수\tTM00663\tTSA00500P1\t대상 간장 500\t대상주식회사\t500\t박스\t100\t0\t500\t1\t기사\tK2",
            "2025-01-13\tK3\t반품\t내수\tTM00663\tTSA00500P1\t대상 간장 500\t대상주식회사\t500\t박스\t100\t0\t-100\t1\t기사\tK3",
            "2025-01-31\tK4\t정상\t내수\tAMBT366\tAMBTPF27\tPF - PCO 25g\t하이트진로(주)마산공장\t0\t83*155\t11040\t0\t8000000\t1\t기사\tK4",
            "2025-01-20\tK5\t정상\t내수\tAMCP029\tAMCPSA\tPE 말통 캡\t시아스\t0\t83*155\t500\t0\t300\t1\t기사\tK5",
        ])
        write_cp949(os.path.join(self.src, "2025년 생산실적(1211).xls"), [
            PROD_HEADER,
            "2025-01-05\t1211 PET 1팀\tA A조\tB1\t1\tTM00663\tTSA00500P1\t대상 간장 500\t대상주식회사\t박스\t22 재가공입고\t121A 제품창고\t\t100\t1500\t10",
        ])

    def tearDown(self):
        shutil.rmtree(self.src)
        shutil.rmtree(self.out)

    def test_writes_outputs_and_preserves_totals(self):
        summary = build(self.src, self.out)
        for name in ["sales_daily.csv", "prod_daily.csv", "items.csv", "weekly.csv"]:
            self.assertTrue(os.path.exists(os.path.join(self.out, name)), name)
        sales = pd.read_csv(os.path.join(self.out, "sales_daily.csv"))
        self.assertEqual(int(sales["qty"].sum()), 1000 + 500 - 100 + 8000000 + 300)
        self.assertEqual(summary["sales_rows"], 5)
        self.assertEqual(summary["prod_rows"], 1)

    def test_items_are_grouped_and_weekly_covers_cheongju_normal_shipments_only(self):
        build(self.src, self.out)
        items = pd.read_csv(os.path.join(self.out, "items.csv")).set_index("item_code")
        self.assertEqual(items.loc["TM00663", "group"], "청주생산")
        self.assertEqual(items.loc["AMBT366", "group"], "월말전표")
        self.assertEqual(items.loc["AMCP029", "group"], "기타")
        self.assertEqual(items.loc["TM00663", "main_dept"], 1211)
        weekly = pd.read_csv(os.path.join(self.out, "weekly.csv"))
        self.assertEqual(int(weekly["qty"].sum()), 1500)  # 반품 제외, 청주생산 품목만
        self.assertEqual(len(weekly), 1)  # 1/6(월)과 1/12(일)은 같은 주


if __name__ == "__main__":
    unittest.main()

# ERP 덤프(CP949 탭 텍스트) 로더의 동작을 검증하는 테스트
import os
import tempfile
import unittest

import pandas as pd

from pipeline.load import read_sales, read_production

SALES_HEADER = "출고일자\t전표번호\t출고구분\t판매형태\t품 번\t품 종\t품명/규격\t거래선\t용량\t포장단위\t포장단위수량\t포장수량\t출고수량\t차량번호\t운송기사\t출지번호"
PROD_HEADER = "생산일자\t생산부서\t작업조\t생산호기\t작업지시번호\t생산품번\t생산품종\t품명/규격\t거래선명\t포장단위\t전표구분\t투입공정\t투입호기\t포장단위수량\t수량(A급)\t수량(C급)"


def write_cp949(lines):
    fd, path = tempfile.mkstemp(suffix=".xls")
    with os.fdopen(fd, "wb") as f:
        f.write("\n".join(lines).encode("cp949"))
    return path


class ReadSalesTest(unittest.TestCase):
    def setUp(self):
        self.path = write_cp949([
            SALES_HEADER,
            "2025-01-01\tK2510001\t정상\t내수\tTM00329\tTSA01700P9\t지평 1.7L 쌀막걸리   \t지평주조\t1700\t파렛트\t924\t0\t12936\t7124\t          \tK25010002",
            "2025-01-02\tK2510002\t반품\t내수\tAMCP029\tAMCPSA\tPE 말통 캡\t주식회사 시아스\t0\t83*155\t500\t0\t-408\t    \t          \tK25010003",
            "합계\t\t\t\t\t\t\t\t\t\t\t\t12528\t\t\t",
        ])

    def tearDown(self):
        os.remove(self.path)

    def test_reads_rows_with_valid_dates_only(self):
        df = read_sales(self.path)
        self.assertEqual(len(df), 2)
        self.assertEqual(df["date"].iloc[0], pd.Timestamp("2025-01-01"))

    def test_strips_whitespace_and_converts_quantity(self):
        df = read_sales(self.path)
        self.assertEqual(df["item_name"].iloc[0], "지평 1.7L 쌀막걸리")
        self.assertEqual(df["qty"].iloc[0], 12936)
        self.assertEqual(df["qty"].iloc[1], -408)
        self.assertEqual(df["ship_type"].iloc[1], "반품")


class ReadProductionTest(unittest.TestCase):
    def setUp(self):
        self.path = write_cp949([
            PROD_HEADER,
            "2025-01-01\t1219 PET 2팀\tA A조\tP3\t202501010011\tFM00007\tFSA00049P9\t원터치 49G [CL]   \t\t없음\t21 본가공입고\t121A 제품창고\t\t6000\t44200\t40",
            "2025-01-01\t1211 PET 1팀\tC C조\t02\t202412270001\tTM00580\tTSO00200P1\t대선 소주 200\t(주)평안매직\t박스\t22 재가공입고\t121A 제품창고\t\t459\t22950\t58",
        ])

    def tearDown(self):
        os.remove(self.path)

    def test_extracts_department_code_and_doc_type_code(self):
        df = read_production(self.path)
        self.assertEqual(list(df["dept"]), ["1219", "1211"])
        self.assertEqual(list(df["doc_type"]), ["21", "22"])
        self.assertEqual(list(df["shift"]), ["A", "C"])

    def test_converts_quantities(self):
        df = read_production(self.path)
        self.assertEqual(int(df["qty_a"].sum()), 44200 + 22950)
        self.assertEqual(int(df["qty_c"].sum()), 98)


if __name__ == "__main__":
    unittest.main()

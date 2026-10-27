# ERP(Mold) 덤프 파일(CP949 인코딩 탭 구분 텍스트, 확장자 .xls)을 읽어 정리된 DataFrame으로 만드는 로더
import io

import pandas as pd

SALES_COLUMNS = {
    "출고일자": "date", "전표번호": "doc_no", "출고구분": "ship_type", "판매형태": "sale_type",
    "품 번": "item_code", "품 종": "item_type", "품명/규격": "item_name", "거래선": "customer",
    "용량": "capacity", "포장단위": "pack_unit", "포장단위수량": "pack_qty", "포장수량": "pack_count",
    "출고수량": "qty", "차량번호": "vehicle", "운송기사": "driver", "출지번호": "ship_no",
}
PROD_COLUMNS = {
    "생산일자": "date", "생산부서": "dept_name", "작업조": "shift_name", "생산호기": "machine",
    "작업지시번호": "order_no", "생산품번": "item_code", "생산품종": "item_type", "품명/규격": "item_name",
    "거래선명": "customer", "포장단위": "pack_unit", "전표구분": "doc_type_name", "투입공정": "input_process",
    "투입호기": "input_machine", "포장단위수량": "pack_qty", "수량(A급)": "qty_a", "수량(C급)": "qty_c",
}


def _read_tsv(path, columns):
    with open(path, "rb") as f:
        text = f.read().decode("cp949", errors="replace")
    df = pd.read_csv(io.StringIO(text), sep="\t", dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns=columns)
    for c in df.columns:
        df[c] = df[c].fillna("").astype(str).str.strip()
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    df = df[df["date"].notna()].reset_index(drop=True)
    return df


def _to_int(series):
    return pd.to_numeric(series.str.replace(",", ""), errors="coerce").fillna(0).astype("int64")


def read_sales(path):
    df = _read_tsv(path, SALES_COLUMNS)
    for c in ["qty", "pack_qty", "pack_count", "capacity"]:
        df[c] = _to_int(df[c])
    return df


def read_production(path):
    df = _read_tsv(path, PROD_COLUMNS)
    for c in ["qty_a", "qty_c", "pack_qty"]:
        df[c] = _to_int(df[c])
    df["dept"] = df["dept_name"].str.extract(r"^(\d{4})")[0]
    df["doc_type"] = df["doc_type_name"].str.extract(r"^(\d{2})")[0]
    df["shift"] = df["shift_name"].str.extract(r"([A-Za-z])\s*조")[0].str.upper()
    return df

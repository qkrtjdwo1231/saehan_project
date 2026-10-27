# 주간 집계(weekly.csv)로 2025년 walk-forward 검증을 돌리고 모델×구간×수요유형별 점수표를 만드는 실행 스크립트
import os
import sys

import numpy as np
import pandas as pd

from pipeline.aggregate import plant1_outage
from pipeline.classify import demand_type
from pipeline.forecast.backtest import walk_forward
from pipeline.forecast.baselines import moving_average, seasonal_naive
from pipeline.forecast.metrics import wape, hit_rate

TEST_YEAR = 2025
TYPE_YEAR = 2024
PLANT1_DEPTS = {1211, 1212}

BASELINES = {
    "zero": lambda history, h, valid: 0.0,
    "ma8": lambda history, h, valid: moving_average(history, valid),
    "snaive": lambda history, h, valid: seasonal_naive(history, h, valid),
}


def series_matrix(weekly):
    df = weekly.assign(series=weekly["item_type"] + "|" + weekly["customer"])
    weeks = pd.date_range(df["week_start"].min(), df["week_start"].max(), freq="W-MON")
    return df.pivot_table(index="series", columns="week_start", values="qty", aggfunc="sum", fill_value=0).reindex(columns=weeks, fill_value=0)


def summarize(result, types):
    df = result.assign(demand_type=result["series"].map(types).fillna("C"))
    df = pd.concat([df, df.assign(demand_type="전체")], ignore_index=True)
    rows = []
    for (model, h, t), g in df.groupby(["model", "horizon", "demand_type"]):
        rows.append({"model": model, "horizon": h, "demand_type": t, "n": len(g),
                     "wape": wape(g["actual"], g["pred"]), "hit_rate": hit_rate(g["actual"], g["pred"])})
    return pd.DataFrame(rows)


def valid_mask(matrix, items):
    """1공장(1211·1212) 품종의 화재 중단 구간은 학습에 쓰지 않도록 False."""
    type_dept = items.dropna(subset=["main_dept"]).groupby("item_type")["main_dept"].agg(lambda s: s.mode().iloc[0])
    plant1_types = set(type_dept[type_dept.isin(PLANT1_DEPTS)].index)
    is_plant1 = matrix.index.to_series().str.split("|").str[0].isin(plant1_types).to_numpy()
    outage_weeks = plant1_outage(pd.Series(matrix.columns)).to_numpy()
    mask = np.ones(matrix.shape, dtype=bool)
    mask[np.ix_(is_plant1, outage_weeks)] = False
    return pd.DataFrame(mask, index=matrix.index, columns=matrix.columns)


def series_types(matrix, valid, year):
    cols = [c for c in matrix.columns if c.year == year]
    out = {}
    for s in matrix.index:
        v = valid.loc[s, cols].to_numpy()
        out[s] = demand_type(matrix.loc[s, cols].to_numpy()[v])
    return pd.Series(out)


def run(processed_dir, models=BASELINES, label="baseline"):
    weekly = pd.read_csv(os.path.join(processed_dir, "weekly.csv"), parse_dates=["week_start"])
    items = pd.read_csv(os.path.join(processed_dir, "items.csv"))
    matrix = series_matrix(weekly)
    valid = valid_mask(matrix, items)
    types = series_types(matrix, valid, TYPE_YEAR)
    origins = [c for c in matrix.columns if c.year == TEST_YEAR][:-1]
    result = walk_forward(matrix, models, origins, horizons=(1, 2, 3, 4), valid=valid)
    table = summarize(result, types)
    result.to_csv(os.path.join(processed_dir, f"backtest_{label}.csv"), index=False, encoding="utf-8-sig")
    table.to_csv(os.path.join(processed_dir, f"scores_{label}.csv"), index=False, encoding="utf-8-sig")
    return table, types


if __name__ == "__main__":
    processed = sys.argv[1] if len(sys.argv) > 1 else os.path.join("data", "processed")
    table, types = run(processed)
    print("계열 수:", len(types), "| 2024년 기준 유형:", types.value_counts().to_dict())
    pd.set_option("display.width", 200)
    for t in ["전체", "A", "B", "C"]:
        print(f"\n=== 수요유형 {t} ===")
        print(table[table["demand_type"] == t].pivot(index="model", columns="horizon", values="wape").round(3).to_string())
        print("출고 유무 적중률 (h=1):", table[(table["demand_type"] == t) & (table["horizon"] == 1)].set_index("model")["hit_rate"].round(3).to_dict())

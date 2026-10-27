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
from pipeline.forecast.models import ses, tsb

TEST_YEAR = 2025
TYPE_YEAR = 2024
PLANT1_DEPTS = {1211, 1212}

BASELINES = {
    "zero": lambda history, h, valid: 0.0,
    "ma8": lambda history, h, valid: moving_average(history, valid),
    "snaive": lambda history, h, valid: seasonal_naive(history, h, valid),
}
MODELS = dict(BASELINES, **{
    "ses": lambda history, h, valid: ses(history, h, valid),
    "tsb": lambda history, h, valid: tsb(history, h, valid),
})


def levels(result):
    """모델별로 네 집계 수준의 WAPE를 낸다. 계열×주·품종×주·총량은 1주 앞, 4주합은 h=1~4 합계."""
    rows = []
    for model, g in result.groupby("model"):
        h1 = g[g["horizon"] == 1]
        by_type = h1.assign(t=h1["series"].str.split("|").str[0]).groupby(["t", "target"])[["actual", "pred"]].sum()
        total = h1.groupby("target")[["actual", "pred"]].sum()
        four = g.groupby(["series", "origin"])[["actual", "pred"]].sum()
        for level, d in [("계열×주", h1), ("품종×주", by_type), ("계열×4주합", four), ("총량", total)]:
            rows.append({"model": model, "level": level, "wape": wape(d["actual"], d["pred"])})
    return pd.DataFrame(rows)


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
    levels(result).to_csv(os.path.join(processed_dir, f"levels_{label}.csv"), index=False, encoding="utf-8-sig")
    return table, types, result


if __name__ == "__main__":
    processed = sys.argv[1] if len(sys.argv) > 1 else os.path.join("data", "processed")
    table, types, result = run(processed, MODELS, label="models")
    print("계열 수:", len(types), "| 2024년 기준 유형:", types.value_counts().to_dict())
    pd.set_option("display.width", 200)
    print("\n=== 집계 수준별 WAPE ===")
    print(levels(result).pivot(index="model", columns="level", values="wape").round(3).to_string())
    for t in ["전체", "A", "B", "C"]:
        print(f"\n=== 수요유형 {t} · 계열×주 WAPE (구간별) ===")
        print(table[table["demand_type"] == t].pivot(index="model", columns="horizon", values="wape").round(3).to_string())
        print("출고 유무 적중률 (h=1):", table[(table["demand_type"] == t) & (table["horizon"] == 1)].set_index("model")["hit_rate"].round(3).to_dict())
    four = result.groupby(["model", "series", "origin"])[["actual", "pred"]].sum().reset_index()
    four["demand_type"] = four["series"].map(types)
    print("\n=== 수요유형별 계열×4주합 WAPE ===")
    print(four.groupby(["model", "demand_type"]).apply(lambda g: wape(g["actual"], g["pred"]), include_groups=False).unstack().round(3).to_string())

# 최신 데이터 시점에서 계열별 다음 4주 예측(지수평활 × 계절지수 × 연휴계수)과 화면용 JSON을 만드는 모듈
import json
import os
import sys

import numpy as np
import pandas as pd

from pipeline.aggregate import plant1_outage
from pipeline.classify import demand_type
from pipeline.forecast.adjust import monthly_index, flag_factors
from pipeline.forecast.calendar import week_flags
from pipeline.forecast.evaluate import series_matrix, valid_mask
from pipeline.forecast.models import ses

HORIZON = 4
RECENT = 12
TRAIN_YEARS = [2021, 2022, 2023]  # 계절·연휴 계수 추정 연도. 실험 1 결과 2021~2023이 최적(2024 하반기 화재 왜곡 제외). 학습 데이터 자체는 2021~2024 전체


def _factors(matrix, valid, future_weeks):
    weeks = pd.DatetimeIndex(matrix.columns)
    all_weeks = weeks.append(pd.DatetimeIndex(future_weeks))
    train = [w for w in weeks if w.year in TRAIN_YEARS]
    totals = pd.Series(np.where(valid.to_numpy(), matrix.to_numpy(), 0).sum(axis=0), index=weeks)
    season = monthly_index(totals[train])
    season_vec = pd.Series([season[w.month] for w in all_weeks], index=all_weeks)
    flags = week_flags(all_weeks).set_index("week_start")
    hol = flag_factors((totals / season_vec[weeks])[train], week_flags(weeks)[lambda f: f["week_start"].isin(train)])
    hol_vec = pd.Series([hol["holiday_week"] if flags.loc[w, "holiday_week"] else hol["pre_holiday_week"] if flags.loc[w, "pre_holiday_week"] else 1.0 for w in all_weeks], index=all_weeks)
    return season_vec * hol_vec, season, hol


def produce(weekly, items):
    matrix = series_matrix(weekly)
    valid = valid_mask(matrix, items)
    weeks = pd.DatetimeIndex(matrix.columns)
    last = weeks[-1]
    future = [last + pd.Timedelta(days=7 * (h + 1)) for h in range(HORIZON)]
    factor, season, hol = _factors(matrix, valid, future)
    type_year = last.year
    type_cols = [c for c in weeks if c.year == type_year]
    meta = items.groupby("item_type").agg(item_name=("item_name", "first"), main_dept=("main_dept", lambda s: s.mode().iloc[0] if s.notna().any() else None),
                                           item_codes=("item_code", lambda s: list(s)))
    series_out = []
    for s in matrix.index:
        hist = matrix.loc[s].to_numpy(dtype=float)
        v = valid.loc[s].to_numpy(dtype=bool)
        level = ses(hist / factor[weeks].to_numpy(), valid=v)
        fc = [float(level * factor[w]) for w in future]
        t = demand_type(matrix.loc[s, type_cols].to_numpy()[valid.loc[s, type_cols].to_numpy()])
        item_type, customer = s.split("|", 1)
        m = meta.loc[item_type] if item_type in meta.index else None
        series_out.append({
            "series": s, "item_type": item_type, "customer": customer,
            "item_name": (m["item_name"] if m is not None else ""), "item_codes": (m["item_codes"] if m is not None else []),
            "main_dept": (int(m["main_dept"]) if m is not None and m["main_dept"] is not None and not pd.isna(m["main_dept"]) else None),
            "demand_type": t, "recent": [float(x) for x in hist[-RECENT:]], "qty_year": float(matrix.loc[s, type_cols].sum()),
            "forecast": fc, "forecast_4w": float(sum(fc)),
        })
    series_out.sort(key=lambda r: -r["forecast_4w"])
    totals_recent = matrix.sum(axis=0).to_numpy(dtype=float)[-RECENT:]
    return {
        "as_of": last.strftime("%Y-%m-%d"),
        "forecast_weeks": [w.strftime("%Y-%m-%d") for w in future],
        "recent_weeks": [w.strftime("%Y-%m-%d") for w in weeks[-RECENT:]],
        "model": "ses(alpha=0.3) x 월별 계절지수 x 설·추석 연휴계수, 계수 추정 2021~2023, 1공장 화재 구간 제외",
        "season_index": {str(k): round(v, 3) for k, v in season.items()}, "holiday_factors": {k: round(v, 3) for k, v in hol.items()},
        "totals": {"recent_weeks": [w.strftime("%Y-%m-%d") for w in weeks[-RECENT:]], "recent": [float(x) for x in totals_recent],
                   "forecast": [float(np.sum([r["forecast"][h] for r in series_out])) for h in range(HORIZON)]},
        "series": series_out,
    }


def machines(prod_daily, year):
    p = prod_daily[(prod_daily["date"].dt.year == year) & (prod_daily["doc_type"].isin(["21", "22"]))]
    g = p.groupby(["dept", "machine"]).agg(days=("date", "nunique"), qty=("qty_a", "sum"), items=("item_type", lambda s: sorted(set(s))[:12])).reset_index()
    g = g[g["days"] >= 10].sort_values(["dept", "machine"])
    return [{"dept": str(r.dept), "machine": r.machine, "active_days": int(r.days), "qty_year": float(r.qty), "item_types": r["items"]} for _, r in g.iterrows()]


if __name__ == "__main__":
    processed = sys.argv[1] if len(sys.argv) > 1 else os.path.join("data", "processed")
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.join("data", "web")
    os.makedirs(out_dir, exist_ok=True)
    weekly = pd.read_csv(os.path.join(processed, "weekly.csv"), parse_dates=["week_start"])
    items = pd.read_csv(os.path.join(processed, "items.csv"))
    out = produce(weekly, items)
    json.dump(out, open(os.path.join(out_dir, "forecast.json"), "w", encoding="utf8"), ensure_ascii=False)
    prod = pd.read_csv(os.path.join(processed, "prod_daily.csv"), parse_dates=["date"], dtype={"dept": str, "doc_type": str, "machine": str})
    json.dump(machines(prod, int(out["as_of"][:4])), open(os.path.join(out_dir, "machines.json"), "w", encoding="utf8"), ensure_ascii=False)
    print("as_of", out["as_of"], "| series", len(out["series"]), "| totals forecast", [round(x / 1e6, 2) for x in out["totals"]["forecast"]], "백만")
    print("types", pd.Series([r["demand_type"] for r in out["series"]]).value_counts().to_dict())

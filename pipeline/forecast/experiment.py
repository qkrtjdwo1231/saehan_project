# 외부 변수 실험: 계절지수·연휴 계수·기온 보정을 하나씩 더해 2025년 walk-forward 점수 변화를 비교하는 실행 스크립트
import os
import sys

import numpy as np
import pandas as pd

from pipeline.forecast.adjust import monthly_index, flag_factors, with_factors, deseasonalized
from pipeline.forecast.baselines import moving_average
from pipeline.forecast.calendar import week_flags
from pipeline.forecast.evaluate import series_matrix, valid_mask, series_types, summarize, levels, TEST_YEAR, TYPE_YEAR
from pipeline.forecast.backtest import walk_forward
from pipeline.forecast.metrics import wape
from pipeline.forecast.models import ses
from pipeline.external.weather import weekly_temperature

TRAIN_YEARS = [2021, 2022, 2023]  # 2024 하반기는 1공장 중단으로 총량이 왜곡되어 계수 추정에서 제외


def factor_vectors(matrix, valid, weather_daily, train_years=TRAIN_YEARS):
    weeks = pd.DatetimeIndex(matrix.columns)
    train = [w for w in weeks if w.year in train_years]
    totals = pd.Series(np.where(valid.to_numpy(), matrix.to_numpy(), 0).sum(axis=0), index=weeks)
    season = monthly_index(totals[train])
    season_vec = pd.Series([season[w.month] for w in weeks], index=weeks)

    flags = week_flags(weeks)
    hol = flag_factors((totals / season_vec)[train], flags[flags["week_start"].isin(train)])
    fl = flags.set_index("week_start")
    hol_vec = pd.Series([hol["holiday_week"] if fl.loc[w, "holiday_week"] else hol["pre_holiday_week"] if fl.loc[w, "pre_holiday_week"] else 1.0 for w in weeks], index=weeks)

    temp = weekly_temperature(weather_daily).set_index("week_start")["temp_mean"].reindex(weeks)
    month_mean = temp.groupby(temp.index.month).transform("mean")
    anomaly = (temp - month_mean).fillna(0)
    resid = np.log((totals / (season_vec * hol_vec)).clip(lower=1))[train]
    beta = float(np.polyfit(anomaly[train], resid - resid.mean(), 1)[0])
    temp_vec = pd.Series(np.exp(beta * anomaly), index=weeks)
    return {"season": season_vec, "holiday": hol_vec, "temp": temp_vec, "beta": beta, "season_index": season, "holiday_factors": hol}


def variants(fv):
    s, hl, tp = fv["season"], fv["holiday"], fv["temp"]
    base_ses = lambda history, h, valid: ses(history, h, valid)
    base_ma8 = lambda history, h, valid: moving_average(history, valid)
    return {
        "ses": base_ses,
        "ses+season": with_factors(deseasonalized(base_ses, s), s),
        "ses+season+hol": with_factors(deseasonalized(base_ses, s * hl), s * hl),
        "ses+season+hol+temp": with_factors(deseasonalized(base_ses, s * hl), s * hl * tp),
        "ma8": base_ma8,
        "ma8+season+hol": with_factors(deseasonalized(base_ma8, s * hl), s * hl),
    }


def run(processed_dir, weather_path):
    weekly = pd.read_csv(os.path.join(processed_dir, "weekly.csv"), parse_dates=["week_start"])
    items = pd.read_csv(os.path.join(processed_dir, "items.csv"))
    weather = pd.read_csv(weather_path, parse_dates=["date"])
    matrix = series_matrix(weekly)
    valid = valid_mask(matrix, items)
    types = series_types(matrix, valid, TYPE_YEAR)
    fv = factor_vectors(matrix, valid, weather)
    origins = [c for c in matrix.columns if c.year == TEST_YEAR][:-1]
    result = walk_forward(matrix, variants(fv), origins, horizons=(1, 2, 3, 4), valid=valid)
    result.to_csv(os.path.join(processed_dir, "backtest_external.csv"), index=False, encoding="utf-8-sig")
    return result, types, fv


if __name__ == "__main__":
    processed = sys.argv[1] if len(sys.argv) > 1 else os.path.join("data", "processed")
    weather_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join("data", "external", "cheongju_weather_daily.csv")
    result, types, fv = run(processed, weather_path)
    pd.set_option("display.width", 220)
    print("월별 계절지수:", {k: round(v, 2) for k, v in fv["season_index"].items()})
    print("연휴 계수:", {k: round(v, 2) for k, v in fv["holiday_factors"].items()}, "| 기온 민감도 beta:", round(fv["beta"], 4))
    print("\n=== 집계 수준별 WAPE ===")
    print(levels(result).pivot(index="model", columns="level", values="wape").round(3).to_string())
    four = result.groupby(["model", "series", "origin"])[["actual", "pred"]].sum().reset_index()
    four["demand_type"] = four["series"].map(types)
    print("\n=== 수요유형별 계열×4주합 WAPE ===")
    print(four.groupby(["model", "demand_type"]).apply(lambda g: wape(g["actual"], g["pred"]), include_groups=False).unstack().round(3).to_string())
    table = summarize(result, types)
    print("\n=== 수요유형 A · 계열×주 WAPE (구간별) ===")
    print(table[table["demand_type"] == "A"].pivot(index="model", columns="horizon", values="wape").round(3).to_string())

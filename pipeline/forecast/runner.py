# 여러 조건(모델·평활계수·계절·연휴·계수 추정 연도·업계 지수 비중)을 한 번에 돌리고 조건별 폴더에 기록하는 실험 러너
import json
import os
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd

from pipeline.forecast.adjust import with_factors, deseasonalized
from pipeline.forecast.baselines import moving_average
from pipeline.forecast.evaluate import series_matrix, valid_mask, series_types, levels, TEST_YEAR, TYPE_YEAR
from pipeline.forecast.experiment import factor_vectors
from pipeline.forecast.backtest import walk_forward
from pipeline.forecast.metrics import wape
from pipeline.forecast.models import ses

# 동종 핵심 6개사 합산 매출의 연도별 수준(2022=1). reports/05_peers.md
INDUSTRY_LEVEL = {2021: 1.0, 2022: 1.0, 2023: 1.068, 2024: 1.186, 2025: 1.202}
FACTOR_YEAR_SETS = {"2021-2023": [2021, 2022, 2023], "2021-2024": [2021, 2022, 2023, 2024]}


def grid():
    configs = []
    for base, alphas in [("ses", [0.2, 0.3, 0.5]), ("ma8", [None])]:
        for alpha in alphas:
            for season, holiday in [(False, False), (True, False), (True, True), (False, True)]:
                for fy in FACTOR_YEAR_SETS:
                    ws = [0.0] + ([0.5, 1.0] if (season and holiday) else [])
                    for w in ws:
                        cid = f"{base}" + (f"_a{alpha}" if alpha is not None else "") + f"_s{int(season)}h{int(holiday)}_{fy}_w{w}"
                        configs.append({"id": cid, "base": base, "alpha": alpha, "season": season, "holiday": holiday, "factor_years": fy, "industry_w": w})
    return configs


def build_model(config, fv, weeks):
    base = (lambda h, k, v: ses(h, k, v, alpha=config["alpha"])) if config["base"] == "ses" else (lambda h, k, v: moving_average(h, v))
    factor = pd.Series(1.0, index=weeks)
    if config["season"]:
        factor = factor * fv["season"]
    if config["holiday"]:
        factor = factor * fv["holiday"]
    if config["industry_w"]:
        factor = factor * pd.Series([INDUSTRY_LEVEL.get(w.year, 1.0) ** config["industry_w"] for w in weeks], index=weeks)
    if (factor != 1.0).any():
        return with_factors(deseasonalized(base, factor), factor)
    return base


def record_run(root, config, levels_df, by_type, seconds, note=""):
    run_dir = os.path.join(root, config["id"])
    os.makedirs(run_dir, exist_ok=True)
    json.dump(config, open(os.path.join(run_dir, "config.json"), "w", encoding="utf8"), ensure_ascii=False, indent=2)
    levels_df.to_csv(os.path.join(run_dir, "levels.csv"), index=False, encoding="utf-8-sig")
    by_type.to_csv(os.path.join(run_dir, "by_type.csv"), index=False, encoding="utf-8-sig")
    lv = levels_df.set_index("level")["wape"]
    bt = by_type.set_index("demand_type")["wape_4w"]
    row = dict(config)
    row.update({
        "wape_series": lv.get("계열×주", np.nan), "wape_type": lv.get("품종×주", np.nan),
        "wape_4w": lv.get("계열×4주합", np.nan), "wape_total": lv.get("총량", np.nan),
        "wape_4w_A": bt.get("A", np.nan), "wape_4w_B": bt.get("B", np.nan), "wape_4w_C": bt.get("C", np.nan),
        "seconds": round(seconds, 1), "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "note": note,
    })
    with open(os.path.join(run_dir, "log.txt"), "a", encoding="utf8") as f:
        f.write(f"{row['timestamp']} 완료 {seconds:.1f}s | 계열×주 {row['wape_series']:.3f} 4주합 {row['wape_4w']:.3f} 총량 {row['wape_total']:.3f} | A {row['wape_4w_A']:.3f} B {row['wape_4w_B']:.3f} C {row['wape_4w_C']:.3f} | {note}\n")
    index_path = os.path.join(root, "index.csv")
    pd.DataFrame([row]).to_csv(index_path, mode="a", header=not os.path.exists(index_path), index=False, encoding="utf-8-sig")
    return run_dir


def run_all(processed_dir, weather_path, root, note=""):
    os.makedirs(root, exist_ok=True)
    weekly = pd.read_csv(os.path.join(processed_dir, "weekly.csv"), parse_dates=["week_start"])
    items = pd.read_csv(os.path.join(processed_dir, "items.csv"))
    weather = pd.read_csv(weather_path, parse_dates=["date"])
    matrix = series_matrix(weekly)
    valid = valid_mask(matrix, items)
    types = series_types(matrix, valid, TYPE_YEAR)
    weeks = pd.DatetimeIndex(matrix.columns)
    origins = [c for c in matrix.columns if c.year == TEST_YEAR][:-1]
    fvs = {fy: factor_vectors(matrix, valid, weather, train_years=yrs) for fy, yrs in FACTOR_YEAR_SETS.items()}
    done = set(pd.read_csv(os.path.join(root, "index.csv"))["id"]) if os.path.exists(os.path.join(root, "index.csv")) else set()
    progress = open(os.path.join(root, "progress.log"), "a", encoding="utf8")
    configs = grid()
    for i, config in enumerate(configs, 1):
        if config["id"] in done:
            continue
        t0 = time.time()
        model = build_model(config, fvs[config["factor_years"]], weeks)
        result = walk_forward(matrix, {config["id"]: model}, origins, horizons=(1, 2, 3, 4), valid=valid)
        lv = levels(result)
        four = result.groupby(["series", "origin"])[["actual", "pred"]].sum().reset_index()
        four["demand_type"] = four["series"].map(types)
        by_type = four.groupby("demand_type").apply(lambda g: wape(g["actual"], g["pred"]), include_groups=False).rename("wape_4w").reset_index()
        record_run(root, config, lv, by_type, time.time() - t0, note)
        progress.write(f"{datetime.now():%H:%M:%S} [{i}/{len(configs)}] {config['id']} 완료 ({time.time() - t0:.0f}s)\n"); progress.flush()
    progress.write(f"{datetime.now():%H:%M:%S} 전체 완료\n"); progress.close()


if __name__ == "__main__":
    processed = sys.argv[1] if len(sys.argv) > 1 else os.path.join("data", "processed")
    weather = sys.argv[2] if len(sys.argv) > 2 else os.path.join("data", "external", "cheongju_weather_daily.csv")
    root = sys.argv[3] if len(sys.argv) > 3 else os.path.join("experiments", "exp01_factors")
    run_all(processed, weather, root, note=sys.argv[4] if len(sys.argv) > 4 else "")

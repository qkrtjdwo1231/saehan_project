# 청주 일별 기온·강수를 Open-Meteo 과거 기상 API에서 내려받아 저장하고 주 평균으로 집계한다
import json
import os
import sys
import urllib.request

import pandas as pd

from pipeline.aggregate import week_start

CHEONGJU = (36.64, 127.49)
URL = ("https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}"
       "&start_date={start}&end_date={end}&daily=temperature_2m_mean,precipitation_sum&timezone=Asia%2FSeoul")


def fetch_daily(start, end, lat=CHEONGJU[0], lon=CHEONGJU[1]):
    with urllib.request.urlopen(URL.format(lat=lat, lon=lon, start=start, end=end), timeout=60) as r:
        d = json.load(r)["daily"]
    return pd.DataFrame({"date": pd.to_datetime(d["time"]), "temp_mean": d["temperature_2m_mean"], "precip": d["precipitation_sum"]})


def weekly_temperature(daily):
    df = daily.assign(week_start=week_start(daily["date"]))
    return df.groupby("week_start", as_index=False)[[c for c in ["temp_mean", "precip"] if c in df.columns]].mean()


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join("data", "external", "cheongju_weather_daily.csv")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    daily = fetch_daily("2021-01-01", "2025-12-31")
    daily.to_csv(out, index=False, encoding="utf-8-sig")
    print("saved", out, len(daily), "days")

# 일별 출고를 품종×거래처×주(월요일 시작) 단위로 집계하고, 1공장 화재 중단 구간을 표시하는 함수
import pandas as pd

PLANT1_OUTAGE_START = pd.Timestamp("2024-07-08")  # 오창 공장 화재 보도일
PLANT1_OUTAGE_END = pd.Timestamp("2025-01-31")    # 신규 설비 재가동 직전


def week_start(dates):
    return dates.dt.normalize() - pd.to_timedelta(dates.dt.weekday, unit="D")


def weekly_by_type_customer(daily):
    df = daily.assign(week_start=week_start(daily["date"]))
    return (df.groupby(["item_type", "customer", "week_start"], as_index=False)["qty"].sum()
              .sort_values(["item_type", "customer", "week_start"]).reset_index(drop=True))


def plant1_outage(dates):
    dates = pd.Series(pd.to_datetime(dates))
    return (dates >= PLANT1_OUTAGE_START) & (dates <= PLANT1_OUTAGE_END)

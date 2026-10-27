# 설·추석 연휴 달력(공휴일 기준, 대체·임시공휴일 포함)과 주 단위 플래그(연휴 주, 연휴 전 주)
import pandas as pd

# (연휴 시작일, 연휴 종료일). 출처: 관공서의 공휴일에 관한 규정, 연도별 인사혁신처 공휴일 고시.
HOLIDAY_RANGES = [
    ("2021-02-11", "2021-02-13"), ("2021-09-20", "2021-09-22"),
    ("2022-01-31", "2022-02-02"), ("2022-09-09", "2022-09-12"),
    ("2023-01-21", "2023-01-24"), ("2023-09-28", "2023-10-03"),
    ("2024-02-09", "2024-02-12"), ("2024-09-16", "2024-09-18"),
    ("2025-01-27", "2025-01-30"), ("2025-10-03", "2025-10-09"),
    ("2026-02-16", "2026-02-18"), ("2026-09-24", "2026-09-26"),
]


def holiday_days():
    days = []
    for start, end in HOLIDAY_RANGES:
        days.extend(pd.date_range(start, end, freq="D"))
    return pd.DatetimeIndex(days)


def week_flags(week_starts):
    weeks = pd.DatetimeIndex(pd.to_datetime(week_starts))
    holiday_weeks = set(d - pd.Timedelta(days=d.weekday()) for d in holiday_days())
    is_holiday = [w in holiday_weeks for w in weeks]
    is_pre = [(w + pd.Timedelta(days=7)) in holiday_weeks and w not in holiday_weeks for w in weeks]
    return pd.DataFrame({"week_start": weeks, "holiday_week": is_holiday, "pre_holiday_week": is_pre})

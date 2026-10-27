# 외부 변수 보정: 월별 계절지수, 연휴 주 계수, 그리고 기본 모델의 예측값에 목표 주의 계수를 곱하는 래퍼
import numpy as np
import pandas as pd


def monthly_index(weekly_totals):
    """주별 총량(인덱스 = 주 시작일) → 월(1~12)별 계수. 없는 달은 1.0."""
    s = pd.Series(weekly_totals)
    by_month = s.groupby(s.index.month).mean() / s.mean()
    return {m: float(by_month.get(m, 1.0)) for m in range(1, 13)}


def flag_factors(weekly_totals, flags):
    """플래그가 켜진 주의 평균 ÷ 아무 플래그도 없는 주의 평균."""
    s = pd.Series(weekly_totals)
    f = flags.set_index("week_start").reindex(s.index).fillna(False)
    cols = [c for c in f.columns]
    base = s[~f[cols].any(axis=1)].mean()
    return {c: float(s[f[c]].mean() / base) if f[c].any() else 1.0 for c in cols}


def deseasonalized(base_model, factor_by_week):
    """history를 각 주의 계수로 나눈 뒤 base_model에 넘긴다(계절성을 뺀 수준을 추정)."""
    factors = np.asarray(pd.Series(factor_by_week).to_numpy(), dtype=float)

    def model(history, h, valid):
        n = len(history)
        return float(base_model(np.asarray(history, dtype=float) / factors[:n], h, valid))
    return model


def with_factors(base_model, factor_by_week):
    """base_model(history, h, valid) × factor(목표 주). 목표 주 = history 마지막 주 + h."""
    factors = np.asarray(pd.Series(factor_by_week).to_numpy(), dtype=float)

    def model(history, h, valid):
        target = len(history) - 1 + h
        f = factors[target] if target < len(factors) else 1.0
        return float(base_model(history, h, valid)) * f
    return model

# 기준선 예측: 최근 8주 평균, 작년 같은 주(52주 전). 모델은 (history, horizon, valid) → 예측값 한 개
import numpy as np

WINDOW = 8
SEASON = 52


def moving_average(history, valid=None, horizon=1):
    history = np.asarray(history, dtype=float)
    if valid is None:
        valid = np.ones(len(history), dtype=bool)
    recent = history[np.asarray(valid, dtype=bool)][-WINDOW:]
    if len(recent) == 0:
        return 0.0
    return float(recent.mean())


def seasonal_naive(history, horizon=1, valid=None):
    history = np.asarray(history, dtype=float)
    if valid is None:
        valid = np.ones(len(history), dtype=bool)
    ref = len(history) - 1 + horizon - SEASON
    if ref >= 0 and valid[ref]:
        return float(history[ref])
    return moving_average(history, valid)

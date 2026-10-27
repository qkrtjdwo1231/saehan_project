# 예측 점수: 물량 가중 오차율(WAPE)과 출고 유무 적중률
import numpy as np


def wape(actual, pred):
    actual = np.asarray(actual, dtype=float)
    pred = np.asarray(pred, dtype=float)
    total = np.abs(actual).sum()
    if total == 0:
        return np.nan
    return float(np.abs(actual - pred).sum() / total)


def hit_rate(actual, pred):
    actual = np.asarray(actual, dtype=float)
    pred = np.asarray(pred, dtype=float)
    if len(actual) == 0:
        return np.nan
    return float(((actual > 0) == (pred > 0)).mean())

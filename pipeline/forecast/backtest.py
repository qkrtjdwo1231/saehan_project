# walk-forward 검증: 각 시점(origin)까지의 데이터로 1~4주 앞을 예측해 실제와 나란히 기록한다
import numpy as np
import pandas as pd


def walk_forward(matrix, models, origins, horizons=(1, 2, 3, 4), valid=None):
    """matrix: 행 = 계열, 열 = 주(오름차순). models: {이름: f(history, horizon, valid) -> 예측값}."""
    cols = list(matrix.columns)
    values = matrix.to_numpy(dtype=float)
    mask = np.ones_like(values, dtype=bool) if valid is None else valid.reindex(index=matrix.index, columns=cols).to_numpy(dtype=bool)
    rows = []
    for origin in origins:
        t = cols.index(origin)
        for i, series in enumerate(matrix.index):
            history = values[i, : t + 1]
            hist_valid = mask[i, : t + 1]
            for h in horizons:
                if t + h >= len(cols):
                    continue
                for name, model in models.items():
                    rows.append((series, origin, h, cols[t + h], values[i, t + h], float(model(history, h, hist_valid)), name))
    return pd.DataFrame(rows, columns=["series", "origin", "horizon", "target", "actual", "pred", "model"])

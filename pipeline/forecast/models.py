# 예측 모델: 꾸준한 품목용 지수평활(SES), 몰아 나가는 품목용 간헐 수요 모델(TSB: 출고 확률 × 로트 크기)
import numpy as np

SES_ALPHA = 0.3
TSB_ALPHA_P = 0.1   # 출고 확률 갱신 속도
TSB_ALPHA_Z = 0.3   # 로트 크기 갱신 속도


def _clean(history, valid):
    history = np.asarray(history, dtype=float)
    if valid is None:
        return history
    return history[np.asarray(valid, dtype=bool)]


def ses(history, horizon=1, valid=None, alpha=SES_ALPHA):
    x = _clean(history, valid)
    if len(x) == 0:
        return 0.0
    level = x[0]
    for v in x[1:]:
        level = level + alpha * (v - level)
    return float(level)


def tsb(history, horizon=1, valid=None, alpha_p=TSB_ALPHA_P, alpha_z=TSB_ALPHA_Z):
    x = _clean(history, valid)
    if len(x) == 0 or (x > 0).sum() == 0:
        return 0.0
    p = float((x > 0).mean())
    z = float(x[x > 0].mean())
    for v in x:
        if v > 0:
            p = p + alpha_p * (1 - p)
            z = z + alpha_z * (v - z)
        else:
            p = p * (1 - alpha_p)
    return float(p * z)

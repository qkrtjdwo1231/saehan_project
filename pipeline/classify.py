# 품목을 묶음(월말전표/청주생산/기타)과 수요 유형(A 꾸준함 / B 몰아 나감 / C 드묾)으로 판정하는 규칙
MONTH_END_PREFIX = "AMBT"
TYPE_A_MIN_SHARE = 0.5
TYPE_B_MIN_SHARE = 0.1


def item_group(item_code, produced):
    if item_code.startswith(MONTH_END_PREFIX):
        return "월말전표"
    if item_code in produced:
        return "청주생산"
    return "기타"


def demand_type(weekly_qty):
    if len(weekly_qty) == 0:
        return "C"
    share = (weekly_qty > 0).mean()
    if share >= TYPE_A_MIN_SHARE:
        return "A"
    if share >= TYPE_B_MIN_SHARE:
        return "B"
    return "C"

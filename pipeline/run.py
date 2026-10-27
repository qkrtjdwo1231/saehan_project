# ERP 덤프 폴더를 읽어 data/processed/ 에 정리된 CSV(일별 판매·생산, 품목표, 주간 집계)를 만드는 실행 스크립트
import glob
import os
import sys

import pandas as pd

from pipeline.load import read_sales, read_production
from pipeline.classify import item_group, demand_type
from pipeline.aggregate import weekly_by_type_customer, plant1_outage, week_start

DEMAND_TYPE_YEAR = 2025


def _load_all(src):
    sales = pd.concat([read_sales(p) for p in sorted(glob.glob(os.path.join(src, "*판매실적*.xls")))], ignore_index=True)
    prod = pd.concat([read_production(p) for p in sorted(glob.glob(os.path.join(src, "*생산실적*.xls")))], ignore_index=True)
    return sales, prod


def _main_dept(prod):
    by = prod[prod["doc_type"].isin(["21", "22"])].groupby(["item_code", "dept"])["qty_a"].sum().reset_index()
    by = by.sort_values(["item_code", "qty_a"], ascending=[True, False]).drop_duplicates("item_code")
    return by.set_index("item_code")["dept"].astype(int)


def _items(sales, prod):
    produced = set(prod["item_code"])
    first = sales.sort_values("date").drop_duplicates("item_code").set_index("item_code")
    items = pd.DataFrame({
        "item_type": first["item_type"],
        "item_name": first["item_name"],
    })
    items["group"] = [item_group(c, produced) for c in items.index]
    items["main_dept"] = _main_dept(prod).reindex(items.index)
    main_customer = (sales[sales["ship_type"] == "정상"].groupby(["item_code", "customer"])["qty"].sum()
                     .reset_index().sort_values(["item_code", "qty"], ascending=[True, False])
                     .drop_duplicates("item_code").set_index("item_code")["customer"])
    items["main_customer"] = main_customer.reindex(items.index)
    ref = sales[(sales["ship_type"] == "정상") & (sales["date"].dt.year == DEMAND_TYPE_YEAR)]
    weeks = pd.date_range(f"{DEMAND_TYPE_YEAR}-01-01", f"{DEMAND_TYPE_YEAR}-12-31", freq="W-MON")
    weekly = ref.assign(week_start=week_start(ref["date"])).groupby(["item_code", "week_start"])["qty"].sum().unstack(fill_value=0)
    weekly = weekly.reindex(columns=weeks, fill_value=0)
    items["demand_type"] = [
        "C" if items.loc[c, "group"] == "월말전표" else demand_type(weekly.loc[c]) if c in weekly.index else "C"
        for c in items.index
    ]
    items["qty_2025"] = ref.groupby("item_code")["qty"].sum().reindex(items.index).fillna(0).astype("int64")
    return items.reset_index().rename(columns={"index": "item_code"})


def build(src, out):
    os.makedirs(out, exist_ok=True)
    sales, prod = _load_all(src)
    items = _items(sales, prod)
    group_of = items.set_index("item_code")["group"]
    dept_of = items.set_index("item_code")["main_dept"]

    sales = sales.assign(group=sales["item_code"].map(group_of))
    sales["plant1_outage"] = plant1_outage(sales["date"]).values & sales["item_code"].map(dept_of).isin([1211, 1212]).values
    prod = prod.assign(plant1_outage=plant1_outage(prod["date"]).values & prod["dept"].isin(["1211", "1212"]).values)

    normal = sales[(sales["ship_type"] == "정상") & (sales["group"] == "청주생산")]
    weekly = weekly_by_type_customer(normal[["date", "item_type", "customer", "qty"]])

    sales.to_csv(os.path.join(out, "sales_daily.csv"), index=False, encoding="utf-8-sig")
    prod.to_csv(os.path.join(out, "prod_daily.csv"), index=False, encoding="utf-8-sig")
    items.to_csv(os.path.join(out, "items.csv"), index=False, encoding="utf-8-sig")
    weekly.to_csv(os.path.join(out, "weekly.csv"), index=False, encoding="utf-8-sig")

    summary = {
        "sales_rows": len(sales), "sales_qty": int(sales["qty"].sum()),
        "prod_rows": len(prod), "prod_qty_a": int(prod["qty_a"].sum()),
        "items": len(items), "weekly_rows": len(weekly), "weekly_qty": int(weekly["qty"].sum()),
        "cheongju_normal_qty": int(normal["qty"].sum()),
        "group_counts": items["group"].value_counts().to_dict(),
        "demand_type_counts": items[items["group"] == "청주생산"]["demand_type"].value_counts().to_dict(),
    }
    return summary


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "2025년 판매실적"
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join("data", "processed")
    s = build(src, out)
    for k, v in s.items():
        print(f"{k}: {v}")
    assert s["weekly_qty"] == s["cheongju_normal_qty"], "주간 집계 합계가 일별 합계와 다름"
    print("OK: 주간 집계 합계 = 청주 생산 품목 정상 출고 합계")

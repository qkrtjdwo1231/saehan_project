// 수요 예측: 품종×거래처 계열별 유형, 최근 실적, 다음 1~4주 예측, 4주 소요량
"use client";
import { Suspense, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { getDocument, fmt } from "@/lib/data";
import Sparkline from "@/components/Sparkline";
import TypeBadge from "@/components/TypeBadge";

function ForecastInner() {
  const params = useSearchParams();
  const [fc, setFc] = useState(null);
  const [q, setQ] = useState(params.get("q") || "");
  const [types, setTypes] = useState({ A: true, B: true, C: false });
  const [err, setErr] = useState("");
  useEffect(() => { getDocument("forecast").then(setFc).catch((e) => setErr(e.message)); }, []);

  const rows = useMemo(() => {
    if (!fc) return [];
    const k = q.trim().toLowerCase();
    return fc.series.filter((r) => types[r.demand_type]).filter((r) => !k || r.item_type.toLowerCase().includes(k) || r.customer.toLowerCase().includes(k) || (r.item_name || "").toLowerCase().includes(k) || (r.item_codes || []).some((c) => c.toLowerCase().includes(k))).slice(0, 300);
  }, [fc, q, types]);

  if (err) return <div className="notice">{err}</div>;
  if (!fc) return <p className="muted">불러오는 중...</p>;
  return (
    <>
      <h1>수요 예측</h1>
      <p className="sub">기준 {fc.as_of} · 예측 주 {fc.forecast_weeks[0]} ~ {fc.forecast_weeks[3]} · 단위 개 · 계절지수 {Object.entries(fc.season_index).map(([m, v]) => `${m}월 ${v}`).join(", ")} · 연휴 주 {fc.holiday_factors.holiday_week}, 연휴 전 주 {fc.holiday_factors.pre_holiday_week}</p>
      <div className="toolbar">
        <input type="text" placeholder="품종·품번·품명·거래처 검색" value={q} onChange={(e) => setQ(e.target.value)} />
        {["A", "B", "C"].map((t) => <button key={t} className={"btn" + (types[t] ? " on" : "")} onClick={() => setTypes({ ...types, [t]: !types[t] })}>{t === "A" ? "A 꾸준함" : t === "B" ? "B 몰아 나감" : "C 드묾"}</button>)}
        <span className="muted">{rows.length}개 표시 (최대 300)</span>
      </div>
      <div className="notice">B 유형은 이력만으로 주별 수량을 맞히기 어렵습니다. 주별 값은 회색 참고값이고 <b>4주 소요량</b>을 보세요. 거래처가 미리 알려주는 주문이 있으면 그 값을 우선합니다.</div>
      <div className="card">
        <table>
          <thead><tr><th>품종</th><th>대표 품명</th><th>거래처</th><th>유형</th><th>최근 12주</th><th className="num">올해 실적</th>{fc.forecast_weeks.map((w) => <th key={w} className="num">{w.slice(5)}</th>)}<th className="num">4주 소요량</th></tr></thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.series}>
                <td className="bold">{r.item_type}</td>
                <td className="muted">{r.item_name}</td>
                <td>{r.customer}</td>
                <td><TypeBadge type={r.demand_type} /></td>
                <td><Sparkline values={r.recent} /></td>
                <td className="num muted">{fmt(r.qty_year)}</td>
                {r.forecast.map((v, i) => <td key={i} className={"num" + (r.demand_type === "A" ? "" : " dim")}>{fmt(v)}</td>)}
                <td className={"num" + (r.demand_type === "A" ? "" : " bold")}>{fmt(r.forecast_4w)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

export default function ForecastPage() {
  return <Suspense fallback={<p className="muted">불러오는 중...</p>}><ForecastInner /></Suspense>;
}

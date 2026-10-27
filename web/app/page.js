// 홈: 다음 4주 공장 총량 예측, 4주 소요량 상위 품목, 유형 분포, 이번 달 변경 건수
"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { getDocument, listChanges, fmtK, fmt } from "@/lib/data";
import TypeBadge from "@/components/TypeBadge";

export default function Home() {
  const [fc, setFc] = useState(null);
  const [changes, setChanges] = useState([]);
  const [err, setErr] = useState("");
  useEffect(() => {
    getDocument("forecast").then(setFc).catch((e) => setErr(e.message));
    listChanges().then(setChanges).catch(() => {});
  }, []);
  if (err) return <div className="notice">{err}</div>;
  if (!fc) return <p className="muted">불러오는 중...</p>;

  const chart = [
    ...fc.totals.recent_weeks.map((w, i) => ({ week: w.slice(5), actual: fc.totals.recent[i], kind: "actual" })),
    ...fc.forecast_weeks.map((w, i) => ({ week: w.slice(5), forecast: fc.totals.forecast[i], kind: "forecast" })),
  ];
  const byType = fc.series.reduce((a, r) => { a[r.demand_type] = (a[r.demand_type] || 0) + 1; return a; }, {});
  const top = fc.series.slice(0, 10);
  const month = new Date().toISOString().slice(0, 7);
  const changesThisMonth = changes.filter((c) => (c.ts || "").slice(0, 7) === month).length;
  const sum4 = fc.totals.forecast.reduce((a, b) => a + b, 0);

  return (
    <>
      <h1>오늘 한눈에</h1>
      <p className="sub">기준 시점 {fc.as_of} · 예측 방식 {fc.model}</p>
      <div className="grid cols-4" style={{ marginBottom: 16 }}>
        <div className="card kpi"><div className="label">다음 주 예측 출고량</div><div className="value">{fmtK(fc.totals.forecast[0])}</div><div className="note">{fc.forecast_weeks[0]} 주, 개</div></div>
        <div className="card kpi"><div className="label">다음 4주 소요량 합계</div><div className="value orange">{fmtK(sum4)}</div><div className="note">청주 생산 품목, 품종×거래처 합산</div></div>
        <div className="card kpi"><div className="label">예측 계열 수</div><div className="value">{fc.series.length.toLocaleString()}</div><div className="note">A {byType.A || 0} · B {byType.B || 0} · C {byType.C || 0}</div></div>
        <div className="card kpi"><div className="label">이번 달 계획 변경</div><div className="value">{changesThisMonth}</div><div className="note"><Link href="/changes">변경 이력 보기</Link></div></div>
      </div>
      <div className="grid cols-2">
        <div className="card">
          <h2>주간 출고량 · 최근 12주 실적과 다음 4주 예측 (개)</h2>
          <div style={{ width: "100%", height: 280 }}>
            <ResponsiveContainer>
              <BarChart data={chart} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
                <XAxis dataKey="week" tick={{ fontSize: 11 }} />
                <YAxis tickFormatter={(v) => fmtK(v)} tick={{ fontSize: 11 }} width={60} />
                <Tooltip formatter={(v) => fmt(v)} />
                <Bar dataKey="actual" name="실적" fill="#1e3a5f" />
                <Bar dataKey="forecast" name="예측" fill="#e07b2a" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <p className="muted" style={{ fontSize: 12 }}>남색은 실제 출고, 주황은 예측입니다. 근거는 <Link href="/forecast">수요 예측</Link> 화면의 품종×거래처 예측값을 모두 더한 것입니다.</p>
        </div>
        <div className="card">
          <h2>다음 4주 소요량 상위 10</h2>
          <div className="notice">현재고 자료가 없어 "부족 예상" 대신 소요량 상위 품목을 보여줍니다. 재고를 입력하면 <Link href="/inventory">가용재고</Link>에서 소진 예상일이 계산됩니다.</div>
          <table>
            <thead><tr><th>품종</th><th>품명</th><th>거래처</th><th>유형</th><th className="num">4주 소요량</th></tr></thead>
            <tbody>
              {top.map((r) => (
                <tr key={r.series}>
                  <td><Link href={`/forecast?q=${encodeURIComponent(r.item_type)}`} className="bold">{r.item_type}</Link></td>
                  <td className="muted">{r.item_name}</td><td>{r.customer}</td><td><TypeBadge type={r.demand_type} /></td>
                  <td className="num">{fmt(r.forecast_4w)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <p className="footer">2021~2025년 실적으로 만든 예측입니다. 2025년을 모르는 상태에서 매주 예측해 검증했고, 몰아서 나가는 품목(B)은 주별 값보다 4주 소요량을 보는 것이 맞습니다.</p>
    </>
  );
}

// 가용재고 보드: 품종별 현재고(입력) + 4주 출고 예정(예측) + 생산 예정(계획) → 소진 예상 주
"use client";
import { useEffect, useMemo, useState } from "react";
import { getDocument, getInventory, setInventory, getPlan, getUser, fmt } from "@/lib/data";
import TypeBadge from "@/components/TypeBadge";

export default function InventoryPage() {
  const [fc, setFc] = useState(null);
  const [inv, setInv] = useState({});
  const [cells, setCells] = useState([]);
  const [q, setQ] = useState("");
  const [err, setErr] = useState("");
  useEffect(() => {
    getDocument("forecast").then(async (f) => { setFc(f); setInv(await getInventory()); setCells(await getPlan(f.forecast_weeks[0])); }).catch((e) => setErr(e.message));
  }, []);

  const rows = useMemo(() => {
    if (!fc) return [];
    const by = {};
    for (const r of fc.series) {
      const d = by[r.item_type] || (by[r.item_type] = { item_type: r.item_type, item_name: r.item_name, out4: 0, types: new Set(), customers: new Set() });
      d.out4 += r.forecast_4w; d.types.add(r.demand_type); d.customers.add(r.customer);
    }
    const planned = {};
    for (const c of cells) planned[c.item_type] = (planned[c.item_type] || 0) + Number(c.qty);
    const k = q.trim().toLowerCase();
    return Object.values(by).map((d) => {
      const stock = inv[d.item_type]?.qty;
      const weekly = d.out4 / 4;
      const weeks = stock == null ? null : weekly > 0 ? (Number(stock) + (planned[d.item_type] || 0)) / weekly : Infinity;
      const type = d.types.has("A") ? "A" : d.types.has("B") ? "B" : "C";
      return { ...d, type, stock, planned: planned[d.item_type] || 0, weekly, weeks };
    }).filter((d) => d.out4 > 0).filter((d) => !k || d.item_type.toLowerCase().includes(k) || (d.item_name || "").toLowerCase().includes(k))
      .sort((a, b) => (a.weeks ?? 99) - (b.weeks ?? 99) || b.out4 - a.out4).slice(0, 300);
  }, [fc, inv, cells, q]);

  if (err) return <div className="notice">{err}</div>;
  if (!fc) return <p className="muted">불러오는 중...</p>;
  return (
    <>
      <h1>가용재고 보드</h1>
      <p className="sub">소진 예상 = (현재고 + 이번 주 생산 예정) ÷ 주당 출고 예정. 단위 개. 기준 {fc.as_of}.</p>
      <div className="notice">현재고 자료(제품수불표)가 아직 없습니다. 현재고 칸에 숫자를 넣으면 소진 예상이 계산되고 저장됩니다. ERP 재고 파일을 받으면 자동으로 채워집니다.</div>
      <div className="toolbar"><input type="text" placeholder="품종·품명 검색" value={q} onChange={(e) => setQ(e.target.value)} /><span className="muted">{rows.length}개 표시</span></div>
      <div className="card">
        <table>
          <thead><tr><th>품종</th><th>품명</th><th>유형</th><th className="num">현재고 (입력)</th><th className="num">주당 출고 예정</th><th className="num">4주 출고 예정</th><th className="num">생산 예정</th><th>소진 예상</th><th>상태</th></tr></thead>
          <tbody>
            {rows.map((d) => (
              <tr key={d.item_type}>
                <td className="bold">{d.item_type}</td><td className="muted">{d.item_name}</td><td><TypeBadge type={d.type} /></td>
                <td className="num"><input className="cell-input" type="number" defaultValue={d.stock ?? ""} placeholder="미입력" onBlur={async (e) => { if (e.target.value === "") return; await setInventory(d.item_type, Number(e.target.value), getUser()); setInv(await getInventory()); }} /></td>
                <td className="num">{fmt(d.weekly)}</td><td className="num">{fmt(d.out4)}</td><td className="num">{fmt(d.planned)}</td>
                <td>{d.weeks == null ? <span className="muted">현재고 필요</span> : d.weeks === Infinity ? "여유" : `${d.weeks.toFixed(1)}주 (약 ${Math.round(d.weeks * 7)}일)`}</td>
                <td>{d.weeks == null ? <span className="status-pill none">미입력</span> : d.weeks < 1 ? <span className="status-pill bad">1주 미만</span> : d.weeks < 2 ? <span className="status-pill warn">2주 미만</span> : <span className="status-pill ok">충분</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

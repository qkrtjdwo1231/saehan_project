// 변경 이력: 배포 후 계획 수정 목록과 사유별 집계
"use client";
import { useEffect, useMemo, useState } from "react";
import { DAYS, REASONS, listChanges, fmt } from "@/lib/data";

export default function ChangesPage() {
  const [rows, setRows] = useState([]);
  useEffect(() => { listChanges().then(setRows); }, []);
  const month = new Date().toISOString().slice(0, 7);
  const summary = useMemo(() => {
    const s = Object.fromEntries(REASONS.map((r) => [r, 0]));
    for (const c of rows) if ((c.ts || "").slice(0, 7) === month) s[c.reason] = (s[c.reason] || 0) + 1;
    return s;
  }, [rows, month]);
  return (
    <>
      <h1>변경 이력</h1>
      <p className="sub">배포된 계획을 고칠 때마다 자동으로 한 줄이 남습니다. 어떤 이유로 계획이 흔들리는지 보는 자료입니다.</p>
      <div className="grid cols-4" style={{ marginBottom: 16 }}>
        {REASONS.slice(0, 4).map((r) => <div key={r} className="card kpi"><div className="label">{month} · {r}</div><div className="value">{summary[r]}</div></div>)}
      </div>
      <div className="card">
        <table>
          <thead><tr><th>시각</th><th>담당자</th><th>계획 주</th><th>설비</th><th>요일</th><th>품종</th><th className="num">변경 전</th><th className="num">변경 후</th><th>사유</th><th>메모</th></tr></thead>
          <tbody>
            {rows.length === 0 && <tr><td colSpan={10} className="muted">아직 변경 기록이 없습니다. 주간 생산계획을 배포한 뒤 수정하면 여기에 쌓입니다.</td></tr>}
            {rows.map((c, i) => (
              <tr key={c.id || i}>
                <td>{new Date(c.ts).toLocaleString("ko-KR")}</td><td>{c.user_name}</td><td>{c.week_start}</td><td>{c.machine}</td><td>{DAYS[c.day]}</td><td className="bold">{c.item_type}</td>
                <td className="num">{fmt(c.qty_before)}</td><td className="num">{fmt(c.qty_after)}</td><td>{c.reason}</td><td className="muted">{c.memo}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

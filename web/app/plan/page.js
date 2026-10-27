// 주간 생산계획: 왼쪽 미배정 소요량(예측 기반) → 오른쪽 설비×요일 격자에 배치, 배포로 버전 고정, 배포 후 수정은 사유와 함께 기록
"use client";
import { useEffect, useMemo, useState } from "react";
import { DAYS, getDocument, getPlan, setCell, getVersion, publish, addChange, getUser, fmt } from "@/lib/data";
import ReasonModal from "@/components/ReasonModal";

const DEPT_NAME = { 1211: "1공장 PET1팀", 1212: "1공장 PE팀", 1219: "2공장 PET2팀" };

export default function PlanPage() {
  const [fc, setFc] = useState(null);
  const [machines, setMachines] = useState([]);
  const [cells, setCells] = useState([]);
  const [version, setVersion] = useState(null);
  const [selected, setSelected] = useState(null);
  const [pending, setPending] = useState(null);
  const [err, setErr] = useState("");
  const week = fc?.forecast_weeks?.[0];

  useEffect(() => {
    Promise.all([getDocument("forecast"), getDocument("machines")]).then(([f, m]) => { setFc(f); setMachines(m); }).catch((e) => setErr(e.message));
  }, []);
  useEffect(() => { if (week) { getPlan(week).then(setCells); getVersion(week).then(setVersion); } }, [week]);

  const demand = useMemo(() => {
    if (!fc) return [];
    const by = {};
    for (const r of fc.series) {
      if (r.demand_type === "C") continue;
      const d = by[r.item_type] || (by[r.item_type] = { item_type: r.item_type, item_name: r.item_name, need: 0, customers: new Set(), dept: r.main_dept });
      d.need += r.forecast_4w / 4; d.customers.add(r.customer);
    }
    const assigned = {};
    for (const c of cells) assigned[c.item_type] = (assigned[c.item_type] || 0) + Number(c.qty);
    return Object.values(by).map((d) => ({ ...d, assigned: assigned[d.item_type] || 0, left: d.need - (assigned[d.item_type] || 0) })).sort((a, b) => b.need - a.need);
  }, [fc, cells]);

  const grid = useMemo(() => {
    const g = {};
    for (const c of cells) (g[`${c.machine}|${c.day}`] = g[`${c.machine}|${c.day}`] || []).push(c);
    return g;
  }, [cells]);

  async function applyCell(machineKey, day, item_type, qty, reason, memo) {
    const before = (grid[`${machineKey}|${day}`] || []).find((c) => c.item_type === item_type)?.qty || 0;
    await setCell(week, machineKey, day, item_type, qty, getUser());
    if (version) await addChange({ week_start: week, user_name: getUser(), machine: machineKey, day, item_type, qty_before: before, qty_after: qty, reason, memo });
    setCells(await getPlan(week));
  }

  function requestChange(machineKey, day, item_type, qty) {
    if (version) setPending({ machineKey, day, item_type, qty });
    else applyCell(machineKey, day, item_type, qty);
  }

  function onCellClick(machineKey, day) {
    if (!selected) return;
    const existing = (grid[`${machineKey}|${day}`] || []).find((c) => c.item_type === selected.item_type);
    if (existing) return;
    requestChange(machineKey, day, selected.item_type, Math.max(0, Math.round(selected.left > 0 ? Math.min(selected.left, selected.need) : selected.need)));
  }

  if (err) return <div className="notice">{err}</div>;
  if (!fc) return <p className="muted">불러오는 중...</p>;

  const deptOrder = ["1219", "1211", "1212"];
  const byDept = deptOrder.map((d) => [d, machines.filter((m) => m.dept === d)]).filter(([, ms]) => ms.length);

  return (
    <>
      <h1>주간 생산계획 · {week} 주</h1>
      <p className="sub">왼쪽에서 품종을 고른 뒤 오른쪽 격자 칸을 누르면 배치됩니다. 수량은 칸 안에서 바로 고칠 수 있습니다. 단위 개.</p>
      <div className="toolbar">
        {version
          ? <><span className="status-pill ok">배포됨 · {new Date(version.published_at).toLocaleString("ko-KR")} · {version.published_by}</span><button className="btn" onClick={async () => { await publish(week, getUser(), true); setVersion(null); }}>배포 해제 (시연용)</button></>
          : <><span className="status-pill none">작성 중</span><button className="btn primary" onClick={async () => setVersion(await publish(week, getUser()))}>이 계획 배포 (버전 고정)</button></>}
        <span className="muted">배포 후의 수정은 사유와 함께 변경 이력에 남습니다.</span>
      </div>
      <div className="notice">설비별 생산 가능 품목과 시간당 생산량 자료가 없어 자동 배정과 과부하 경고는 아직 없습니다. 품종을 고르면 2025년에 그 품종을 만든 적 있는 설비가 파란색으로 표시됩니다.</div>
      <div className="plan-layout">
        <div className="card">
          <h2>미배정 소요량 (주당, A·B 유형)</h2>
          <div className="demand-list">
            {demand.map((d) => (
              <div key={d.item_type} className={"demand-item" + (selected?.item_type === d.item_type ? " selected" : "")} onClick={() => setSelected(selected?.item_type === d.item_type ? null : d)}>
                <div><div className="bold">{d.item_type}</div><div className="name muted">{d.item_name} · {[...d.customers].slice(0, 2).join(", ")}{d.customers.size > 2 ? ` 외 ${d.customers.size - 2}` : ""}</div></div>
                <div className="left" style={{ color: d.left <= 0 ? "#2e8b57" : undefined }}>{d.left <= 0 ? "배정 완료" : `${fmt(d.left)} 남음`}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="card plan-grid">
          <table>
            <thead><tr><th>설비</th>{DAYS.map((d, i) => <th key={d}>{d} <span className="muted" style={{ fontWeight: 400 }}>{addDays(week, i)}</span></th>)}</tr></thead>
            <tbody>
              {byDept.map(([dept, ms]) => (
                <Row key={dept} dept={dept} ms={ms} grid={grid} selected={selected} onCellClick={onCellClick} requestChange={requestChange} />
              ))}
            </tbody>
          </table>
        </div>
      </div>
      {pending && <ReasonModal onCancel={() => setPending(null)} onConfirm={async (reason, memo) => { const p = pending; setPending(null); await applyCell(p.machineKey, p.day, p.item_type, p.qty, reason, memo); }} />}
    </>
  );
}

function Row({ dept, ms, grid, selected, onCellClick, requestChange }) {
  return (
    <>
      <tr className="dept-row"><td colSpan={8}>{DEPT_NAME[dept] || dept}</td></tr>
      {ms.map((m) => {
        const key = `${m.dept}|${m.machine}`;
        const hint = selected && (m.item_types || []).includes(selected.item_type);
        return (
          <tr key={key}>
            <td className="machine">{m.machine}<div className="muted" style={{ fontSize: 11, fontWeight: 400 }}>{m.active_days}일 가동</div></td>
            {DAYS.map((_, day) => (
              <td key={day} className={"cell" + (hint ? " hint" : "")} onClick={(e) => { if (e.target.tagName !== "INPUT" && e.target.className !== "x") onCellClick(key, day); }}>
                {(grid[`${key}|${day}`] || []).map((c) => (
                  <div key={c.item_type} className="entry">
                    <span title={c.item_type}>{c.item_type}</span>
                    <input className="cell-input" type="number" defaultValue={c.qty} onBlur={(e) => { const v = Number(e.target.value); if (v !== Number(c.qty)) requestChange(key, day, c.item_type, v); }} />
                    <span className="x" onClick={() => requestChange(key, day, c.item_type, 0)}>×</span>
                  </div>
                ))}
              </td>
            ))}
          </tr>
        );
      })}
    </>
  );
}

function addDays(iso, n) {
  if (!iso) return "";
  const d = new Date(iso + "T00:00:00"); d.setDate(d.getDate() + n);
  return `${d.getMonth() + 1}/${d.getDate()}`;
}

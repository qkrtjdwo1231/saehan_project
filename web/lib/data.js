// 화면이 쓰는 데이터 계층. 읽기(예측·설비)는 수파베이스 documents 표 → 없으면 /data/*.json. 쓰기(재고·계획·변경)는 수파베이스 → 없으면 브라우저 저장소
import { supabase } from "./supabase";

export const REASONS = ["거래처 주문 변경", "설비 고장", "원부자재 부족", "인원 부족", "품질", "기타"];
export const DAYS = ["월", "화", "수", "목", "금", "토", "일"];
export const USERS = ["담당자 A", "담당자 B", "담당자 C"];

const local = {
  get(key, fallback) {
    if (typeof window === "undefined") return fallback;
    try { const v = window.localStorage.getItem(key); return v ? JSON.parse(v) : fallback; } catch { return fallback; }
  },
  set(key, value) {
    if (typeof window === "undefined") return;
    try { window.localStorage.setItem(key, JSON.stringify(value)); } catch {}
  },
};

export function getUser() { return local.get("user", USERS[0]); }
export function setUser(name) { local.set("user", name); }

export async function getDocument(name) {
  if (supabase) {
    const { data, error } = await supabase.from("documents").select("data").eq("key", name).maybeSingle();
    if (!error && data) return data.data;
  }
  const res = await fetch(`/data/${name}.json`);
  if (!res.ok) throw new Error(`${name} 데이터가 없습니다. 수파베이스 documents 표 또는 /data/${name}.json을 확인하세요.`);
  return res.json();
}

export async function getInventory() {
  if (supabase) {
    const { data, error } = await supabase.from("inventory").select("item_type, qty, updated_by, updated_at");
    if (!error && data) return Object.fromEntries(data.map((r) => [r.item_type, r]));
  }
  return local.get("inventory", {});
}

export async function setInventory(item_type, qty, user) {
  const row = { item_type, qty, updated_by: user, updated_at: new Date().toISOString() };
  if (supabase) {
    const { error } = await supabase.from("inventory").upsert(row, { onConflict: "item_type" });
    if (!error) return row;
  }
  const inv = local.get("inventory", {}); inv[item_type] = row; local.set("inventory", inv);
  return row;
}

export async function getPlan(week_start) {
  if (supabase) {
    const { data, error } = await supabase.from("plan_cells").select("*").eq("week_start", week_start);
    if (!error && data) return data;
  }
  return local.get(`plan:${week_start}`, []);
}

export async function setCell(week_start, machine, day, item_type, qty, user) {
  const row = { week_start, machine, day, item_type, qty, updated_by: user, updated_at: new Date().toISOString() };
  if (supabase) {
    if (qty > 0) {
      const { error } = await supabase.from("plan_cells").upsert(row, { onConflict: "week_start,machine,day,item_type" });
      if (!error) return;
    } else {
      const { error } = await supabase.from("plan_cells").delete().match({ week_start, machine, day, item_type });
      if (!error) return;
    }
  }
  const cells = local.get(`plan:${week_start}`, []).filter((c) => !(c.machine === machine && c.day === day && c.item_type === item_type));
  if (qty > 0) cells.push(row);
  local.set(`plan:${week_start}`, cells);
}

export async function getVersion(week_start) {
  if (supabase) {
    const { data, error } = await supabase.from("plan_versions").select("*").eq("week_start", week_start).order("id", { ascending: false }).limit(1).maybeSingle();
    if (!error) return data;
  }
  return local.get(`version:${week_start}`, null);
}

export async function publish(week_start, user, unpublish = false) {
  const row = unpublish ? null : { week_start, name: `${week_start} 주간계획`, published_at: new Date().toISOString(), published_by: user };
  if (supabase) {
    if (unpublish) { const { error } = await supabase.from("plan_versions").delete().eq("week_start", week_start); if (!error) return null; }
    else { const { error } = await supabase.from("plan_versions").insert(row); if (!error) return row; }
  }
  local.set(`version:${week_start}`, row);
  return row;
}

export async function listChanges(limit = 500) {
  if (supabase) {
    const { data, error } = await supabase.from("plan_changes").select("*").order("ts", { ascending: false }).limit(limit);
    if (!error && data) return data;
  }
  return local.get("changes", []).slice().reverse();
}

export async function addChange(entry) {
  const row = { ts: new Date().toISOString(), ...entry };
  if (supabase) {
    const { error } = await supabase.from("plan_changes").insert(row);
    if (!error) return row;
  }
  const list = local.get("changes", []); list.push(row); local.set("changes", list);
  return row;
}

export const fmt = (n) => (n == null || isNaN(n) ? "-" : Math.round(n).toLocaleString("ko-KR"));
export const fmtK = (n) => (n == null || isNaN(n) ? "-" : Math.abs(n) >= 1e6 ? (n / 1e6).toFixed(2) + "백만" : Math.abs(n) >= 1e4 ? (n / 1e4).toFixed(1) + "만" : Math.round(n).toLocaleString("ko-KR"));
export const usingSupabase = () => !!supabase;

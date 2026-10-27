// 상단 메뉴와 담당자 선택(변경 이력의 "누가" 기록용)
"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { USERS, getUser, setUser, usingSupabase } from "@/lib/data";

const LINKS = [["/", "홈"], ["/forecast", "수요 예측"], ["/plan", "주간 생산계획"], ["/inventory", "가용재고"], ["/changes", "변경 이력"]];

export default function Nav() {
  const path = usePathname();
  const [user, setU] = useState(USERS[0]);
  useEffect(() => { setU(getUser()); }, []);
  return (
    <nav className="nav">
      <span className="brand"><span className="dot" />새한프라텍 생산계획 보드</span>
      {LINKS.map(([href, label]) => (
        <Link key={href} href={href} className={"link" + (path === href ? " active" : "")}>{label}</Link>
      ))}
      <span className="right">
        <span>{usingSupabase() ? "수파베이스 연결" : "로컬 데이터"}</span>
        <select value={user} onChange={(e) => { setU(e.target.value); setUser(e.target.value); }}>
          {USERS.map((u) => <option key={u}>{u}</option>)}
        </select>
      </span>
    </nav>
  );
}

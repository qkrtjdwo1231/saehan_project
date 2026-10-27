// 배포된 계획을 고칠 때 사유를 고르게 하는 창 (브라우저 기본 대화상자 대신 사용)
"use client";
import { useState } from "react";
import { REASONS } from "@/lib/data";

export default function ReasonModal({ title, onConfirm, onCancel }) {
  const [reason, setReason] = useState(REASONS[0]);
  const [memo, setMemo] = useState("");
  return (
    <div className="modal-bg">
      <div className="modal">
        <h3>{title || "변경 사유"}</h3>
        <p className="muted" style={{ marginTop: 0 }}>배포된 계획을 바꾸면 이력에 남습니다. 이유를 골라 주세요.</p>
        <select value={reason} onChange={(e) => setReason(e.target.value)}>
          {REASONS.map((r) => <option key={r}>{r}</option>)}
        </select>
        <textarea rows={3} placeholder="메모 (선택)" value={memo} onChange={(e) => setMemo(e.target.value)} />
        <div className="actions">
          <button className="btn" onClick={onCancel}>취소</button>
          <button className="btn primary" onClick={() => onConfirm(reason, memo)}>기록하고 변경</button>
        </div>
      </div>
    </div>
  );
}

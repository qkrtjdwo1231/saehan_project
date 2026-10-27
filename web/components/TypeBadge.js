// 수요 유형(A 꾸준함, B 몰아 나감, C 드묾) 표시
const LABEL = { A: "꾸준함", B: "몰아 나감", C: "드묾" };
export default function TypeBadge({ type }) {
  return <span className={"badge " + type} title={LABEL[type] || ""}>{type} {LABEL[type] || ""}</span>;
}

// 최근 주별 실적을 작은 선 그래프로 보여주는 부품
export default function Sparkline({ values, width = 90, height = 24 }) {
  if (!values || values.length === 0) return null;
  const max = Math.max(...values, 1);
  const step = width / Math.max(values.length - 1, 1);
  const pts = values.map((v, i) => `${(i * step).toFixed(1)},${(height - 2 - (v / max) * (height - 4)).toFixed(1)}`).join(" ");
  return (
    <svg width={width} height={height} aria-label="최근 실적">
      <polyline points={pts} fill="none" stroke="#5b84b1" strokeWidth="1.5" />
    </svg>
  );
}

import { SIZES, StockLevel, stockLevel } from "../api";

// Color-blind-safe size availability (Problem 9). Each state differs by shape + symbol + text,
// not just color: in stock = solid blue chip, low = amber chip with "!", sold out = dashed gray
// outline, struck through, with "✕". Screen readers get the full sentence in aria-label.
const WORD: Record<StockLevel, string> = { in: "in stock", low: "only a few left", out: "sold out" };

export default function SizeStrip({ sizeStock, compact = false }: { sizeStock?: Record<string, number>; compact?: boolean }) {
  if (!sizeStock || !Object.keys(sizeStock).length) return null;
  return (
    <ul className={`size-strip${compact ? " compact" : ""}`} aria-label="Sizes">
      {SIZES.map((s) => {
        const q = sizeStock[s] ?? 0;
        const level = stockLevel(q);
        return (
          <li key={s} className={`ss ss-${level}`} aria-label={`${s}: ${WORD[level]}${level === "low" ? ` (${q})` : ""}`} title={`${s}: ${WORD[level]}${level !== "out" ? ` (${q})` : ""}`}>
            {s}
            {level === "low" && <span className="ss-mark" aria-hidden>!</span>}
            {level === "out" && <span className="ss-mark" aria-hidden>✕</span>}
          </li>
        );
      })}
    </ul>
  );
}

export function SizeLegend() {
  return (
    <p className="size-legend" aria-label="Size legend">
      <span className="ss ss-in">M</span> in stock
      <span className="ss ss-low">M<span className="ss-mark">!</span></span> 5 or fewer left
      <span className="ss ss-out">M<span className="ss-mark">✕</span></span> sold out
    </p>
  );
}

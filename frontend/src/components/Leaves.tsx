// Decorative autumn leaves drifting across the hero (Problem 10). Purely visual:
// aria-hidden, pointer-events off, and frozen for prefers-reduced-motion (see styles.css).
const LEAVES = [
  { left: "6%", delay: "0s", dur: "13s", size: 22, color: "#c8892b", rot: 20 },
  { left: "22%", delay: "4s", dur: "16s", size: 16, color: "#a8452a", rot: -30 },
  { left: "41%", delay: "8s", dur: "14s", size: 20, color: "#d4a23f", rot: 60 },
  { left: "63%", delay: "2s", dur: "17s", size: 14, color: "#a8452a", rot: -10 },
  { left: "78%", delay: "6s", dur: "15s", size: 24, color: "#c8892b", rot: 35 },
  { left: "92%", delay: "10s", dur: "18s", size: 15, color: "#5e7a3c", rot: -45 },
];

function Maple({ size, color, rot }: { size: number; color: string; rot: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" style={{ transform: `rotate(${rot}deg)` }}>
      <path
        fill={color}
        d="M12 2l1.6 3.6 3-1.4-.7 3.5 3.6.2-2.4 2.6 3.2 1.7-3.6 1.1.9 3.4-3.3-1.5L13 19h-.6v3h-1v-3H11l-1.4-3.8-3.3 1.5.9-3.4-3.6-1.1 3.2-1.7L4.4 7.9l3.6-.2-.7-3.5 3 1.4z"
      />
    </svg>
  );
}

export default function Leaves() {
  return (
    <div className="leaves" aria-hidden>
      {LEAVES.map((l, i) => (
        <span key={i} className="leaf" style={{ left: l.left, animationDelay: l.delay, animationDuration: l.dur }}>
          <Maple size={l.size} color={l.color} rot={l.rot} />
        </span>
      ))}
    </div>
  );
}

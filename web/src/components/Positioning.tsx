import type { PositionedBank } from "../types";

const COLOUR = { traditional: "var(--traditional)", challenger: "var(--challenger)" } as const;

/**
 * One axis, one question: is ING closer to the incumbents or the challengers?
 *
 * Deliberately not a scatter or a radar. The stakeholders asked a directional
 * question and this answers exactly that; anything with two axes invites
 * reading a second dimension that was never measured.
 */
export function Positioning({ banks }: { banks: PositionedBank[] }) {
  const scores = banks.map((b) => b.score);
  const lo = Math.min(-0.15, ...scores) - 0.05;
  const hi = Math.max(1.15, ...scores) + 0.05;
  const pct = (v: number) => ((v - lo) / (hi - lo)) * 100;

  return (
    <div className="card axis">
      {[...banks].sort((a, b) => b.score - a.score).map((b) => (
        <div key={b.key} className={`axis-row${b.isFocus ? " focus" : ""}`}>
          <div className="axis-name">{b.bank}</div>
          <div className="axis-track">
            <span
              style={{ position: "absolute", left: `${pct(0)}%`, top: 0, bottom: 0, width: 1, background: "var(--line)" }}
            />
            <span
              style={{ position: "absolute", left: `${pct(1)}%`, top: 0, bottom: 0, width: 1, background: "var(--line)" }}
            />
            <span
              className="axis-dot"
              style={{ left: `${pct(b.score)}%`, background: COLOUR[b.category] }}
              title={`${b.bank}: ${b.score.toFixed(2)}`}
            />
          </div>
          <div className="axis-score">{b.score.toFixed(2)}</div>
        </div>
      ))}

      <div className="axis-scale">
        <div />
        <div className="ends">
          <span>◀ typical traditional bank</span>
          <span>typical challenger ▶</span>
        </div>
        <div />
      </div>
    </div>
  );
}

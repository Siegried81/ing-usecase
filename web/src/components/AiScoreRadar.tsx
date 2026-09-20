import { useState } from "react";
import type { AiScoreAxis, BankProfile } from "../types";

const COLOUR = { traditional: "var(--traditional)", challenger: "var(--challenger)" } as const;
const SIZE = 320;
const CENTER = SIZE / 2;
const RADIUS = 120;

function point(angle: number, r: number): [number, number] {
  return [CENTER + r * Math.cos(angle), CENTER + r * Math.sin(angle)];
}

function angleOf(index: number, count: number): number {
  return -Math.PI / 2 + (index * 2 * Math.PI) / count;
}

function average(banks: BankProfile[], axisKey: string): number | null {
  const values = banks
    .map((b) => b.aiScore[axisKey])
    .filter((v): v is number => v !== null && v !== undefined);
  return values.length ? values.reduce((a, b) => a + b, 0) / values.length : null;
}

/**
 * AI Score radar - comparator/ai_score.py's six axes, ONE bank at a time
 * against the market average.
 *
 * sieg 19/09, first SVG/multi-axis chart in this codebase. Positioning.tsx
 * deliberately avoids a 2-axis chart because the traditional-vs-challenger
 * question is genuinely one-dimensional and a second axis would invite reading
 * a dimension nobody measured. The AI Score is the opposite case: it IS six
 * independently-measured dimensions, so a radar is the honest shape for it.
 *
 * sieg 19/09, picker added: overlaying all banks' polygons at once (the first
 * version) was unreadable past 3-4 banks. Reuses the same .picker/.picker-btn
 * pattern as Trends.tsx's bank/product pickers rather than inventing a new
 * control. One bank's polygon (solid, coloured by category) against the
 * market average (dashed, neutral) is the comparison a reader can actually
 * follow; the table underneath still lists every bank for reference.
 *
 * A bank with no data for an axis (ai_score.py returns null rather than a
 * fabricated 0) draws that vertex at the centre rather than pretending to a
 * measured zero - the table says "no data" explicitly for the same cell, so
 * colour is never the only way to notice a gap (this repo's charts.py doctrine).
 */
export function AiScoreRadar({
  banks, axes, focusKey,
}: { banks: BankProfile[]; axes: AiScoreAxis[]; focusKey: string }) {
  const [selectedKey, setSelectedKey] = useState(focusKey || banks[0]?.key || "");
  const selected = banks.find((b) => b.key === selectedKey) ?? banks[0];

  if (!selected || axes.length === 0) return null;

  const rings = [0.25, 0.5, 0.75, 1];
  const polygon = (scoreOf: (axisKey: string) => number | null | undefined) =>
    axes
      .map((axis, i) => {
        const value = scoreOf(axis.key);
        const r = value === null || value === undefined ? 0 : (value / 10) * RADIUS;
        return point(angleOf(i, axes.length), r).join(",");
      })
      .join(" ");

  return (
    <div className="card">
      <div className="picker">
        {banks.map((b) => (
          <button
            key={b.key}
            className={`picker-btn${b.key === selectedKey ? " active" : ""}`}
            onClick={() => setSelectedKey(b.key)}
          >
            {b.name}
          </button>
        ))}
      </div>

      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} width="100%" style={{ maxWidth: 420, display: "block", margin: "12px auto 0" }}>
        {rings.map((f) => (
          <polygon
            key={f}
            points={axes.map((_, i) => point(angleOf(i, axes.length), RADIUS * f).join(",")).join(" ")}
            fill="none"
            stroke="var(--line)"
          />
        ))}
        {axes.map((axis, i) => {
          const angle = angleOf(i, axes.length);
          const [x2, y2] = point(angle, RADIUS);
          const [lx, ly] = point(angle, RADIUS + 16);
          return (
            <g key={axis.key}>
              <line x1={CENTER} y1={CENTER} x2={x2} y2={y2} stroke="var(--line)" />
              <text x={lx} y={ly} fontSize={11} fill="var(--ink-2)" textAnchor="middle" dominantBaseline="middle">
                {axis.label}
              </text>
            </g>
          );
        })}

        <polygon
          points={polygon((k) => average(banks, k))}
          fill="none"
          stroke="var(--ink-3)"
          strokeWidth={1.5}
          strokeDasharray="4 3"
        />
        <polygon
          points={polygon((k) => selected.aiScore[k])}
          fill={COLOUR[selected.category]}
          fillOpacity={0.2}
          stroke={COLOUR[selected.category]}
          strokeWidth={2.5}
        >
          <title>{selected.name}</title>
        </polygon>
      </svg>

      <div className="legend" style={{ justifyContent: "center", marginTop: 4 }}>
        <strong style={{ color: COLOUR[selected.category] }}>{selected.name}</strong> (solid) vs{" "}
        <span style={{ color: "var(--ink-3)" }}>market average</span> (dashed)
      </div>

      {/* sieg 19/09: reuses DeckClaims' .claims table styling - the accessibility
          fallback for the radar above, same doctrine as charts.py's companion tables. */}
      <div className="table-scroll wide">
        <table className="claims" style={{ marginTop: 14 }}>
          <thead>
            <tr>
              <th>Bank</th>
              {axes.map((a) => <th key={a.key}>{a.label}</th>)}
            </tr>
          </thead>
          <tbody>
            {banks.map((b) => (
              <tr key={b.key}>
                <td className="claim" style={{ fontWeight: b.key === selectedKey ? 700 : 400 }}>{b.name}</td>
                {axes.map((a) => {
                  const value = b.aiScore[a.key];
                  return <td key={a.key}>{value === null || value === undefined ? "no data" : value.toFixed(1)}</td>;
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

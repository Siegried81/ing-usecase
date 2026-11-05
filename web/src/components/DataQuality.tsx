import type { DataQuality } from "../types";

/** A data-quality team reads a dataset by dimension, not as one pass/fail. This
 *  panel shows the six, with the gating ones (completeness, validity,
 *  uniqueness) that block a build separated in words from the ones that only
 *  warn, and accuracy stated as not measurable here rather than invented. */

const STATUS: Record<string, { label: string; colour: string }> = {
  pass: { label: "pass", colour: "#1a7f4b" },
  warn: { label: "warn", colour: "#b7791f" },
  fail: { label: "fail", colour: "#c0392b" },
  not_measured: { label: "not measurable", colour: "var(--ink-3)" },
};

export function DataQualityPanel({ dq }: { dq: DataQuality }) {
  return (
    <div className="card">
      <p style={{ margin: "0 0 14px", color: "var(--ink-2)" }}>
        The dataset scored on the standard data-quality dimensions — the ones a BCBS 239 data-quality
        programme reports on — using the feature dictionary's own rules. Completeness, validity and
        uniqueness <strong>gate the build</strong>; consistency and timeliness are reported but only
        warn; accuracy is not measurable here and says so. {dq.rows} rows, {dq.columnsChecked} columns
        checked.
      </p>
      <table className="dq-table" style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
        <thead>
          <tr style={{ textAlign: "left", color: "var(--ink-3)", fontSize: 12.5 }}>
            <th style={{ padding: "6px 8px" }}>Dimension</th>
            <th style={{ padding: "6px 8px", width: 70 }}>Score</th>
            <th style={{ padding: "6px 8px", width: 110 }}>Status</th>
            <th style={{ padding: "6px 8px" }}>Detail</th>
          </tr>
        </thead>
        <tbody>
          {dq.dimensions.map((d) => {
            const s = STATUS[d.status] ?? STATUS.not_measured;
            return (
              <tr key={d.dimension} style={{ borderTop: "1px solid var(--line, #e6e6e6)" }}>
                <td style={{ padding: "8px", textTransform: "capitalize", fontWeight: 600 }}>
                  {d.dimension}
                </td>
                <td style={{ padding: "8px", fontVariantNumeric: "tabular-nums" }}>
                  {d.score === null ? "—" : `${Math.round(d.score * 100)}%`}
                </td>
                <td style={{ padding: "8px" }}>
                  <span style={{ display: "inline-flex", alignItems: "center", gap: 6, color: s.colour }}>
                    <span style={{ width: 8, height: 8, borderRadius: "50%", background: s.colour }} />
                    {s.label}
                  </span>
                </td>
                <td style={{ padding: "8px", color: "var(--ink-2)" }}>{d.detail}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

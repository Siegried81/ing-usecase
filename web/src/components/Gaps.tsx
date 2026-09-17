import type { PeerGap, Separation } from "../types";

/**
 * A business reader cannot otherwise tell that "clarity of the offer" is one
 * model's opinion while "words on the page" is counted. Both are numbers on the
 * same chart; only one of them is a measurement.
 */
function Judged({ extraction }: { extraction: string }) {
  if (extraction === "automatic" || extraction === "derived") return null;
  const human = extraction === "rubric";
  return (
    <span
      className="judged"
      title={human
        ? "Scored by a person against a written rubric — a judgement, not a measurement"
        : "Scored by a language model against the same rubric — a judgement, not a measurement, and not yet checked against a human"}
    >
      {human ? "judged" : "model-judged"}
    </span>
  );
}

const fmt = (v: number | null) =>
  v === null ? "—" : Math.abs(v) >= 1000 ? v.toLocaleString("en-GB", { maximumFractionDigits: 0 })
    : Math.abs(v) < 10 ? v.toFixed(2) : v.toFixed(1);

/** How far ING sits from the average of its peers, feature by feature. */
export function PeerGaps({ gaps, focus }: { gaps: PeerGap[]; focus: string }) {
  const max = Math.max(...gaps.map((g) => Math.abs(g.gapSd)), 1);
  return (
    <div className="card">
      {gaps.map((g) => {
        const width = (Math.abs(g.gapSd) / max) * 50;
        const above = g.direction === "above";
        return (
          <div className="bar-row" key={g.feature}>
            <div className="bar-label">
              {g.label} <Judged extraction={g.extraction} />
              <small>{focus} {fmt(g.focusValue)} · peers {fmt(g.peerMean)}</small>
            </div>
            <div className="bar-track">
              <span className="bar-mid" />
              <span
                className="bar-fill"
                style={{
                  left: above ? "50%" : `${50 - width}%`,
                  width: `${width}%`,
                  background: above ? "var(--challenger)" : "var(--traditional)",
                }}
              />
            </div>
            <div className="bar-value">{above ? "more" : "less"}</div>
          </div>
        );
      })}
    </div>
  );
}

/** What actually separates the incumbents from the challengers. */
export function GroupSeparation({ rows }: { rows: Separation[] }) {
  const max = Math.max(...rows.map((r) => Math.abs(r.effect)), 1);
  return (
    <div className="card">
      {rows.map((r) => {
        const width = (Math.abs(r.effect) / max) * 50;
        const challenger = r.higherAt === "challenger";
        return (
          <div className="bar-row" key={r.feature}>
            <div className="bar-label">
              {r.label} <Judged extraction={r.extraction} />
              <small>traditional {fmt(r.traditional)} · challenger {fmt(r.challenger)}</small>
            </div>
            <div className="bar-track">
              <span className="bar-mid" />
              <span
                className="bar-fill"
                style={{
                  left: challenger ? "50%" : `${50 - width}%`,
                  width: `${width}%`,
                  background: challenger ? "var(--challenger)" : "var(--traditional)",
                }}
              />
            </div>
            <div className="bar-value">{challenger ? "challengers" : "incumbents"}</div>
          </div>
        );
      })}
    </div>
  );
}

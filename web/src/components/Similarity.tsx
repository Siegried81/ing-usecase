import type { Report } from "../types";

/**
 * Euclidean distance between banks in standardised feature space, plus the
 * two-cluster split and ING's nearest neighbours.
 *
 * Lower is more similar. The distance itself is not a quality judgement: two
 * banks being close means they made similar measurable choices, nothing more.
 */
export function Similarity({
  similarity,
  clusters,
  nearest,
  focus,
}: {
  similarity: Report["similarity"];
  clusters: Report["clusters"];
  nearest: Report["nearestToFocus"];
  focus: string;
}) {
  const { banks, matrix } = similarity;
  if (banks.length === 0) return <div className="muted-note">No comparable banks.</div>;
  const max = Math.max(1, ...matrix.flat());

  return (
    <div className="card">
      <div className="table-scroll">
        <table className="claims matrix">
          <thead>
            <tr>
              <th />
              {banks.map((b) => <th key={b}>{b}</th>)}
            </tr>
          </thead>
          <tbody>
            {banks.map((row, i) => (
              <tr key={row}>
                <td className="claim">{row}</td>
                {banks.map((col, j) => {
                  const value = matrix[i][j];
                  return (
                    <td
                      key={col}
                      className={i === j ? "diagonal" : ""}
                      style={i === j ? undefined : { background: cellColour(value / max) }}
                      title={`${row} ↔ ${col}: ${value}`}
                    >
                      {i === j ? "—" : value.toFixed(1)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="legend">Darker = further apart on the measured features. Diagonal omitted.</div>

      <div className="profile-grid" style={{ marginTop: 18 }}>
        <div>
          <h3 className="sub-h">Closest to {focus}</h3>
          {nearest.length === 0 ? (
            <div className="muted-note">No focus bank in this comparison.</div>
          ) : (
            nearest.map((n) => (
              <div className="bar-row" key={n.bank} style={{ gridTemplateColumns: "1fr 70px" }}>
                <div className="bar-label">{n.bank}</div>
                <div className="bar-value">{n.distance}</div>
              </div>
            ))
          )}
        </div>
        <div>
          <h3 className="sub-h">Clusters (k=2)</h3>
          <p className="muted-note" style={{ marginTop: 0 }}>
            A descriptive split of the measured features. It is not guaranteed to be
            the traditional/challenger boundary.
          </p>
          {clusters.map((c) => (
            <div className="cluster" key={c.cluster}>
              <span className="cluster-id">Cluster {c.cluster + 1}</span>
              <span>{c.banks.join(", ")}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/** 0 -> near white, 1 -> the traditional blue. Alpha keeps text readable. */
function cellColour(ratio: number): string {
  const clamped = Math.max(0, Math.min(1, ratio));
  return `rgba(42, 120, 214, ${(clamped * 0.55).toFixed(2)})`;
}

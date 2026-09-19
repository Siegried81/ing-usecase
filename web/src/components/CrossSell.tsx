import type { BankProfile, CrossSellMatrix } from "../types";

/**
 * sieg 19/09: the brief's "Cross-Sell Score" (products offered / products
 * possible, per bank) plus its co-occurrence matrix flattened to a table -
 * this repo has no graph-drawing library and one wasn't worth adding for 7
 * product families. The largest cells are "most associated products".
 *
 * "Never offered together" is split into two lists computed in Python
 * (cross_sell.py::never_paired()), not recomputed here: with only 1-2 real
 * pages in some product families, a "0" is usually "not enough data to say"
 * rather than a genuine finding, and that distinction has to come from the
 * same place the page counts live.
 */
export function CrossSell({ banks, matrix }: { banks: BankProfile[]; matrix: CrossSellMatrix }) {
  return (
    <div className="card">
      {banks.map((b) => (
        <div className="bar-row" key={b.key}>
          <div className="bar-label">{b.name}</div>
          <div className="bar-track">
            <span
              className="bar-fill"
              style={{ left: 0, width: `${(b.crossSellScore ?? 0) * 100}%`, background: "var(--focus-ring)" }}
            />
          </div>
          <div className="bar-value">{b.crossSellScore === null ? "no data" : `${(b.crossSellScore * 100).toFixed(0)}%`}</div>
        </div>
      ))}

      {matrix.mostAssociated.length > 0 && (
        <div className="scope-note" style={{ marginTop: 14 }}>
          <strong>Most associated:</strong>{" "}
          {matrix.mostAssociated.map((m) => `${m.from} + ${m.to} (${m.count})`).join(", ")}
        </div>
      )}

      <table className="claims" style={{ marginTop: 14 }}>
        <thead>
          <tr>
            <th>Page&rsquo;s own product</th>
            {matrix.products.map((p) => <th key={p}>{p}</th>)}
          </tr>
        </thead>
        <tbody>
          {matrix.products.map((row, i) => (
            <tr key={row}>
              <td className="claim">{row}</td>
              {matrix.products.map((col, j) => (
                <td key={col}>{i === j ? "—" : matrix.matrix[i][j]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      {matrix.neverPaired.confirmed.length > 0 && (
        <div className="scope-note" style={{ marginTop: 12 }}>
          <strong>Never offered together:</strong>{" "}
          {matrix.neverPaired.confirmed.map((p) => `${p.from} + ${p.to}`).join(", ")}
        </div>
      )}
      {matrix.neverPaired.insufficient_data.length > 0 && (
        <div className="scope-note" style={{ marginTop: 8 }}>
          <strong>Not enough data to say:</strong>{" "}
          {matrix.neverPaired.insufficient_data.map((p) => `${p.from} + ${p.to}`).join(", ")} — the row's product
          family has too few real pages for a "0" to mean anything yet.
        </div>
      )}
    </div>
  );
}

import type { Report } from "../types";

/**
 * sieg 20/09: Google Trends search interest by Belgian region
 * (comparator/geo_trends.py, its own pytrends calls). Optional and
 * rate-limited, so this shows an honest "not generated yet" state rather
 * than nothing.
 */
export function GeoTrends({ geoTrends }: { geoTrends: Report["geoTrends"] }) {
  if (!geoTrends.available) {
    return (
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Geographic breakdown not generated</h2>
        <p style={{ color: "var(--ink-2)" }}>
          Run <code>python3 scripts/geo_trends.py</code> to see search interest by Belgian region
          (Brussels / Flanders / Wallonia) here. Nothing else is affected.
        </p>
      </div>
    );
  }

  const banks = Object.entries(geoTrends.banks);
  const maxValue = Math.max(1, ...banks.flatMap(([, b]) => Object.values(b.regions)));

  return (
    <div className="banks">
      {banks.map(([key, bank]) => (
        <div key={key} className="bank">
          <div className="bank-top">
            <span className="bank-name">{bank.name}</span>
          </div>
          {Object.entries(bank.regions)
            .sort(([, a], [, b]) => b - a)
            .map(([region, value]) => (
              <div className="bar-row" key={region} style={{ gridTemplateColumns: "1fr 120px 40px" }}>
                <div className="bar-label">{region}</div>
                <div className="bar-track">
                  <span
                    className="bar-fill"
                    style={{ left: 0, width: `${(value / maxValue) * 100}%`, background: "var(--focus-ring)" }}
                  />
                </div>
                <div className="bar-value">{value}</div>
              </div>
            ))}
        </div>
      ))}
    </div>
  );
}

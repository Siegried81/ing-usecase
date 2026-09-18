import { useEffect, useMemo, useState } from "react";
import type {
  CampaignMatch,
  CampaignScore,
  TrendAnomaly,
  TrendsPayload,
  TrendsSummary,
} from "../types";

/** Five hues, one per term in a sheet - a sheet never has more than 5 terms. */
const TERM_COLOURS = ["#2a78d6", "#eb6834", "#1a7f4b", "#8a5cf6", "#9a6a00"];

const CHART = { w: 760, h: 300, top: 14, right: 16, bottom: 28, left: 42 };

const pct = (v: number) => `${Math.round(v * 100)}%`;

/**
 * Google Trends measures search attention, not campaign performance. This tab
 * exists to give that context a home of its own - and to keep the sentence that
 * says so above every number, rather than in a footnote a reader can skip.
 *
 * Dan's benchmark is a separate project (kbc-ing-benchmark/); we read its
 * export and never recompute its numbers differently. Anomaly detection here is
 * a port of his thresholds, tested against the same inputs.
 */
export function Trends({ summary }: { summary: TrendsSummary | null }) {
  const [data, setData] = useState<TrendsPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [bankKey, setBankKey] = useState<string>("");
  const [productId, setProductId] = useState<string>("");
  const [campaignId, setCampaignId] = useState<number | null>(null);

  useEffect(() => {
    if (!summary?.available) return;
    fetch(`${import.meta.env.BASE_URL}${summary.data_url}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`${r.status}`))))
      .then((payload: TrendsPayload) => {
        setData(payload);
        const focus = payload.banks.find((b) => b.key === "ing") ?? payload.banks[0];
        setBankKey(focus?.key ?? "");
        setProductId(focus?.products[0]?.id ?? "");
        setCampaignId(payload.campaigns.scorecards[0]?.id ?? null);
      })
      .catch((e) => setError(String(e)));
  }, [summary]);

  const bank = useMemo(() => data?.banks.find((b) => b.key === bankKey) ?? null, [data, bankKey]);
  const product = useMemo(
    () => bank?.products.find((p) => p.id === productId) ?? bank?.products[0] ?? null,
    [bank, productId],
  );

  if (!summary?.available) {
    return (
      <div className="card">
        <h2 style={{ marginTop: 0 }}>No search-interest data</h2>
        <p style={{ color: "var(--ink-2)" }}>
          Dan&rsquo;s Google Trends export (<code>kbc-ing-benchmark/export/</code>) is not present,
          so this tab is skipped. Nothing else is affected.
        </p>
        <p className="muted-note">
          Regenerate with <code>python3 scripts/export_web_report.py --product-family auto</code>
          {" "}once the export is checked out.
        </p>
      </div>
    );
  }
  if (error) {
    return (
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Trends data could not be loaded</h2>
        <p className="muted-note">{error}</p>
      </div>
    );
  }
  if (!data) return <div className="card muted-note">Loading search-interest data…</div>;

  const events = data.events.filter((e) => e.bank === bank?.name);
  const anomalies = product
    ? product.terms.flatMap((t) =>
        t.anomalies.map((a) => ({ ...a, term: t.label })),
      ).sort((a, b) => b.score - a.score)
    : [];
  const selectedCampaign = data.campaigns.scorecards.find((c) => c.id === campaignId) ?? null;
  const matches = selectedCampaign
    ? data.campaigns.matches.filter((m) => m.campaignId === selectedCampaign.id)
    : [];

  return (
    <>
      <div className="card guardrail">
        <strong>Context, not performance.</strong> {data.guardrail}
      </div>

      <div className="trend-meta">
        <span>{data.source}</span>
        <span>
          {data.window.start} → {data.window.end}
        </span>
        <span>{data.campaigns.catalogued} campaigns catalogued</span>
      </div>

      {data.coverage.uncovered.length > 0 && (
        <div className="scope-note" style={{ marginTop: 0 }}>
          <strong>No trends coverage:</strong> {data.coverage.uncovered.join(", ")} — captured by
          the comparator, but not a search term in Dan&rsquo;s benchmark.
        </div>
      )}

      <section>
        <div className="section-head">
          <h2>Search interest by bank and product</h2>
          <p>
            Weekly Google search interest in Belgium over five years (0–100, relative within a
            sheet). Markers are the anomalies Dan&rsquo;s own detector flags: a diamond is a single
            week, a dot is two or more consecutive weeks above both the term&rsquo;s baseline and its
            normal seasonal level.
          </p>
        </div>

        <div className="picker">
          {data.banks.map((b) => (
            <button
              key={b.key}
              className={`picker-btn${b.key === bankKey ? " active" : ""}`}
              onClick={() => {
                setBankKey(b.key);
                setProductId(b.products[0]?.id ?? "");
              }}
            >
              {b.name}
            </button>
          ))}
        </div>

        {bank && (
          <div className="picker picker-sub">
            {bank.products.map((p) => (
              <button
                key={p.id}
                className={`picker-btn${p.id === productId ? " active" : ""}`}
                onClick={() => setProductId(p.id)}
              >
                {p.label}
              </button>
            ))}
          </div>
        )}

        {product && (
          <div className="card">
            <TermChart terms={product.terms} events={events} />
            <div className="chart-legend">
              {product.terms.map((t, i) => (
                <span key={t.term} className="legend-item">
                  <span className="legend-swatch" style={{ background: TERM_COLOURS[i % TERM_COLOURS.length] }} />
                  {t.label}
                  <small>
                    {t.language}
                    {t.anomalies.length > 0 ? ` · ${t.anomalies.length} anomalies` : " · none flagged"}
                  </small>
                </span>
              ))}
            </div>
            {events.length > 0 && (
              <div className="muted-note" style={{ marginTop: 10 }}>
                Dashed markers are known structural events for {bank?.name}:{" "}
                {events.map((e) => `${e.date} ${e.label}`).join(" · ")}
              </div>
            )}
          </div>
        )}

        {anomalies.length > 0 && (
          <div className="card" style={{ marginTop: 14 }}>
            <h3 className="sub-h">Flagged weeks in this sheet ({anomalies.length})</h3>
            <table className="claims">
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Term</th>
                  <th>Kind</th>
                  <th>Value</th>
                  <th>Deviation (z)</th>
                </tr>
              </thead>
              <tbody>
                {anomalies.slice(0, 40).map((a, i) => (
                  <tr key={`${a.term}-${a.date}-${i}`}>
                    <td>{a.date}</td>
                    <td className="claim">{a.term}</td>
                    <td>{a.label}</td>
                    <td>{a.value}</td>
                    <td>{a.score.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {anomalies.length > 40 && (
              <p className="muted-note">Showing the 40 largest deviations of {anomalies.length}.</p>
            )}
          </div>
        )}
      </section>

      <section>
        <div className="section-head">
          <h2>Campaigns matched to those spikes</h2>
          <p>
            Dan catalogued real ING, KBC and CBC campaigns by hand and matched them to detected
            anomalies. A match is a date coincidence to verify, not proof that the campaign moved
            the search number — most rows carry a possible seasonal confound.
          </p>
        </div>

        <div className="card">
          <table className="claims">
            <thead>
              <tr>
                <th>Bank</th>
                <th>Catalogued</th>
                <th>Scorable</th>
                <th>Total score</th>
                <th>Average</th>
                <th>With a matched spike</th>
              </tr>
            </thead>
            <tbody>
              {data.campaigns.summary.map((s) => (
                <tr key={s.bank}>
                  <td className="claim">{s.bank}</td>
                  <td>{s.catalogued}</td>
                  <td>{s.scorable}</td>
                  <td>{s.totalScore.toFixed(2)}</td>
                  <td>{s.averageScore.toFixed(2)}</td>
                  <td>{pct(s.successRate)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="muted-note" style={{ marginTop: 10 }}>
            A brand or sponsoring campaign is structurally less likely to match a product term —
            read the score with its type, not against a product campaign.
          </p>
        </div>

        <div className="card" style={{ marginTop: 14 }}>
          <table className="claims">
            <thead>
              <tr>
                <th>Score</th>
                <th>Bank</th>
                <th>Campaign</th>
                <th>Type</th>
                <th>Spikes</th>
                <th>Sheets</th>
                <th>Dates</th>
              </tr>
            </thead>
            <tbody>
              {data.campaigns.scorecards.map((c) => (
                <CampaignRow
                  key={c.id}
                  campaign={c}
                  selected={c.id === campaignId}
                  onSelect={() => setCampaignId(c.id)}
                />
              ))}
            </tbody>
          </table>
        </div>

        {selectedCampaign && (
          <div className="card" style={{ marginTop: 14 }}>
            <h3 className="sub-h">{selectedCampaign.name}</h3>
            {matches.length === 0 ? (
              <p className="muted-note">
                No detected spike falls in this campaign&rsquo;s window — the campaign is catalogued
                but unmatched.
              </p>
            ) : (
              <table className="claims">
                <thead>
                  <tr>
                    <th>Spike date</th>
                    <th>Product sheet</th>
                    <th>Term</th>
                    <th>Kind</th>
                    <th>Deviation</th>
                    <th>Delay</th>
                    <th>Seasonal confound</th>
                    <th>Contribution</th>
                  </tr>
                </thead>
                <tbody>
                  {matches.map((m: CampaignMatch, i) => (
                    <tr key={`${m.productId}-${m.date}-${i}`}>
                      <td>{m.date}</td>
                      <td>{m.productId}</td>
                      <td className="claim">{m.term}</td>
                      <td>{m.label}</td>
                      <td>{m.score === null ? "—" : m.score.toFixed(2)}</td>
                      <td>{m.delayDays === null ? "—" : `${m.delayDays}d`}</td>
                      <td>{m.seasonalConfound ? "possible" : "no"}</td>
                      <td>{m.contribution === null ? "—" : m.contribution.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        )}
      </section>
    </>
  );
}

function CampaignRow({
  campaign,
  selected,
  onSelect,
}: {
  campaign: CampaignScore;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <tr className={selected ? "campaign-row selected" : "campaign-row"} onClick={onSelect}>
      <td className="score-cell">{campaign.finalScore.toFixed(2)}</td>
      <td>{campaign.bank}</td>
      <td className="claim">{campaign.name}</td>
      <td>{campaign.type}</td>
      <td>{campaign.anomalyCount}</td>
      <td>{campaign.fichesTouched}</td>
      <td>
        {campaign.startDate ?? "—"}
        {campaign.endDate ? ` → ${campaign.endDate}` : ""}
        {campaign.confidence !== "exact" ? ` (${campaign.confidence})` : ""}
      </td>
    </tr>
  );
}

/**
 * A small SVG line chart. No chart library: the repo's other charts are
 * hand-drawn too, and a dependency for one tab is not worth the bundle.
 */
function TermChart({
  terms,
  events,
}: {
  terms: { term: string; label: string; points: [string, number][]; anomalies: TrendAnomaly[] }[];
  events: { date: string; label: string }[];
}) {
  const allPoints = terms.flatMap((t) => t.points);
  if (allPoints.length === 0) return <p className="muted-note">This sheet has no data points.</p>;

  const times = allPoints.map((p) => Date.parse(p[0]));
  const xMin = Math.min(...times);
  const xMax = Math.max(...times);
  const yMax = Math.max(10, ...allPoints.map((p) => p[1]));

  const px = (date: string) =>
    CHART.left + ((Date.parse(date) - xMin) / Math.max(1, xMax - xMin)) * (CHART.w - CHART.left - CHART.right);
  const py = (value: number) =>
    CHART.h - CHART.bottom - (value / yMax) * (CHART.h - CHART.top - CHART.bottom);

  const yearTicks = useMemo(() => {
    const first = new Date(xMin).getUTCFullYear();
    const last = new Date(xMax).getUTCFullYear();
    const ticks: number[] = [];
    for (let y = first; y <= last; y++) ticks.push(y);
    return ticks.filter((_, i) => i % Math.ceil(ticks.length / 6) === 0);
  }, [xMin, xMax]);

  return (
    <svg viewBox={`0 0 ${CHART.w} ${CHART.h}`} className="trend-chart" role="img">
      {[0, 0.5, 1].map((f) => (
        <g key={f}>
          <line
            x1={CHART.left}
            x2={CHART.w - CHART.right}
            y1={py(yMax * f)}
            y2={py(yMax * f)}
            stroke="var(--line-2)"
            strokeWidth={1}
          />
          <text x={CHART.left - 6} y={py(yMax * f) + 3} textAnchor="end" className="chart-tick">
            {Math.round(yMax * f)}
          </text>
        </g>
      ))}

      {events.map((e) => (
        <line
          key={`${e.date}-${e.label}`}
          x1={px(e.date)}
          x2={px(e.date)}
          y1={CHART.top}
          y2={CHART.h - CHART.bottom}
          stroke="var(--ink-3)"
          strokeWidth={1}
          strokeDasharray="3 3"
        >
          <title>{`${e.date} · ${e.label}`}</title>
        </line>
      ))}

      {yearTicks.map((y) => {
        const iso = `${y}-01-01`;
        return (
          <text key={y} x={px(iso)} y={CHART.h - 8} textAnchor="middle" className="chart-tick">
            {y}
          </text>
        );
      })}

      {terms.map((t, i) => {
        const colour = TERM_COLOURS[i % TERM_COLOURS.length];
        const d = t.points.map((p, j) => `${j === 0 ? "M" : "L"}${px(p[0])},${py(p[1])}`).join(" ");
        return (
          <g key={t.term}>
            <path d={d} fill="none" stroke={colour} strokeWidth={1.6} />
            {t.anomalies.map((a) => {
              const x = px(a.date);
              const y = py(a.value);
              return (
                <g key={`${a.date}-${a.type}`} fill={colour}>
                  <title>{`${t.label} · ${a.date} · ${a.label} (z ${a.score.toFixed(2)})`}</title>
                  {a.type === "isolated_spike" ? (
                    <path d={`M${x},${y - 4} L${x + 4},${y} L${x},${y + 4} L${x - 4},${y} Z`} />
                  ) : (
                    <circle cx={x} cy={y} r={3.4} stroke="#fff" strokeWidth={1} />
                  )}
                </g>
              );
            })}
          </g>
        );
      })}
    </svg>
  );
}

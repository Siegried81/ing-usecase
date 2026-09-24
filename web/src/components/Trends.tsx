import { useEffect, useMemo, useState } from "react";
import type {
  BenchmarkBank,
  SearchInterestLessons,
  ShareBankReading,
  TrendBenchmark,
  TrendsTrajectoryPayload,
  ShareChallengerFocus,
  ShareInsights,
  ShareOfSearch,
  TrendExternalReference,
  TrendsPayload,
  TrendsSummary,
} from "../types";

/** Five hues, one per term in a sheet - a sheet never has more than 5 terms. */
const TERM_COLOURS = ["#2a78d6", "#eb6834", "#1a7f4b", "#8a5cf6", "#9a6a00"];

/** Same logic as the ranking bars: incumbent blue, challenger violet. The
 *  other-incumbent tint is the same hue as the big four, one step lighter. */
const SEGMENT_COLOURS: Record<string, string> = {
  big_four: "#2a78d6",
  other_incumbents: "#9dc2ee",
  challengers: "#8a5cf6",
};

/** How many bank readings are shown before the "show all" toggle. */
const READINGS_VISIBLE = 7;

const CHART = { w: 760, h: 300, top: 14, right: 16, bottom: 28, left: 42 };

/**
 * Google Trends measures search attention, not campaign performance. This tab
 * exists to give that context a home of its own - and to keep the sentence that
 * says so above every number, rather than in a footnote a reader can skip.
 *
 * the benchmark is a separate project (search_interest/); we read its
 * export and never recompute its numbers differently.
 */
export function Trends({
  summary,
  lessons,
}: {
  summary: TrendsSummary | null;
  lessons: SearchInterestLessons | null;
}) {
  const [data, setData] = useState<TrendsPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [bankKey, setBankKey] = useState<string>("");
  const [productId, setProductId] = useState<string>("");

  useEffect(() => {
    if (!summary?.available) return;
    fetch(`${import.meta.env.BASE_URL}${summary.data_url}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`${r.status}`))))
      .then((payload: TrendsPayload) => {
        setData(payload);
        const focus = payload.banks.find((b) => b.key === "ing") ?? payload.banks[0];
        setBankKey(focus?.key ?? "");
        setProductId(focus?.products[0]?.id ?? "");
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
          Dan&rsquo;s Google Trends export (<code>search_interest/export/</code>) is not present,
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
  const flagged = new Set(data.shareOfSearch?.lowConfidence ?? []);

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
      </div>

      {data.coverage.uncovered.length > 0 && (
        <div className="scope-note" style={{ marginTop: 0 }}>
          <strong>No trends coverage:</strong> {data.coverage.uncovered.join(", ")} — captured by
          the comparator, but not a search term in Dan&rsquo;s benchmark.
        </div>
      )}

      {data.shareOfSearch && <ShareOfSearchView share={data.shareOfSearch} flagged={flagged} />}

      {data.trajectory && <AttentionMoved traj={data.trajectory} flagged={flagged} />}

      {lessons && <SearchInterestContext lessons={lessons} />}

      <section>
        <div className="section-head">
          <h2>How much each bank is searched for</h2>
          <p>
            The weekly series behind the ranking above: Google search interest in Belgium over
            five years, 0–100 relative to the peak <em>within each request</em> — which is why two
            banks from different requests cannot be compared here, only in the chained ranking.
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
                  <small>{t.language}</small>
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

      </section>

      {flagged.size > 0 && <LowVolumeFootnote />}
    </>
  );
}

function TermChart({
  terms,
  events,
}: {
  terms: { term: string; label: string; points: [string, number][] }[];
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
          </g>
        );
      })}
    </svg>
  );
}

/**
 * Share of search: the ranking answers "who is first", the sentence under it
 * answers "and why", and the method sits folded underneath.
 *
 * The order is the point. A dozen overlaid series cannot answer "who leads", so
 * the sorted bars come first and the weekly detail is demoted below the fold.
 * Every figure is handed over by comparator/trends.py; nothing is computed
 * here and no sentence is hardcoded, so a later collection run cannot leave a
 * stale conclusion on screen.
 */
/** "A", "A and B", "A, B and C" - so a tie group of any size reads naturally. */
function joinNames(names: string[]): string {
  if (names.length <= 1) return names[0] ?? "";
  return `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`;
}

/** A non-computed claim always travels with its source and publication date. */
function ReferenceNote({ reference }: { reference: TrendExternalReference }) {
  return (
    <p className="muted-note" style={{ marginBottom: 0 }}>
      {reference.claim}{" "}
      <a href={reference.url} target="_blank" rel="noreferrer">
        {reference.source}
      </a>
      , published {reference.published} (retrieved {reference.retrieved}).
    </p>
  );
}

/** Block 1. Nothing here is asserted: every quantity is read off the payload. */
function WhatThisMeasures({ share }: { share: ShareOfSearch }) {
  const w = share.insights.window;
  return (
    <div className="card">
      <h3 className="sub-h">What this measures</h3>
      <p style={{ color: "var(--ink-2)", margin: 0 }}>
        This ranking compares how often people in Belgium searched for each bank&rsquo;s brand on
        Google, across {w.banks} banks and {w.weeks} weeks ({w.firstDate} to {w.lastDate}). Google
        Trends only returns relative values inside a single query, so the {w.fiches} queries are
        chained through {joinNames(share.method.anchors)}, which appear identically in every query.
        The result is a share of search attention: it says which brands people look for, not how
        many customers each bank has.
      </p>
    </div>
  );
}

/** Block 2. The wording forks on bigFourAreTopFour: the convention is checked
 *  against the ranking, never assumed, so the copy cannot claim a lead the
 *  data does not show. */
function HowConcentrated({ insights, flagged }: { insights: ShareInsights; flagged: Set<string> }) {
  const { groups, bigFourAreTopFour, topFour } = insights.segments;
  const byId = Object.fromEntries(groups.map((g) => [g.id, g]));
  const bigFour = byId.big_four;
  const others = byId.other_incumbents;
  const challengers = byId.challengers;
  const depositsRef = insights.references.find((r) => r.id === "big_four_deposits");
  const total = groups.reduce((sum, g) => sum + g.sharePct, 0) || 1;

  return (
    <div className="card">
      <h3 className="sub-h">How concentrated attention is</h3>

      {bigFourAreTopFour ? (
        <p style={{ color: "var(--ink-2)", marginTop: 0 }}>
          The big four (<BankList names={bigFour.members.map((m) => m.bank)} flagged={flagged} />)
          capture {bigFour.sharePct}% of brand search. The other {others.count} incumbents take{" "}
          {others.sharePct}%, and the {challengers.count} challengers {challengers.sharePct}%
          combined.
        </p>
      ) : (
        <p style={{ color: "var(--ink-2)", marginTop: 0 }}>
          The top four by brand search are{" "}
          {topFour.map((t, i) => (
            <span key={t.key}>
              {i > 0 && (i === topFour.length - 1 ? " and " : ", ")}
              <BankName name={t.bank} flagged={flagged} /> ({t.sharePct}%)
            </span>
          ))}
          . The big four (<BankList names={bigFour.members.map((m) => m.bank)} flagged={flagged} />)
          hold {bigFour.sharePct}% together. The
          other {others.count} incumbents take {others.sharePct}%, and the {challengers.count}{" "}
          challengers {challengers.sharePct}% combined.
        </p>
      )}

      <div
        style={{ display: "flex", height: 18, borderRadius: 4, overflow: "hidden", margin: "14px 0 8px" }}
        role="img"
        aria-label="Share of brand search by segment"
      >
        {groups.map((g) => (
          <div
            key={g.id}
            style={{ width: `${(g.sharePct / total) * 100}%`, background: SEGMENT_COLOURS[g.id] }}
            title={`${g.label}: ${g.sharePct}%`}
          />
        ))}
      </div>
      <div className="chart-legend" style={{ marginBottom: 14 }}>
        {groups.map((g) => (
          <span key={g.id} className="legend-item">
            <span className="legend-swatch" style={{ background: SEGMENT_COLOURS[g.id] }} />
            {g.label}
            <small>
              {g.sharePct}% · {g.count} banks
            </small>
          </span>
        ))}
      </div>

      <p style={{ color: "var(--ink-2)" }}>
        Attention is spread as if there were about {insights.concentration.equivalentBrands} equally
        sized brands (HHI {insights.concentration.hhi}).
      </p>

      {depositsRef && (
        <>
          <p style={{ color: "var(--ink-2)", marginBottom: 4 }}>
            This matches the known structure of the Belgian market:
          </p>
          <ReferenceNote reference={depositsRef} />
        </>
      )}
    </div>
  );
}

/** Block 3. One pre-computed line per bank; a tie group is never ordered. */
function BankByBank({ readings, flagged }: { readings: ShareBankReading[]; flagged: Set<string> }) {
  const [showAll, setShowAll] = useState(false);
  const visible = showAll ? readings : readings.slice(0, READINGS_VISIBLE);
  const hidden = readings.length - visible.length;

  return (
    <div className="card" style={{ marginTop: 14 }}>
      <h3 className="sub-h">Bank-by-bank reading</h3>
      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
        {visible.map((b) => (
          <li
            key={b.key}
            style={{ padding: "8px 0", borderBottom: "1px solid var(--line-2)", fontSize: "14.5px" }}
          >
            <strong>
              <BankName name={b.bank} flagged={flagged} />
            </strong>{" "}
            — {b.sharePct}%,{" "}
            {b.tieWith.length > 0 ? (
              <>
                level with <BankList names={b.tieWith} flagged={flagged} /> ({b.tieSpreadPts} pts
                apart).
              </>
            ) : (
              `rank ${b.rank}.`
            )}
            {b.tieWith.length === 0 && b.gapToAbovePts !== null && b.bankAbove
              ? ` ${b.gapToAbovePts} pts behind ${b.bankAbove}.`
              : ""}
            {b.pctOfSegment !== null ? ` ${b.pctOfSegment}% of ${b.segmentLabel} attention.` : ""}
          </li>
        ))}
      </ul>
      {hidden > 0 && (
        <button className="picker-btn" style={{ marginTop: 12 }} onClick={() => setShowAll(true)}>
          Show all {readings.length}
        </button>
      )}
      {showAll && readings.length > READINGS_VISIBLE && (
        <button className="picker-btn" style={{ marginTop: 12 }} onClick={() => setShowAll(false)}>
          Show fewer
        </button>
      )}
    </div>
  );
}

/** The aside. Its job is to stop a reader concluding that a small share means
 *  a small bank - three reasons why the two come apart, one of them flagged as
 *  an unverified hypothesis rather than a finding. */
function ChallengerAside({
  focus,
  totalBanks,
  peakFloor,
  flagged,
}: {
  focus: ShareChallengerFocus;
  totalBanks: number;
  peakFloor: number;
  flagged: Set<string>;
}) {
  const reference = focus.reference;
  return (
    <section
      style={{
        marginTop: 18,
        border: "1px solid var(--line)",
        borderLeft: "4px solid var(--challenger)",
        background: "var(--surface-2)",
        borderRadius: "var(--radius)",
        padding: 22,
      }}
    >
      <h3 className="sub-h">Why challengers look small here</h3>

      <p style={{ color: "var(--ink-2)", marginTop: 0 }}>
        {reference ? (
          <>
            {focus.bank} reports {reference.value} in Belgium ({reference.source},{" "}
            {reference.published}), yet it holds {focus.sharePct}% of brand search, rank{" "}
            {focus.rank} of {totalBanks}, behind {focus.incumbentsAbove} incumbents.
          </>
        ) : (
          <>
            {focus.bank} is the largest challenger by brand search, yet it holds {focus.sharePct}%,
            rank {focus.rank} of {totalBanks}, behind {focus.incumbentsAbove} incumbents.
          </>
        )}{" "}
        That gap is expected, for three reasons.
      </p>

      <h4 className="sub-h" style={{ marginBottom: 4 }}>
        Incumbent brand searches are partly navigational
      </h4>
      <p style={{ color: "var(--ink-2)", marginTop: 0 }}>
        Many searches for a traditional bank&rsquo;s name are people looking for its web banking
        login, a branch or opening hours. That traffic reflects day-to-day use of the web channel as
        much as brand interest, and it inflates incumbents&rsquo; share. This is a working
        hypothesis: it has not yet been verified with query-level data.
      </p>

      <h4 className="sub-h" style={{ marginBottom: 4 }}>
        Challenger journeys bypass Google
      </h4>
      <p style={{ color: "var(--ink-2)", marginTop: 0 }}>
        Challengers are app-first. Customers sign up through app stores or referral links and use
        the app daily without searching the brand name, so a growing customer base does not
        translate into a proportional rise in brand searches.
      </p>

      <h4 className="sub-h" style={{ marginBottom: 4 }}>
        Small series hit a measurement floor
      </h4>
      <p style={{ color: "var(--ink-2)", marginTop: 0 }}>
        <BankList names={focus.lowConfidenceBanks} flagged={flagged} /> peak below {peakFloor} on
        Google&rsquo;s 0–100 scale in their query, so their weekly values move in whole steps of a
        few units.
      </p>

      <p style={{ color: "var(--ink)", fontWeight: 600, marginBottom: 0 }}>
        Read challenger shares as a floor on attention, not as a measure of their customer base.
      </p>
    </section>
  );
}

function ShareOfSearchView({ share, flagged }: { share: ShareOfSearch; flagged: Set<string> }) {
  const max = Math.max(...share.ranking.map((r) => r.sharePct), 1);
  const insights = share.insights;

  return (
    <section>
      <div className="section-head">
        <h2>Share of brand search</h2>
        <p>
          Which bank Belgians looked up, across {share.ranking.length} banks and {share.weeks}{" "}
          weeks ({share.window.start} → {share.window.end}).
        </p>
      </div>

      {insights && <WhatThisMeasures share={share} />}
      {insights && <HowConcentrated insights={insights} flagged={flagged} />}

      <div className="card">
        <p className="headline-sentence" style={{ fontSize: "1.1rem", marginTop: 0 }}>
          {share.headline.sentence}
        </p>
        <p style={{ color: "var(--muted)", marginBottom: 0 }}>{share.headline.segmentSentence}</p>
      </div>

      <div className="card">
        <table className="share-table" style={{ width: "100%", borderCollapse: "collapse" }}>
          <tbody>
            {share.ranking.map((row) => (
              <tr key={row.key}>
                <td style={{ width: "2rem", color: "var(--muted)" }}>{row.rank}</td>
                {/* wide enough for the longest bank name on one line */}
                <td style={{ width: "12rem", whiteSpace: "nowrap" }}>
                  <BankName name={row.bank} flagged={flagged} />
                </td>
                <td>
                  <div
                    style={{
                      width: `${(row.sharePct / max) * 100}%`,
                      minWidth: row.sharePct > 0 ? "2px" : 0,
                      height: "14px",
                      borderRadius: "3px",
                      background:
                        row.key === "ing"
                          ? "#eb6834"
                          : row.segment === "challenger"
                            ? "#8a5cf6"
                            : "#2a78d6",
                    }}
                  />
                </td>
                <td style={{ width: "4.5rem", textAlign: "right" }}>{row.sharePct.toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {insights && <BankByBank readings={insights.banks} flagged={flagged} />}

      {insights?.challengerFocus && (
        <ChallengerAside
          focus={insights.challengerFocus}
          totalBanks={insights.window.banks}
          peakFloor={insights.measurablePeakFloor}
          flagged={flagged}
        />
      )}

      <div className="scope-note">
        <strong>Attention, not market.</strong> {share.caveat}
      </div>

      <details>
        {/* counted, not written: this said "nine" while the panel had grown to 14 */}
        <summary>
          How {share.ranking.length} banks fit on one scale
        </summary>
        <p>{share.method.why}</p>
        <p>{share.method.aggregation}</p>
        <p>
          Reference request: <code>{share.method.referenceSheet}</code>. Anchors:{" "}
          {share.method.anchors.join(" + ")}. Scale factors applied:{" "}
          {Object.entries(share.method.scaleFactors)
            .map(([sheet, factor]) => `${sheet} ×${factor}`)
            .join(", ")}
          .
        </p>
      </details>
    </section>
  );
}

/** Anchor of the single low-volume footnote at the bottom of the tab. */
const LOW_VOLUME_NOTE_ID = "trends-low-volume-note";

/** A flagged bank is never described in words, only marked. The asterisk is
 *  the whole convention: one footnote carries the caveat for the whole tab. */
function BankName({ name, flagged }: { name: string; flagged: Set<string> }) {
  if (!flagged.has(name)) return <>{name}</>;
  return (
    <>
      {name}
      <a href={`#${LOW_VOLUME_NOTE_ID}`} style={{ textDecoration: "none" }}>
        <sup>*</sup>
      </a>
    </>
  );
}

/** Same marking inside a comma-separated list. */
function BankList({ names, flagged }: { names: string[]; flagged: Set<string> }) {
  return (
    <>
      {names.map((name, i) => (
        <span key={name}>
          {i > 0 && (i === names.length - 1 ? " and " : ", ")}
          <BankName name={name} flagged={flagged} />
        </span>
      ))}
    </>
  );
}

const DIRECTION_STYLE: Record<string, { label: string; colour: string }> = {
  up: { label: "up", colour: "#1a7f4b" },
  flat: { label: "flat", colour: "#767b8a" },
  down: { label: "down", colour: "#b44a1d" },
};

function DirectionBadge({ direction }: { direction: string | null }) {
  if (!direction) return <>—</>;
  const style = DIRECTION_STYLE[direction];
  return (
    <span
      className="tag"
      style={{ background: "transparent", color: style.colour, border: `1px solid ${style.colour}` }}
    >
      {style.label}
    </span>
  );
}

/** Block 1. A flagged bank keeps its row and its aggregated share; every
 *  per-period cell is a dash, because no period figure exists for it. */
function BankTrajectory({ traj, flagged }: { traj: TrendsTrajectoryPayload; flagged: Set<string> }) {
  return (
    <div className="card">
      <h3 className="sub-h">Bank trajectory</h3>
      <div className="table-scroll wide">
        <table className="claims">
          <thead>
            <tr>
              <th>Bank</th>
              {traj.periods.map((p) => (
                <th key={p.label}>{p.label}</th>
              ))}
              <th>Change</th>
              <th>Direction</th>
            </tr>
          </thead>
          <tbody>
            {traj.banks.map((b) => (
              <tr key={b.key}>
                <td className="claim">
                  <BankName name={b.bank} flagged={flagged} />
                  {b.robust === false && (
                    <div className="muted-note">
                      sensitive to {traj.methodChangeDate.slice(0, 4)} method change
                    </div>
                  )}
                </td>
                {traj.periods.map((p, i) => (
                  <td key={p.label}>{b.periodShares ? `${b.periodShares[i]}%` : "—"}</td>
                ))}
                <td>
                  {b.deltaPts === null
                    ? "—"
                    : `${b.deltaPts > 0 ? "+" : ""}${b.deltaPts} pts`}
                </td>
                <td>{b.periodShares ? <DirectionBadge direction={b.direction} /> : "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {traj.biggestRise && traj.biggestFall && (
        <p style={{ color: "var(--ink-2)", marginBottom: 0 }}>
          Among incumbents, {traj.biggestRise.bank} gained the most attention over the period (
          {traj.biggestRise.deltaPts > 0 ? "+" : ""}
          {traj.biggestRise.deltaPts} pts) and {traj.biggestFall.bank} lost the most (
          {traj.biggestFall.deltaPts > 0 ? "+" : ""}
          {traj.biggestFall.deltaPts} pts).
        </p>
      )}
    </div>
  );
}

const ROLE_SENTENCE: Record<string, string> = {
  attention: "the largest share of attention among traditional banks",
  momentum: "the strongest upward trajectory among traditional banks",
};

function signed(value: number | null): string {
  if (value === null) return "—";
  return `${value > 0 ? "+" : ""}${value}`;
}

/** Block 2. The subject is never a candidate for its own benchmark. */
function BenchmarkScope({ traj, flagged }: { traj: TrendsTrajectoryPayload; flagged: Set<string> }) {
  const scope = traj.benchmark;
  const periods = traj.periods;
  const first = periods[0];
  const last = periods[periods.length - 1];
  const context = scope.subjectContext;
  const momentumMissing = !scope.benchmarks.some((b) => b.roles.includes("momentum"));

  function card(entry: TrendBenchmark, body: React.ReactNode) {
    return (
      <div
        key={entry.bank}
        style={{
          border: "1px solid var(--line)",
          borderRadius: "var(--radius)",
          padding: 16,
          background: "var(--surface)",
        }}
      >
        <div style={{ fontWeight: 700, marginBottom: 6 }}>
          <BankName name={entry.bank} flagged={flagged} />
        </div>
        <div style={{ color: "var(--ink-2)", fontSize: "14.5px" }}>{body}</div>
        {entry.robust === false && (
          <div className="muted-note" style={{ marginTop: 8 }}>
            This trajectory depends on the first period, which straddles Google&rsquo;s{" "}
            {traj.methodChangeDate.slice(0, 4)} data collection change.
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="card" style={{ marginTop: 14 }}>
      <h3 className="sub-h">A focused scope for {scope.subject}</h3>
      <p style={{ color: "var(--ink-2)", marginTop: 0 }}>
        Among {scope.traditionalCandidates} traditional{" "}
        {scope.traditionalCandidates === 1 ? "bank" : "banks"} and {scope.challengerCandidates}{" "}
        {scope.challengerCandidates === 1 ? "challenger" : "challengers"} with enough search
        volume, these are the brands whose search attention is most worth studying.
      </p>

      <div style={{ display: "grid", gap: 12, gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))" }}>
        {scope.benchmarks.map((entry) =>
          card(
            entry,
            <>
              {entry.roles.includes("attention") && (
                <>
                  {ROLE_SENTENCE.attention} ({entry.lastSharePct}% in {last.label},{" "}
                  {Math.abs(entry.gapToSubjectPts)} pts{" "}
                  {entry.gapToSubjectPts >= 0 ? "ahead of" : "behind"} {scope.subject}).
                </>
              )}
              {entry.roles.includes("attention") && entry.roles.includes("momentum") && " "}
              {entry.roles.includes("momentum") && (
                <>
                  {ROLE_SENTENCE.momentum} ({signed(entry.relativeSlopePctPerYear)}% per year,{" "}
                  {signed(entry.deltaPts)} pts since {first.label}).
                </>
              )}
            </>,
          ),
        )}

        {scope.challenger &&
          card(
            scope.challenger,
            <>
              {scope.challenger.direction === "up" ? "rising" : scope.challenger.direction}{" "}
              trajectory ({signed(scope.challenger.relativeSlopePctPerYear)}% per year,{" "}
              {signed(scope.challenger.deltaPts)} pts since {first.label}, {scope.challenger.lastSharePct}% in{" "}
              {last.label}).
              {scope.challenger.onlyMeasurable && scope.excludedChallengers.length > 0 && (
                <>
                  {" "}
                  It is the only challenger with enough search volume to measure over time;{" "}
                  <BankList names={scope.excludedChallengers} flagged={flagged} /> are not.
                </>
              )}
            </>,
          )}
      </div>

      {momentumMissing && (
        <p style={{ color: "var(--ink-2)", marginTop: 14 }}>
          No traditional bank gained search attention over the period.
        </p>
      )}

      <p style={{ color: "var(--ink)", marginTop: 14, marginBottom: 6 }}>
        For comparison, {context.bank}: {context.lastSharePct}% in {last.label}, {context.direction}{" "}
        ({signed(context.relativeSlopePctPerYear)}% per year).
      </p>
      <p className="muted-note" style={{ marginBottom: 0 }}>
        These brands are selected on search attention alone. The data shows that their attention
        moved, not why. Their communication, offers and pages are the next thing to examine.
      </p>
    </div>
  );
}

function TrajectoryMethod({ traj }: { traj: TrendsTrajectoryPayload }) {
  const periods = traj.periods;
  return (
    <details style={{ marginTop: 14 }}>
      <summary>How the {periods.length} periods are built</summary>
      <p>
        The common weekly window is cut into {traj.weeksPerPeriod}-week periods anchored on the last
        week and counted backwards, so the most recent period is always complete.{" "}
        {traj.droppedWeeks > 0
          ? `${traj.droppedWeeks} leftover week${traj.droppedWeeks > 1 ? "s" : ""} at the start ${
              traj.droppedWeeks > 1 ? "are" : "is"
            } dropped rather than compared against a full year.`
          : "No week is left over."}
      </p>
      <p>
        A period share sums each bank&rsquo;s rescaled weekly values over the period and divides by
        the panel total, the same volume-weighted basis as the aggregated ranking — never a mean of
        weekly shares.
      </p>
      <p>
        Momentum is the ordinary-least-squares slope of period share on period index, one unit per
        year, divided by the bank&rsquo;s own mean share so brands of different sizes are
        comparable. A relative slope within ±{traj.flatBandPct}% per year reads as flat.
      </p>
      <p>
        Google Trends changed how it collects data on {traj.methodChangeDate}, which the first
        period straddles. Every trajectory is recomputed without that period; where the two
        directions disagree, the row is marked.
      </p>
      {traj.lowConfidenceBanks.length > 0 && (
        <p>
          Banks marked with an asterisk are excluded from trajectories, rank comparisons and
          benchmark selection.
        </p>
      )}
    </details>
  );
}

function LowVolumeFootnote() {
  return (
    <p id={LOW_VOLUME_NOTE_ID} className="muted-note" style={{ marginTop: 22 }}>
      * Search volume for these banks is too low to measure change over time. Their figures only
      show that they are rarely searched for on Google in Belgium; neither their exact share nor
      its evolution should be read from this data.
    </p>
  );
}

function AttentionMoved({
  traj,
  flagged,
}: {
  traj: TrendsTrajectoryPayload;
  flagged: Set<string>;
}) {
  const periods = traj.periods;
  return (
    <section>
      <div className="section-head">
        <h2>
          How attention moved ({periods[0].start.slice(0, 4)}–
          {periods[periods.length - 1].end.slice(0, 4)})
        </h2>
        <p>
          The same volume-weighted share, cut into {periods.length} periods of{" "}
          {traj.weeksPerPeriod} weeks. This shows that attention moved, never why.
        </p>
      </div>
      <BankTrajectory traj={traj} flagged={flagged} />
      <BenchmarkScope traj={traj} flagged={flagged} />
      <TrajectoryMethod traj={traj} />
    </section>
  );
}

/** A z-score gap read out loud. The number stays next to the words. */
function GapNote({ gap }: { gap: number }) {
  return (
    <span className="muted-note" style={{ whiteSpace: "nowrap" }}>
      {gap > 0 ? "+" : ""}
      {gap} sd
    </span>
  );
}

function BenchmarkCard({ bank, focus }: { bank: BenchmarkBank; focus: string }) {
  return (
    <div
      style={{
        border: "1px solid var(--line)",
        borderRadius: "var(--radius)",
        padding: 16,
        background: "var(--surface)",
      }}
    >
      <div style={{ fontWeight: 700 }}>{bank.bank}</div>
      <div className="muted-note" style={{ marginBottom: 10 }}>
        {bank.roleLabel}
        {bank.lastSharePct !== null && <> · {bank.lastSharePct}% of brand search</>}
        {bank.relativeSlopePctPerYear !== null && (
          <>
            {" "}
            · {bank.relativeSlopePctPerYear > 0 ? "+" : ""}
            {bank.relativeSlopePctPerYear}% per year
          </>
        )}
      </div>

      {bank.lessons.length === 0 ? (
        <p className="muted-note" style={{ margin: 0 }}>
          Nothing on its pages separates it from {focus} in the measured set.
        </p>
      ) : (
        <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
          {bank.lessons.map((l) => (
            <li
              key={l.feature}
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: 10,
                padding: "5px 0",
                borderBottom: "1px solid var(--line-2)",
                fontSize: "14px",
              }}
            >
              <span>
                {l.label} — <strong>{l.direction === "above" ? "more" : "less"}</strong> than{" "}
                {focus}
              </span>
              <GapNote gap={l.gapSd} />
            </li>
          ))}
        </ul>
      )}
      <div className="muted-note" style={{ marginTop: 8 }}>
        {bank.pages} page{bank.pages === 1 ? "" : "s"} measured
      </div>
    </div>
  );
}

/**
 * Search interest picks the brands; the measured features say what they do.
 *
 * This sits in Trends rather than Recommendations because it is a reading of
 * the search data, not advice: it recommends nothing and nobody selects it for
 * the generated site. The scope block above names the brands; this says what
 * their pages measurably do.
 *
 * The two halves come from different sources and are joined on the bank name
 * and nothing else. Saying "they get searched for BECAUSE their pages do this"
 * is the one claim this project has no data for, so the caveat travels with
 * the payload rather than sitting in a footnote.
 */
function SearchInterestContext({ lessons }: { lessons: SearchInterestLessons }) {
  const focus = lessons.focus.toUpperCase();
  return (
    <section>
      <div className="section-head">
        <h2>From search-interest context</h2>
        <p>
          Google Trends picked these {lessons.banks.length} brands, on brand-search attention
          alone. What follows is what their pages measurably do differently from {focus}, on the
          same standardised features as the page analysis — never proof that those choices are
          why they are searched for.
        </p>
      </div>

      <div
        style={{
          display: "grid",
          gap: 12,
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
        }}
      >
        {lessons.banks.map((b) => (
          <BenchmarkCard key={b.key} bank={b} focus={focus} />
        ))}
      </div>

      {lessons.common.length > 0 && (
        <div className="card" style={{ marginTop: 14 }}>
          <h3 className="sub-h">What all {lessons.banks.length} have in common</h3>
          <p className="muted-note" style={{ marginTop: 0 }}>
            Choices every one of them makes and {focus} does not — the closest this data comes to
            a shared pattern.
          </p>
          <ul style={{ margin: 0, paddingLeft: 18, color: "var(--ink-2)" }}>
            {lessons.common.map((c) => (
              <li key={c.feature} style={{ padding: "3px 0" }}>
                {c.label} — all {lessons.banks.length} sit {c.direction} the market average (
                {c.meanZ > 0 ? "+" : ""}
                {c.meanZ} sd on average), {focus} sits {c.direction === "above" ? "below" : "above"}{" "}
                it ({c.focusZ > 0 ? "+" : ""}
                {c.focusZ} sd).
              </li>
            ))}
          </ul>
        </div>
      )}

      {lessons.divergent.length > 0 && (
        <div className="card" style={{ marginTop: 14 }}>
          <h3 className="sub-h">Where they part company</h3>
          <p className="muted-note" style={{ marginTop: 0 }}>
            On these there is no single lesson to take: the brands sit on opposite sides of the
            market average.
          </p>
          <ul style={{ margin: 0, paddingLeft: 18, color: "var(--ink-2)" }}>
            {lessons.divergent.map((d) => (
              <li key={d.feature} style={{ padding: "3px 0" }}>
                {d.label} —{" "}
                {d.values.map((v, i) => (
                  <span key={v.key}>
                    {i > 0 && ", "}
                    {v.bank} {v.z > 0 ? "+" : ""}
                    {v.z}
                  </span>
                ))}{" "}
                sd.
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="scope-note">
        <strong>Attention, not explanation.</strong> {lessons.caveat}
      </div>
    </section>
  );
}

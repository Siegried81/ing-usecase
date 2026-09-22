import { useCallback, useEffect, useMemo, useState } from "react";
import type {
  BenchmarkBank,
  Priority,
  Recommendation,
  Report,
  SearchInterestLessons,
  SiteStatus,
} from "../types";
import {
  fetchRecommendations,
  fetchSiteStatus,
  generateRecommendations,
  generateSite,
} from "../api";

/**
 * The one place a model is allowed to opine.
 *
 * The analysis tab reports what the pages measure. This tab turns those same
 * measurements into advice, lets the reader reject any piece of it, and only
 * then builds the website from what is left. A recommendation is never shown
 * without the feature it was argued from, so a reader can go back and check it.
 */

const PRIORITY_ORDER: Record<Priority, number> = { high: 0, medium: 1, low: 2 };

function PriorityTag({ priority }: { priority: Priority }) {
  return <span className={`prio prio-${priority}`}>{priority}</span>;
}

export function Recommendations({ report }: { report: Report }) {
  const [payload, setPayload] = useState<Awaited<ReturnType<typeof fetchRecommendations>> | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [language, setLanguage] = useState("fr");
  const [site, setSite] = useState<SiteStatus | null>(null);
  const [includeReputation, setIncludeReputation] = useState(false);
  const [explainSite, setExplainSite] = useState(false);
  const reputationAvailable = Boolean(report.reputation?.available);

  useEffect(() => {
    fetchRecommendations()
      .then((data) => {
        setPayload(data);
        setSelected(new Set(data.recommendations.map((r) => r.id)));
        // Keep the toggle in step with what was generated, so regenerating a
        // set that already used reputation does not silently drop it.
        setIncludeReputation(Boolean(data.used_reputation));
      })
      .catch((e) => setError(String(e)));
    fetchSiteStatus().then(setSite).catch(() => undefined);
  }, []);

  // The site is ten parallel model calls, so the UI polls rather than blocks.
  useEffect(() => {
    if (site?.status !== "generating") return;
    const id = setInterval(() => {
      fetchSiteStatus().then(setSite).catch(() => undefined);
    }, 2000);
    return () => clearInterval(id);
  }, [site?.status]);

  const onGenerate = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const data = await generateRecommendations(
        includeReputation && reputationAvailable,
      );
      setPayload(data);
      setSelected(new Set(data.recommendations.map((r) => r.id)));
      setIncludeReputation(Boolean(data.used_reputation));
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }, [includeReputation, reputationAvailable]);

  const onGenerateSite = useCallback(async () => {
    setError(null);
    try {
      await generateSite([...selected], language, explainSite);
      setSite(await fetchSiteStatus());
    } catch (e) {
      setError(String(e));
    }
  }, [selected, language, explainSite]);

  const recommendations = useMemo(
    () =>
      [...(payload?.recommendations ?? [])].sort(
        (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority],
      ),
    [payload],
  );

  // A recommendation's `features` are raw snake_case ids (they're
  // machine-checked against the report), but showing "background_luminance"
  // to a reader looks unprofessional - map each id back to the same
  // human-readable label the Analysis tab already uses for it.
  const featureLabels = useMemo(() => {
    const map: Record<string, string> = {};
    for (const g of report.peerGaps) map[g.feature] = g.label;
    for (const s of report.separation) map[s.feature] = s.label;
    return map;
  }, [report]);

  // "From search-interest context" is the computed benchmark
  // section now - the model writes nothing from search interest any more.
  // Two groups, one selection. Reputation recommendations are
  // shown apart because they are argued from context, not from a measured
  // page feature - but they are all picked in the same set and built into
  // the same site. Added the reputation group.
  const analysisRecs = useMemo(
    () => recommendations.filter((r) => r.basis !== "reputation"),
    [recommendations],
  );
  const reputationRecs = useMemo(
    () => recommendations.filter((r) => r.basis === "reputation"),
    [recommendations],
  );
  const reputationCount = reputationRecs.length;
  const selectedReputation = reputationRecs.filter((r) => selected.has(r.id)).length;
  const selectedAnalysis = selected.size - selectedReputation;

  const toggle = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });

  const siteReady = Boolean(site?.ready || site?.status === "ready");
  const generating = site?.status === "generating";
  const siteUrl = site?.site_url ? `/${site.site_url}` : null;

  return (
    <>
      <Section
        title="What the analysis suggests ING should change"
        lede="Written by the same pinned model that labels the pages, from this run's own numbers. Nothing below introduces a figure that is not already in the analysis; every recommendation names the features it was argued from."
      >
        <div className="rec-controls card">
          <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
            <button className="btn-action" onClick={onGenerate} disabled={busy}>
              {payload?.available ? "Regenerate recommendations" : "Generate recommendations"}
            </button>
            {payload?.available && (
              <span className="muted-note">
                {payload.model} · {payload.recommendations.length} recommendations
                {payload.used_reputation ? " · includes reputation context" : ""}
              </span>
            )}
            {busy && (
              <span className="muted-note">
                Asking {payload?.model ?? "the pinned model"} — this takes a few seconds…
              </span>
            )}
          </div>

          {/* Opt-in context, for news headline themes. */}
          <label className={`rec-trends${reputationAvailable ? "" : " disabled"}`}>
            <input
              type="checkbox"
              checked={includeReputation && reputationAvailable}
              disabled={!reputationAvailable || busy}
              onChange={(e) => setIncludeReputation(e.target.checked)}
            />
            <span>
              Include Reputation to add recommendations
              <small>
                {reputationAvailable
                  ? "Adds recommendations comparing what a page claims to what the press covers about the bank. Context only — never sentiment, never evidence that a page or campaign performed."
                  : "No reputation data is present (NEWSAPI_KEY / NEWSAPI_AI_KEY not configured), so this option is unavailable."}
              </small>
            </span>
          </label>

          {error && <div className="scope-note" style={{ marginTop: 12 }}>{error}</div>}
        </div>

        {payload?.available === false && !busy && (
          <div className="card" style={{ marginTop: 14, color: "var(--ink-2)" }}>
            No recommendations yet. Generate them from this run's analysis.
          </div>
        )}

        {payload?.summary && (
          <div className="card" style={{ marginTop: 14 }}>
            <div className="rec-summary-label">The short version</div>
            <p style={{ margin: "6px 0 0", color: "var(--ink-2)" }}>{payload.summary}</p>
            <div className="muted-note" style={{ marginTop: 10 }}>
              Based on {report.scope.pages} pages, {report.scope.n_features} features,{" "}
              {report.scope.banks.length} banks · {report.headline.focus} scores{" "}
              {report.headline.score?.toFixed(2)} ({report.headline.verdict}).
            </div>
            {reputationCount > 0 && (
              <div className="muted-note" style={{ marginTop: 6 }}>
                {reputationCount} further recommendation{reputationCount === 1 ? "" : "s"} come
                from news-theme context and appear in their own section below. They can be
                selected alongside the others for the website.
              </div>
            )}
          </div>
        )}

        {recommendations.length > 0 && (
          <>
            <div className="rec-select-bar">
              <label className="rec-check">
                <input
                  type="checkbox"
                  checked={selected.size === recommendations.length && recommendations.length > 0}
                  onChange={(e) =>
                    setSelected(e.target.checked ? new Set(recommendations.map((r) => r.id)) : new Set())
                  }
                />
                <span>
                  {selected.size} of {recommendations.length} selected for the website
                </span>
              </label>
              <span className="muted-note">Untick anything you do not want implemented.</span>
            </div>

            {analysisRecs.length > 0 && (
              <div className="rec-group">
                <div className="rec-group-head">
                  <h3>From the page analysis</h3>
                  <span className="muted-note">
                    Every recommendation names the measured features it was argued from.
                  </span>
                </div>
                <div className="rec-list">
                  {analysisRecs.map((r) => (
                    <RecommendationCard
                      key={r.id}
                      rec={r}
                      featureLabels={featureLabels}
                      checked={selected.has(r.id)}
                      onToggle={() => toggle(r.id)}
                    />
                  ))}
                </div>
              </div>
            )}

            {report.searchInterestLessons && (
              <SearchInterestSection lessons={report.searchInterestLessons} />
            )}

            {/* The model's second context group. */}
            {reputationRecs.length > 0 && (
              <div className="rec-group rec-group-reputation">
                <div className="rec-group-head">
                  <h3>From news-theme context</h3>
                  <span className="muted-note">
                    Kept apart from the analysis: these compare what a page claims to what the
                    press covers about the bank, and cite no page feature as evidence. Theme
                    counts are context, never sentiment or proof that a page or campaign
                    performed — treat each as a hypothesis to test.
                  </span>
                </div>
                <div className="rec-list">
                  {reputationRecs.map((r) => (
                    <RecommendationCard
                      key={r.id}
                      rec={r}
                      featureLabels={featureLabels}
                      checked={selected.has(r.id)}
                      onToggle={() => toggle(r.id)}
                    />
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {recommendations.length > 0 && (
          <div className="rec-controls card" style={{ marginTop: 18 }}>
            <div className="rec-build-row">
              <div>
                <div className="rec-summary-label">Build the website</div>
                <div className="muted-note" style={{ marginTop: 4 }}>
                  Generates a ten-page ING-styled site implementing the {selected.size} selected
                  recommendation{selected.size === 1 ? "" : "s"}
                  {selectedReputation > 0 && (
                    <>
                      {" "}({selectedAnalysis} from the analysis, {selectedReputation} from
                      reputation)
                    </>
                  )}.
                </div>
              </div>
              <div className="rec-build-actions">
                <label className="rec-lang">
                  Language
                  <select value={language} onChange={(e) => setLanguage(e.target.value)}>
                    <option value="fr">Français (fr-BE)</option>
                    <option value="nl">Nederlands (nl-BE)</option>
                    <option value="en">English (en-BE)</option>
                  </select>
                </label>
                <label className="rec-explain">
                  <input
                    type="checkbox"
                    checked={explainSite}
                    disabled={generating}
                    onChange={(e) => setExplainSite(e.target.checked)}
                  />
                  <span>
                    Explain each section
                    <small>Glowing box around every generated section, saying which recommendation it implements and why.</small>
                  </span>
                </label>
                <button
                  className="btn-action"
                  onClick={onGenerateSite}
                  disabled={selected.size === 0 || generating}
                >
                  {generating ? "Generating website…" : "Generate ING website"}
                </button>
              </div>
            </div>

            {generating && (
              <div className="rec-progress">
                <div className="rec-progress-track">
                  <div
                    className="rec-progress-fill"
                    style={{ width: `${site?.total ? (site.progress / site.total) * 100 : 4}%` }}
                  />
                </div>
                <div className="muted-note">
                  {site?.progress ?? 0} of {site?.total ?? 10} pages{site?.page ? ` · ${site.page}` : "…"}
                </div>
              </div>
            )}

            {site?.status === "error" && (
              <div className="scope-note" style={{ marginTop: 12 }}>{site.error}</div>
            )}

            {siteReady && (
              <div className="rec-ready">
                <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
                  <span className="rec-ready-badge">Website ready</span>
                  {siteUrl && (
                    <a className="btn-action" href={siteUrl} target="_blank" rel="noreferrer">
                      Browse generated website ↗
                    </a>
                  )}
                </div>
                {site?.manifest && (
                  <div className="rec-pages">
                    {site.manifest.pages.map((p) => (
                      <a key={p.slug} href={`/site/${p.file}`} target="_blank" rel="noreferrer">
                        <span className="rec-page-title">{p.title}</span>
                        <span className="rec-page-nav">{p.nav}</span>
                        {p.used_fallback && <span className="rec-page-fallback">fallback</span>}
                      </a>
                    ))}
                  </div>
                )}
                {site?.manifest && (
                  <div className="muted-note" style={{ marginTop: 10 }}>
                    {site.manifest.locale} · {site.manifest.model}
                    {site.manifest.explained && " · explained mode"}
                    {site.manifest.asset_warnings.length > 0 &&
                      ` · ${site.manifest.asset_warnings.length} asset(s) reused from cache`}
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </Section>
    </>
  );
}

function RecommendationCard({
  rec,
  featureLabels,
  checked,
  onToggle,
}: {
  rec: Recommendation;
  featureLabels: Record<string, string>;
  checked: boolean;
  onToggle: () => void;
}) {
  return (
    <div className={`rec-card${checked ? " selected" : ""}`}>
      <label className="rec-card-head">
        <input type="checkbox" checked={checked} onChange={onToggle} />
        <span className="rec-id">{rec.id}</span>
        <span className="rec-title">{rec.title}</span>
        <PriorityTag priority={rec.priority} />
      </label>
      <div className="rec-body">
        <div className="rec-field">
          <span className="rec-field-k">What the data shows</span>
          <span>{rec.finding}</span>
        </div>
        {rec.reputation_context && (
          <div className="rec-field">
            <span className="rec-field-k">Reputation context</span>
            <span>{rec.reputation_context}</span>
          </div>
        )}
        <div className="rec-field">
          <span className="rec-field-k">What to do</span>
          <span>{rec.recommendation}</span>
        </div>
        <div className="rec-meta">
          {rec.basis === "reputation" && (
            <span className="rec-basis-reputation" title="From news-theme context — coverage, not performance">
              reputation
            </span>
          )}
          {rec.features.map((f) => (
            <span key={f} className="rec-chip" title={f}>{featureLabels[f] ?? f}</span>
          ))}
          {rec.page_targets.length > 0 && (
            <span className="muted-note">Pages: {rec.page_targets.join(", ")}</span>
          )}
        </div>
      </div>
    </div>
  );
}

function Section({ title, lede, children }: { title: string; lede?: string; children: React.ReactNode }) {
  return (
    <section>
      <div className="section-head">
        <h2>{title}</h2>
        {lede && <p>{lede}</p>}
      </div>
      {children}
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
 * The two halves come from different sources and are joined on the bank name
 * and nothing else. Saying "they get searched for BECAUSE their pages do this"
 * is the one claim this project has no data for, so the caveat travels with
 * the payload rather than sitting in a footnote.
 */
function SearchInterestSection({ lessons }: { lessons: SearchInterestLessons }) {
  const focus = lessons.focus.toUpperCase();
  return (
    <div className="rec-group rec-group-trends">
      <div className="rec-group-head">
        <h3>From search-interest context</h3>
        <span className="muted-note">
          Google Trends picked these {lessons.banks.length} brands, on brand-search attention
          alone. What follows is what their pages measurably do differently from {focus}, on the
          same standardised features as the analysis above — never proof that those choices are
          why they are searched for.
        </span>
      </div>

      <div
        style={{
          display: "grid",
          gap: 12,
          gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
          marginBottom: 14,
        }}
      >
        {lessons.banks.map((b) => (
          <BenchmarkCard key={b.key} bank={b} focus={focus} />
        ))}
      </div>

      {lessons.common.length > 0 && (
        <div className="card" style={{ marginBottom: 12 }}>
          <h4 className="sub-h">What all {lessons.banks.length} have in common</h4>
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
        <div className="card" style={{ marginBottom: 12 }}>
          <h4 className="sub-h">Where they part company</h4>
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
    </div>
  );
}

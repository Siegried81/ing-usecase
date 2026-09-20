import { useCallback, useEffect, useMemo, useState } from "react";
import type { Priority, Recommendation, Report, SiteStatus } from "../types";
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
  const [includeTrends, setIncludeTrends] = useState(false);
  const trendsAvailable = Boolean(report.trends?.available);

  useEffect(() => {
    fetchRecommendations()
      .then((data) => {
        setPayload(data);
        setSelected(new Set(data.recommendations.map((r) => r.id)));
        // Keep the toggle in step with what was generated, so regenerating a
        // set that already used trends does not silently drop them.
        setIncludeTrends(Boolean(data.used_trends));
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
      const data = await generateRecommendations(includeTrends && trendsAvailable);
      setPayload(data);
      setSelected(new Set(data.recommendations.map((r) => r.id)));
      setIncludeTrends(Boolean(data.used_trends));
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }, [includeTrends, trendsAvailable]);

  const onGenerateSite = useCallback(async () => {
    setError(null);
    try {
      await generateSite([...selected], language);
      setSite(await fetchSiteStatus());
    } catch (e) {
      setError(String(e));
    }
  }, [selected, language]);

  const recommendations = useMemo(
    () =>
      [...(payload?.recommendations ?? [])].sort(
        (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority],
      ),
    [payload],
  );

  // sieg 20/09: a recommendation's `features` are raw snake_case ids (they're
  // machine-checked against the report), but showing "background_luminance"
  // to a reader looks unprofessional - map each id back to the same
  // human-readable label the Analysis tab already uses for it.
  const featureLabels = useMemo(() => {
    const map: Record<string, string> = {};
    for (const g of report.peerGaps) map[g.feature] = g.label;
    for (const s of report.separation) map[s.feature] = s.label;
    return map;
  }, [report]);

  // Two groups, one selection. Trends recommendations are shown apart because
  // they are argued from search-interest context, not from a measured page
  // feature - but they are picked in the same set and built into the same site.
  const analysisRecs = useMemo(() => recommendations.filter((r) => r.basis !== "trends"), [recommendations]);
  const trendsRecs = useMemo(() => recommendations.filter((r) => r.basis === "trends"), [recommendations]);
  const trendsCount = trendsRecs.length;
  const selectedTrends = trendsRecs.filter((r) => selected.has(r.id)).length;
  const selectedAnalysis = selected.size - selectedTrends;

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
                {payload.used_trends ? " · includes trends context" : ""}
              </span>
            )}
            {busy && <span className="muted-note">Asking {`deepseek-chat`} — this takes a few seconds…</span>}
          </div>

          <label className={`rec-trends${trendsAvailable ? "" : " disabled"}`}>
            <input
              type="checkbox"
              checked={includeTrends && trendsAvailable}
              disabled={!trendsAvailable || busy}
              onChange={(e) => setIncludeTrends(e.target.checked)}
            />
            <span>
              Include Google Trends to add recommendations
              <small>
                {trendsAvailable
                  ? "Adds timing and focus recommendations from search-interest context. Context only — never evidence that a page or campaign performed."
                  : "No trends export is present, so this option is unavailable. Run scripts/export_web_report.py to produce web/public/trends.json."}
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
            {trendsCount > 0 && (
              <div className="muted-note" style={{ marginTop: 6 }}>
                {trendsCount} further recommendation{trendsCount === 1 ? "" : "s"} come from
                search-interest context and appear in their own section below. They can be
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

            {trendsRecs.length > 0 && (
              <div className="rec-group rec-group-trends">
                <div className="rec-group-head">
                  <h3>From search-interest context</h3>
                  <span className="muted-note">
                    Kept apart from the analysis: these use Google Trends to suggest timing and
                    focus, and cite no page feature as evidence. Search interest is context, never
                    proof that a page or campaign performed — treat each as a hypothesis to test.
                  </span>
                </div>
                <div className="rec-list">
                  {trendsRecs.map((r) => (
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
                  {selectedTrends > 0 && (
                    <> ({selectedAnalysis} from the analysis, {selectedTrends} from trends)</>
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
        {rec.market_context && (
          <div className="rec-field">
            <span className="rec-field-k">Market context</span>
            <span>{rec.market_context}</span>
          </div>
        )}
        <div className="rec-field">
          <span className="rec-field-k">What to do</span>
          <span>{rec.recommendation}</span>
        </div>
        <div className="rec-meta">
          {rec.basis === "trends" && (
            <span className="rec-basis-trends" title="From search-interest context — attention, not performance">
              trends
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

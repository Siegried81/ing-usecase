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

  useEffect(() => {
    fetchRecommendations()
      .then((data) => {
        setPayload(data);
        setSelected(new Set(data.recommendations.map((r) => r.id)));
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
      const data = await generateRecommendations();
      setPayload(data);
      setSelected(new Set(data.recommendations.map((r) => r.id)));
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  }, []);

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
              </span>
            )}
            {busy && <span className="muted-note">Asking {`deepseek-chat`} — this takes a few seconds…</span>}
          </div>
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

            <div className="rec-list">
              {recommendations.map((r) => (
                <RecommendationCard
                  key={r.id}
                  rec={r}
                  checked={selected.has(r.id)}
                  onToggle={() => toggle(r.id)}
                />
              ))}
            </div>
          </>
        )}

        {recommendations.length > 0 && (
          <div className="rec-controls card" style={{ marginTop: 18 }}>
            <div className="rec-build-row">
              <div>
                <div className="rec-summary-label">Build the website</div>
                <div className="muted-note" style={{ marginTop: 4 }}>
                  Generates a ten-page ING-styled site implementing the {selected.size} selected
                  recommendation{selected.size === 1 ? "" : "s"}.
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
  checked,
  onToggle,
}: {
  rec: Recommendation;
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
        <div className="rec-field">
          <span className="rec-field-k">What to do</span>
          <span>{rec.recommendation}</span>
        </div>
        <div className="rec-meta">
          {rec.features.map((f) => (
            <code key={f} className="rec-chip">{f}</code>
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

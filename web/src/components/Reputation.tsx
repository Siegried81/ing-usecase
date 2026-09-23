import type { Report, ReputationHeadline } from "../types";

const themeLabel = (theme: string) => theme.replace(/_/g, " ");

/** Hover popup on a theme's count - the full list of articles it is made of. */
function ThemeCount({ count, headlines }: { count: number; headlines: ReputationHeadline[] }) {
  if (headlines.length === 0) return <span className="sd above">{count}</span>;
  return (
    <span className="sd above rep-theme-count">
      {count}
      <div className="rep-theme-popup">
        {headlines.map((h, i) =>
          h.url ? (
            <a key={i} href={h.url} target="_blank" rel="noreferrer">
              {h.title}
            </a>
          ) : (
            <span key={i}>{h.title}</span>
          ),
        )}
      </div>
    </span>
  );
}

/** Every headline for a bank, in one collapsible dropdown - not just the
 * up-to-5 "notable" ones. Native <details>, so it works without JS state and on touch
 * (the per-theme hover above does not). */
function AllSources({ themeHeadlines }: { themeHeadlines: Record<string, ReputationHeadline[]> }) {
  const all = Object.values(themeHeadlines).flat();
  if (all.length === 0) return null;
  return (
    <details className="rep-sources">
      <summary>{all.length} source{all.length === 1 ? "" : "s"}</summary>
      <div className="rep-sources-list">
        {all.map((h, i) =>
          h.url ? (
            <a key={i} href={h.url} target="_blank" rel="noreferrer">
              {h.title}
            </a>
          ) : (
            <span key={i}>{h.title}</span>
          ),
        )}
      </div>
    </details>
  );
}

/**
 * NewsAPI headline themes per bank - counts only, never sentiment
 * (see comparator/reputation.py's docstring for why). Mirrors Trends.tsx's
 * "not configured, nothing else affected" empty state when NEWSAPI_KEY isn't set.
 * Hovering a theme's count opens every article behind it (ThemeCount),
 * and "N sources" below opens every article for the bank, of any theme (AllSources).
 */
export function Reputation({ reputation }: { reputation: Report["reputation"] }) {
  if (!reputation.available) {
    return (
      <div className="card">
        <h2 style={{ marginTop: 0 }}>Reputation tracking not configured</h2>
        <p style={{ color: "var(--ink-2)" }}>
          Set <code>NEWSAPI_KEY</code> in <code>.env</code> to see recent news headline themes
          per bank here. Nothing else is affected.
        </p>
      </div>
    );
  }

  const entries = Object.entries(reputation.banks);

  return (
    <>
      <p style={{ color: "var(--ink-2)", margin: "0 0 16px", fontSize: 14.5 }}>
        Headline themes say what a bank is being written about. They are context
        about the bank, never evidence that a page or a campaign performed — no
        performance data exists in this project, so nothing here shows how well a
        campaign is doing. A bank with no themes listed either had no matching
        headlines or could not be fetched; the two look the same from here.
      </p>
      <div className="banks">
      {entries.map(([key, snapshot]) => (
        <div key={key} className="bank">
          <div className="bank-top">
            <span className="bank-name">{key}</span>
          </div>
          {!snapshot ? (
            <div style={{ fontSize: 12.5, color: "var(--ink-3)" }}>no headlines recorded</div>
          ) : (
            <>
              <div style={{ fontSize: 12.5, color: "var(--ink-3)", marginBottom: 8 }}>
                {snapshot.headline_count} headline{snapshot.headline_count === 1 ? "" : "s"} scanned
              </div>
              {Object.entries(snapshot.themes)
                .filter(([, count]) => count > 0)
                .sort(([, a], [, b]) => b - a)
                .map(([theme, count]) => (
                  <div className="sig" key={theme}>
                    <ThemeCount count={count} headlines={snapshot.theme_headlines[theme] ?? []} />
                    <span>{themeLabel(theme)}</span>
                  </div>
                ))}
              <AllSources themeHeadlines={snapshot.theme_headlines} />
            </>
          )}
        </div>
      ))}
      </div>
    </>
  );
}

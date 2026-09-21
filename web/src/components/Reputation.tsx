import type { Report, ReputationHeadline } from "../types";

const themeLabel = (theme: string) => theme.replace(/_/g, " ");

/** sieg 21/09: hover popup on a theme's count - the full list of articles it is made of. */
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

/**
 * sieg 19/09: NewsAPI headline themes per bank - counts only, never sentiment
 * (see comparator/reputation.py's docstring for why). Mirrors Trends.tsx's
 * "not configured, nothing else affected" empty state when NEWSAPI_KEY isn't set.
 * sieg 21/09: the notable headline links out to its source when one was found, and
 * hovering a theme's count opens every article behind it (ThemeCount above).
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
    <div className="banks">
      {entries.map(([key, snapshot]) => (
        <div key={key} className="bank">
          <div className="bank-top">
            <span className="bank-name">{key}</span>
          </div>
          {!snapshot ? (
            <div style={{ fontSize: 12.5, color: "var(--ink-3)" }}>no recent headlines found</div>
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
              {snapshot.notable_headlines.length > 0 && (
                <div style={{ marginTop: 10, display: "grid", gap: 4 }}>
                  {/* sieg 21/09: all of the (up to 5) notable headlines, not just the
                      first - each links to its source when reputation.py found one,
                      never a URL the model produced itself. */}
                  {snapshot.notable_headlines.map((h, i) => (
                    <div key={i} style={{ fontSize: 12.5, color: "var(--ink-3)" }}>
                      {h.url ? (
                        <a href={h.url} target="_blank" rel="noreferrer" style={{ color: "inherit" }}>
                          {h.title} ↗
                        </a>
                      ) : (
                        h.title
                      )}
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      ))}
    </div>
  );
}

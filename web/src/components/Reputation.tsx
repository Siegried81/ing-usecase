import type { Report } from "../types";

const themeLabel = (theme: string) => theme.replace(/_/g, " ");

/**
 * sieg 19/09: NewsAPI headline themes per bank - counts only, never sentiment
 * (see comparator/reputation.py's docstring for why). Mirrors Trends.tsx's
 * "not configured, nothing else affected" empty state when NEWSAPI_KEY isn't set.
 * sieg 21/09: the notable headline links out to its source when one was found.
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
                    <span className="sd above">{count}</span>
                    <span>{themeLabel(theme)}</span>
                  </div>
                ))}
              {snapshot.notable_headlines.length > 0 && (
                <div style={{ marginTop: 10, fontSize: 12.5, color: "var(--ink-3)" }}>
                  {/* sieg 21/09: link to the source when reputation.py found one -
                      never a URL the model produced itself. */}
                  {snapshot.notable_headlines[0].url ? (
                    <a
                      href={snapshot.notable_headlines[0].url}
                      target="_blank"
                      rel="noreferrer"
                      style={{ color: "inherit" }}
                    >
                      {snapshot.notable_headlines[0].title} ↗
                    </a>
                  ) : (
                    snapshot.notable_headlines[0].title
                  )}
                </div>
              )}
            </>
          )}
        </div>
      ))}
    </div>
  );
}

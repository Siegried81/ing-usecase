import { useState } from "react";
import type { ResearchPaper } from "../types";
import { searchResearch } from "../api";

/**
 * Semantic Scholar search, for sourcing claims in the business narrative.
 *
 * This is the one live call in the operator surface, so it is deliberately a
 * search box and nothing more: it has no defined metric and is not attached to
 * a per-bank number, because inventing a metric to justify it would be scope
 * the module never claimed. `comparator/research.py` returns [] on a rate
 * limit rather than raising, so an empty result is reported as "nothing came
 * back", not as success.
 */
export function Research() {
  const [query, setQuery] = useState("");
  const [limit, setLimit] = useState(5);
  const [papers, setPapers] = useState<ResearchPaper[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await searchResearch(query.trim(), limit);
      setPapers(result.papers);
    } catch (e) {
      setError(String(e));
      setPapers(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <p style={{ margin: "0 0 14px", color: "var(--ink-2)", fontSize: 14.5, maxWidth: "78ch" }}>
        Searches Semantic Scholar for papers that support a claim in the narrative. Works without an API key at
        low volume; a key in <code>SEMANTIC_SCHOLAR_API_KEY</code> only raises the rate limit.
      </p>

      <div className="search-row">
        <input
          className="text-input"
          placeholder="e.g. cross-selling retail banking"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && query.trim()) run(); }}
        />
        <label className="rec-lang">
          <span>Max results</span>
          <select value={limit} onChange={(e) => setLimit(Number(e.target.value))}>
            {[1, 3, 5, 10, 20].map((n) => <option key={n} value={n}>{n}</option>)}
          </select>
        </label>
        <button className="btn-action" disabled={!query.trim() || loading} onClick={run}>
          {loading ? "Searching…" : "Search"}
        </button>
      </div>

      {error && (
        <div className="scope-note" style={{ marginTop: 14 }}>
          Search needs the backend. Start <code>python3 scripts/serve_web.py</code> and try again. ({error})
        </div>
      )}

      {papers !== null && papers.length === 0 && !error && (
        <div className="scope-note" style={{ marginTop: 14 }}>
          No papers returned. Either nothing matched, or the request was rate-limited — Semantic Scholar's
          public access without a key has a low limit. Try again in a moment.
        </div>
      )}

      {papers?.map((p, i) => (
        <div className="paper" key={i}>
          <div className="paper-title">
            {p.url ? <a href={p.url} target="_blank" rel="noreferrer">{p.title ?? "(untitled)"}</a> : (p.title ?? "(untitled)")}
            {p.year && <span className="muted-note"> ({p.year})</span>}
          </div>
          {p.abstract && (
            <p className="paper-abstract">
              {p.abstract.length > 400 ? `${p.abstract.slice(0, 400)}…` : p.abstract}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}

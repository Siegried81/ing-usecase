import type { Report } from "../types";

/** Markdown bold survives into the JSON; render it rather than showing asterisks. */
function Rich({ text }: { text: string }) {
  const parts = text.split(/\*\*(.+?)\*\*/g);
  return <>{parts.map((p, i) => (i % 2 ? <strong key={i}>{p}</strong> : <span key={i}>{p}</span>))}</>;
}

/**
 * Not an appendix. A business reader deciding something on the strength of this
 * needs to know what it cannot support, and burying that at the end of a deck is
 * how a caveat gets lost between the room and the decision.
 */
export function Limitations({ limitations }: { limitations: Report["limitations"] }) {
  const groups: [string, string[], string][] = [
    ["Questions this cannot answer", limitations.blocking, "Something is missing that no interpretation can replace."],
    ["Findings that survive, but weakened", limitations.material, "Real, and narrower than they look."],
    ["True however much more we collect", limitations.standing, "Properties of the method, not of this dataset."],
  ];
  return (
    <div className="card lim">
      {groups.map(([title, items, note]) =>
        items.length ? (
          <div key={title}>
            <h3>{title}</h3>
            <p style={{ margin: "0 0 8px", fontSize: 13.5, color: "var(--ink-3)" }}>{note}</p>
            <ul>{items.map((t, i) => <li key={i}><Rich text={t} /></li>)}</ul>
          </div>
        ) : null
      )}
    </div>
  );
}

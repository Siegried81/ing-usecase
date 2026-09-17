import type { Report } from "../types";

const cls = (v: string) =>
  v === "supported" ? "supported" : v === "not supported" ? "not" : "untestable";

/**
 * The five observations from ING's own kickoff deck, tested against the data.
 * Most of them do not hold — which is the single most useful thing in here, and
 * the reason it is shown rather than quietly dropped.
 */
export function DeckClaims({ claims }: { claims: Report["deckClaims"] }) {
  return (
    <div className="card">
      <table className="claims">
        <thead>
          <tr><th>What the kickoff deck said</th><th>Verdict</th><th>What the data shows</th></tr>
        </thead>
        <tbody>
          {claims.map((c) => (
            <tr key={c.id}>
              <td className="claim">{c.claim}</td>
              <td><span className={`verdict ${cls(c.verdict)}`}>{c.verdict}</span></td>
              <td>{c.evidence}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

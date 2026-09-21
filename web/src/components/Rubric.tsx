import type { RubricPayload } from "../types";
import { DataTable } from "./Table";
import { Section } from "./Section";

/**
 * The rubric sheets, the disagreement between them, and the scoring guide.
 *
 * Two things this page refuses to do, both deliberate (NFR-05):
 *   * it never merges the sheets into a single "score" - the disagreement is
 *     the finding until the wording is tightened;
 *   * it shows every sheet side by side only because this is the read-only view
 *     after the fact. A live scoring screen must never show another rater's
 *     numbers, or the agreement becomes an artefact of who looked at what.
 */
export function Rubric({ rubric }: { rubric: RubricPayload }) {
  const scored = rubric.raters.filter((r) => r.name !== "model");
  return (
    <>
      <Section
        title="Rubric scoring"
        lede="13 judgement-based features, scored independently by two people. The model writes to its own sheet, so agreement keeps measuring agreement."
      >
        <div className="card">
          <p style={{ margin: 0, color: "var(--ink-2)", fontSize: 14.5 }}>
            {scored.length} human sheet{scored.length === 1 ? "" : "s"} and{" "}
            {rubric.raters.length - scored.length} model sheet present. The model's sheet is never merged with a
            person's, and no sheet here is a pre-fill for another.
          </p>
          <ul className="command-list" style={{ marginTop: 12 }}>
            <li><code>python3 scripts/rubric_sheet.py emit</code></li>
            <li><code>python3 scripts/rubric_sheet.py merge</code></li>
            <li><code>python3 scripts/rubric_sheet.py agreement --sheets data/rubric/*_scores.csv</code></li>
          </ul>
        </div>
      </Section>

      <Section title="Sheets" lede="Every column as stored in data/rubric/. Blank stays blank — a missing score is reported, an invented one is not.">
        {rubric.raters.length === 0 && (
          <div className="card"><div className="muted-note">No scoring sheets found. Run the emit command above.</div></div>
        )}
        {rubric.raters.map((rater) => (
          <details className="rater" key={rater.name}>
            <summary>
              <span className="rec-title">{rater.label}</span>
              <span className="muted-note">{rater.pages} pages</span>
            </summary>
            <div style={{ marginTop: 12 }}>
              <DataTable columns={rater.columns} rows={rater.rows} maxHeight={340} minWidth={1100} />
            </div>
          </details>
        ))}
      </Section>

      <Section
        title="Inter-rater agreement"
        lede="Raw share of pages where raters landed on the same value (or within one point on a scale). Below 60% is flagged — tighten the wording before trusting the feature."
      >
        <DataTable
          columns={["feature", "pages", "agreement", "basis"]}
          rows={rubric.agreement}
          maxHeight={420}
          empty="No feature was scored by more than one rater — agreement cannot be measured."
          rowClass={(row) => (Number(row.agreement) < 0.6 ? "weak-row" : undefined)}
        />
      </Section>

      <Section
        title="Cohen's kappa"
        lede="Chance-corrected agreement per pair of raters. Raw % can look fine while being close to chance, especially on a 1-5 scale."
      >
        <DataTable
          columns={["feature", "raters", "pages", "kappa"]}
          rows={rubric.kappa}
          maxHeight={420}
          empty="Not enough overlapping scores to compute kappa."
          rowClass={(row) => (Number(row.kappa) < 0.4 ? "weak-row" : undefined)}
        />
      </Section>

      <Section title="Scoring guide — features to score" lede="Generated from the frozen dictionary, so the levels a rater reads and the values the validator accepts cannot drift apart.">
        {rubric.features.map((f) => (
          <div className="card guide" key={f.name}>
            <div className="guide-head">
              <code>{f.name}</code>
              <span className="muted-note">{f.label}</span>
            </div>
            <p style={{ margin: "6px 0", color: "var(--ink-2)", fontSize: 14.5 }}>{f.definition}</p>
            {f.values && (
              <div className="rec-meta">
                {f.values.map((v) => <span className="rec-chip" key={v}>{v}</span>)}
              </div>
            )}
            {!f.values && f.range && (
              <div className="muted-note">Enter a whole number from {f.range[0]} to {f.range[1]}.</div>
            )}
            {f.rubric && (
              <table className="kv" style={{ marginTop: 10 }}>
                <tbody>
                  {Object.entries(f.rubric).sort(([a], [b]) => Number(a) - Number(b)).map(([level, text]) => (
                    <tr key={level}>
                      <th>Level {level}</th>
                      <td>{text}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
            {f.notes && <div className="muted-note" style={{ marginTop: 8, fontStyle: "italic" }}>{f.notes}</div>}
          </div>
        ))}
      </Section>
    </>
  );
}

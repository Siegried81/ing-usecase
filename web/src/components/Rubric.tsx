import type { RubricPayload } from "../types";
import { DataTable } from "./Table";
import { Section } from "./Section";

/**
 * The judged sheet and the scales it was scored against.
 *
 * This page used to sit two or more sheets side by side and report
 * the disagreement between them. The project now runs on one judged sheet, so
 * there is nothing to compare - and rather than leave an empty agreement table
 * implying the question was asked and came back blank, the page says in words
 * that no reliability measure exists and why.
 *
 * Still read-only, and still after the fact: a live scoring screen must never
 * show one person's numbers to another.
 */
export function Rubric({ rubric }: { rubric: RubricPayload }) {
  return (
    <>
      <Section
        title="Rubric scoring"
        lede="13 judgement-based features, scored by one named person against a written scale."
      >
        <div className="card">
          <p style={{ margin: 0, color: "var(--ink-2)", fontSize: 14.5 }}>
            {rubric.raters.length} sheet{rubric.raters.length === 1 ? "" : "s"} present.
          </p>
          <ul className="command-list" style={{ marginTop: 12 }}>
            <li><code>python3 scripts/rubric_sheet.py emit</code></li>
            <li><code>python3 scripts/rubric_sheet.py merge --sheet data/rubric/siegried_scores.csv</code></li>
          </ul>
        </div>
      </Section>

      <Section title="Reliability" lede="What this scoring does and does not establish.">
        <div className="scope-note">{rubric.reliability}</div>
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

import { useEffect, useState } from "react";
import type { Report } from "./types";
import { ScopeBanner } from "./components/Scope";
import { Positioning } from "./components/Positioning";
import { PeerGaps, GroupSeparation } from "./components/Gaps";
import { BankCards } from "./components/Banks";
import { GeneratedCampaigns } from "./components/Generated";
import { Limitations } from "./components/Limitations";
import { DeckClaims } from "./components/Claims";

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

export default function App() {
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}report.json`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(`${r.status}`))))
      .then(setReport)
      .catch((e) => setError(String(e)));
  }, []);

  if (error) {
    return (
      <div className="wrap" style={{ paddingTop: 60 }}>
        <div className="card">
          <h2 style={{ marginTop: 0 }}>No report to show</h2>
          <p style={{ color: "var(--ink-2)" }}>
            Generate one first:<br />
            <code>python3 scripts/export_web_report.py</code>
          </p>
          <p style={{ color: "var(--ink-3)", fontSize: 13 }}>{error}</p>
        </div>
      </div>
    );
  }
  if (!report) return <div className="wrap" style={{ paddingTop: 60, color: "var(--ink-3)" }}>Loading…</div>;

  const { scope, headline } = report;
  const focusBank = report.banks.find((b) => b.name === headline.focus);
  const nearest = report.nearestToFocus[0];
  const biggest = report.peerGaps[0];

  return (
    <>
      <div className="masthead">
        <div className="wrap">
          <div className="eyebrow">Banking campaigns comparator</div>
          <h1>How Belgian banks communicate the same product — and where ING sits</h1>
          <div className="sub">
            Prepared for ING · DACI / Customer AI &nbsp;·&nbsp; a proof of concept, not a production study
          </div>
        </div>
      </div>

      <div className="wrap">
        <ScopeBanner scope={scope} />

        <div className="headline">
          <div className="q">The question</div>
          <div className="a">
            {headline.has_focus ? (
              <>
                On {scope.product_family_label.toLowerCase()}, {headline.focus} communicates{" "}
                <em>{headline.verdict?.replace("clearly with the ", "like the ").replace(" banks", " banks")}</em>.
              </>
            ) : (
              <>{headline.focus} has no usable page in this comparison.</>
            )}
          </div>
          {headline.has_focus && (
            <div className="why">
              Across {scope.n_features} measured features, {headline.focus} scores{" "}
              <strong>{headline.score?.toFixed(2)}</strong> on a scale where 0 is the average incumbent
              and 1 the average challenger. Its closest neighbour is{" "}
              <strong>{nearest?.bank}</strong>.
              {biggest && (
                <> The sharpest difference from its peers is <strong>{biggest.label.toLowerCase()}</strong> —{" "}
                  {biggest.direction === "above" ? "notably more" : "notably less"} than the others.</>
              )}
            </div>
          )}
        </div>

        <Section
          title="Where each bank sits"
          lede="Every bank reduced to the features we measured, then projected onto the one axis the question asks about. 0 is the average incumbent, 1 the average challenger."
        >
          <Positioning banks={report.positioning} />
        </Section>

        {report.peerGaps.length > 0 && (
          <Section
            title={`What makes ${headline.focus} different`}
            lede={`How far ${headline.focus} sits from the average of the other banks on this product, largest differences first.`}
          >
            <PeerGaps gaps={report.peerGaps} focus={headline.focus} />
            <div className="legend">
              <span className="judged">judged</span> a person scored this against a written rubric ·{" "}
              <span className="judged">model-judged</span> a language model did, and no human has
              checked it yet. Everything unmarked was counted or measured from the page.
            </div>
            {report.excludedGaps.length > 0 && (
              <div className="scope-note" style={{ marginTop: 12 }}>
                <strong>Not shown:</strong>{" "}
                {report.excludedGaps.map((g) => g.label.toLowerCase()).join(", ")} — the peer values
                were too close together or too incomplete for the comparison to mean anything.
              </div>
            )}
          </Section>
        )}

        <Section
          title="What separates incumbents from challengers"
          lede="The features on which the two business models differ most. Descriptive only — with this many banks these are patterns to notice, not statistically tested effects."
        >
          <GroupSeparation rows={report.separation} />
        </Section>

        <Section
          title="Each bank at a glance"
          lede="Identical fields for every bank, generated from the data. The numbers are how far that bank sits from the market average, in standard deviations."
        >
          <BankCards banks={report.banks} focusKey={focusBank?.key ?? ""} />
        </Section>

        {report.deckClaims.length > 0 && (
          <Section
            title="Testing the assumptions in the kickoff deck"
            lede="Five observations from ING's own briefing, checked against the measured pages."
          >
            <DeckClaims claims={report.deckClaims} />
          </Section>
        )}

        {report.trends && (
          <Section
            title="Search interest, for context"
            lede="What people searched for around these products. Context only — it measures attention, not what any campaign achieved."
          >
            <div className="card">
              {report.trends.rows.map((r, i) => (
                <div className="score-row" key={i}>
                  <span>{r.bank} · {r.family}</span>
                  <span style={{ color: "var(--ink-2)" }}>{r.direction}</span>
                </div>
              ))}
              {report.trends.uncovered.length > 0 && (
                <div style={{ marginTop: 10, fontSize: 13, color: "var(--ink-3)" }}>
                  No search data for {report.trends.uncovered.join(", ")}.
                </div>
              )}
            </div>
          </Section>
        )}

        {report.generated.length > 0 && (
          <Section
            title="What the framework can produce"
            lede="Campaigns written to an explicit target expressed in the same features, then measured by the same extractor that reads the real pages. The point is that the framework is specific enough to steer and then check a generation."
          >
            <GeneratedCampaigns campaigns={report.generated} />
          </Section>
        )}

        <Section
          title="What this cannot tell you"
          lede="Read before acting on anything above."
        >
          <Limitations limitations={report.limitations} />
        </Section>

        <div className="foot">
          Generated {new Date(report.generated_at).toLocaleString("en-GB")} from{" "}
          <code>{report.dataset}</code>. Every figure traces to a stored page capture.
          This is a proof of concept on a deliberately limited scope.
        </div>
      </div>
    </>
  );
}

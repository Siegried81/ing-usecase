import type { GeneratedCampaign } from "../types";

/**
 * The generated campaigns, always beside their scorecard.
 *
 * Plan risk P-08 is that this looks impressive and gets over-claimed. So the
 * copy is never shown alone: the synthetic label, the measured scorecard and
 * the "says nothing about performance" line travel with it, on screen, in the
 * same block a stakeholder screenshots.
 */
export function GeneratedCampaigns({ campaigns }: { campaigns: GeneratedCampaign[] }) {
  return (
    <>
      {campaigns.map((c) => (
        <div className="card" key={c.variant} style={{ marginBottom: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <strong style={{ fontSize: 16 }}>{c.title}</strong>
            <span className="synthetic">● Synthetic — never published</span>
            {c.hitRate !== null && (
              <span style={{ marginLeft: "auto", fontSize: 13.5, color: "var(--ink-2)" }}>
                hit {Math.round(c.hitRate * 100)}% of measured targets
              </span>
            )}
          </div>

          <div className="gen" style={{ marginTop: 14 }}>
            <div className="gen-copy">
              <h3>{c.headline}</h3>
              <div className="sub">{c.subheading}</div>
              {c.body.slice(0, 2).map((p, i) => <p key={i}>{p}</p>)}
              <div style={{ marginTop: 10 }}>
                <span className="cta-pill" style={{ background: c.accent }}>{c.cta}</span>
                {c.additionalCtas.slice(0, 2).map((cta) => (
                  <span className="cta-pill" key={cta} style={{ background: "var(--ink-3)" }}>{cta}</span>
                ))}
              </div>
              <div style={{ marginTop: 12, fontSize: 12.5, color: "var(--ink-3)" }}>
                {c.disclaimer}
              </div>
            </div>

            <div>
              <div style={{ fontSize: 11.5, letterSpacing: ".06em", textTransform: "uppercase",
                            color: "var(--ink-3)", fontWeight: 600, marginBottom: 6 }}>
                Scored by the same extractor as the real pages
              </div>
              {c.scorecard.map((s) => (
                <div className="score-row" key={s.label}>
                  <span>{s.label}</span>
                  <span className={`pill ${s.result === "hit" ? "hit" : "miss"}`}>{s.result}</span>
                </div>
              ))}
              <div style={{ marginTop: 10, fontSize: 12.5, color: "var(--ink-3)" }}>
                {c.model} · prompt {c.promptHash}
              </div>
            </div>
          </div>

          <div className="scope-note" style={{ marginTop: 14 }}>
            Hitting a target means the model followed instructions. It says <strong>nothing</strong> about
            whether this campaign would perform better — no performance data exists in this study.
          </div>
        </div>
      ))}
    </>
  );
}

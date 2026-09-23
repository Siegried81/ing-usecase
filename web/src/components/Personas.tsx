import type { BankProfile } from "../types";

/**
 * Which customer personas each bank's pages target, and how often.
 * Reuses the existing .bank card shell (Banks.tsx) and .bar-track/.bar-fill
 * bars (Gaps.tsx) rather than inventing new styling - a share is a fraction of
 * this bank's own pages, not a diverging comparison, so bars start at 0% here
 * instead of the 50%-midpoint pattern PeerGaps/GroupSeparation use.
 */
export function Personas({ banks }: { banks: BankProfile[] }) {
  return (
    <div className="banks">
      {banks.map((b) => (
        <div key={b.key} className="bank">
          <div className="bank-top">
            <span className="swatch" style={{ background: b.palette.dominant ?? "var(--line)" }} />
            <span className="bank-name">{b.name}</span>
            <span className={`tag ${b.category}`}>{b.category}</span>
          </div>
          {b.personas.length === 0 ? (
            <div style={{ fontSize: 12.5, color: "var(--ink-3)" }}>no persona clearly targeted</div>
          ) : (
            b.personas.map((p) => (
              <div className="bar-row" key={p.persona} style={{ gridTemplateColumns: "1fr 120px 46px" }}>
                <div className="bar-label">{p.label}</div>
                <div className="bar-track">
                  <span
                    className="bar-fill"
                    style={{ left: 0, width: `${p.share * 100}%`, background: "var(--focus-ring)" }}
                  />
                </div>
                <div className="bar-value">{(p.share * 100).toFixed(0)}%</div>
              </div>
            ))
          )}
        </div>
      ))}
    </div>
  );
}

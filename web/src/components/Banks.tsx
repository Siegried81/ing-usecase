import type { BankProfile } from "../types";

/**
 * One card per bank, identical fields, generated from the dataset. The
 * signature line is the three features on which that bank departs most from the
 * market — computed, not written, so nobody can quietly flatter anyone.
 */
export function BankCards({ banks, focusKey }: { banks: BankProfile[]; focusKey: string }) {
  return (
    <div className="banks">
      {banks.map((b) => (
        <div key={b.key} className={`bank${b.key === focusKey ? " focus" : ""}`}>
          <div className="bank-top">
            <span
              className="swatch"
              style={{ background: b.palette.dominant ?? "var(--line)" }}
              title={b.palette.dominant ?? "no dominant colour measured"}
            />
            <span className="bank-name">{b.name}</span>
            <span className={`tag ${b.category}`}>{b.category}</span>
          </div>
          <div>
            {b.signature.map((s) => (
              <div className="sig" key={s.label}>
                <span className={`sd ${s.direction}`}>{s.sd > 0 ? "+" : ""}{s.sd}</span>
                <span>{s.label}</span>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 10, fontSize: 12.5, color: "var(--ink-3)" }}>
            {b.pages} page{b.pages === 1 ? "" : "s"} analysed
          </div>
        </div>
      ))}
    </div>
  );
}

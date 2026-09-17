import type { Scope } from "../types";

const date = (iso: string | null) =>
  iso ? new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" }) : "—";

/**
 * Every qualifier a reader needs before they look at a single number: which
 * product, which banks, when, and who is missing. It sits above the findings
 * rather than in a footnote, because the one thing this analysis must not do is
 * let someone quote a figure without knowing its scope.
 */
export function ScopeBanner({ scope }: { scope: Scope }) {
  return (
    <div className="scope">
      <div className="scope-grid">
        <div className="scope-item">
          <div className="k">Product compared</div>
          <div className="v">{scope.product_family_label}</div>
        </div>
        <div className="scope-item">
          <div className="k">Banks</div>
          <div className="v">{scope.banks.length} &nbsp;<span style={{ fontWeight: 400, color: "var(--ink-3)" }}>
            {scope.traditional.length} traditional · {scope.challenger.length} challenger
          </span></div>
        </div>
        <div className="scope-item">
          <div className="k">Pages analysed</div>
          <div className="v">{scope.pages}<span style={{ fontWeight: 400, color: "var(--ink-3)" }}> of {scope.total_collected} collected</span></div>
        </div>
        <div className="scope-item">
          <div className="k">Features measured</div>
          <div className="v">{scope.n_features}</div>
        </div>
        <div className="scope-item">
          <div className="k">Captured</div>
          <div className="v">{date(scope.captured_from)}</div>
        </div>
        <div className="scope-item">
          <div className="k">Language</div>
          <div className="v">{scope.languages.map((l) => l.toUpperCase()).join(", ") || "—"}</div>
        </div>
      </div>

      {(scope.excluded.length > 0 || scope.uncollectable.length > 0) && (
        <div className="scope-note">
          {scope.excluded.length > 0 && (
            <div>
              <strong>Not in this comparison:</strong>{" "}
              {scope.excluded.map((e) => e.bank).join(", ")} — {scope.excluded[0].reason}.
              Comparing across product families would confound every difference with the product itself.
            </div>
          )}
          {scope.uncollectable.length > 0 && (
            <div style={{ marginTop: scope.excluded.length ? 6 : 0 }}>
              <strong>Could not be captured:</strong>{" "}
              {scope.uncollectable.map((u) => u.bank).join(", ")}.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

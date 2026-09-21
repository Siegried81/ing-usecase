import { useState } from "react";
import type { AiScoreAxis, BankProfile } from "../types";
import { format } from "./Table";

/**
 * The per-bank profile card, expanded: everything the report measured about one
 * bank, the same fields for every bank.
 *
 * The signature bars are the bank's own z-scores, so a longer bar always means
 * "further from the market average", never "better". Only the palette swatch
 * and the capture come from outside the JSON; the capture is served by the
 * backend and degrades to a note when it is not running.
 */
export function Profiles({ banks, axes }: { banks: BankProfile[]; axes: AiScoreAxis[] }) {
  const [selected, setSelected] = useState(banks[0]?.key ?? "");
  const bank = banks.find((b) => b.key === selected) ?? banks[0];

  if (!bank) return <div className="muted-note">No bank profiles in this report.</div>;

  const signatureMax = Math.max(1, ...bank.signature.map((s) => Math.abs(s.sd)));

  return (
    <>
      <div className="profile-picker">
        <label className="rec-lang">
          <span>Choose a bank</span>
          <select value={bank.key} onChange={(e) => setSelected(e.target.value)}>
            {banks.map((b) => (
              <option key={b.key} value={b.key}>{b.name}</option>
            ))}
          </select>
        </label>
        <div className="profile-head">
          <span className="bank-name" style={{ fontSize: 20 }}>{bank.name}</span>
          <span className={`tag ${bank.category}`}>{bank.category}</span>
          <span style={{ color: "var(--ink-3)", fontSize: 13 }}>
            {bank.pages} page{bank.pages === 1 ? "" : "s"} analysed
          </span>
        </div>
      </div>

      <div className="profile-grid">
        <div className="card">
          <h3 className="sub-h">Palette &amp; design</h3>
          <div
            className="palette-swatch"
            style={{ background: bank.palette.dominant ?? "var(--line)" }}
            title={bank.palette.dominant ?? "no dominant colour measured"}
          />
          <KeyValue
            rows={[
              ["Dominant colour", bank.palette.dominant],
              ["Brand colour share", bank.palette.brandShare],
              ["Background luminance", bank.palette.backgroundLuminance],
            ]}
          />
          <h3 className="sub-h" style={{ marginTop: 18 }}>Capture</h3>
          <Capture bankKey={bank.key} name={bank.name} />
        </div>

        <div className="card">
          <h3 className="sub-h">AI Score</h3>
          <p className="muted-note" style={{ marginTop: 0 }}>
            0-10 per axis, computed from the dictionary. A blank is no data, never a zero.
          </p>
          {axes.map((axis) => (
            <div className="bar-row" key={axis.key} style={{ gridTemplateColumns: "1fr 150px 44px" }}>
              <div className="bar-label">{axis.label}</div>
              <div className="bar-track">
                <span
                  className="bar-fill"
                  style={{ left: 0, width: `${((bank.aiScore[axis.key] ?? 0) / 10) * 100}%`, background: "var(--focus-ring)" }}
                />
              </div>
              <div className="bar-value">{bank.aiScore[axis.key] ?? "—"}</div>
            </div>
          ))}
          <div className="rec-meta" style={{ marginTop: 14 }}>
            <span className="rec-chip">
              Cross-sell: {bank.crossSellScore === null ? "no data" : `${(bank.crossSellScore * 100).toFixed(0)}%`}
            </span>
          </div>
        </div>
      </div>

      <div className="card" style={{ marginTop: 14 }}>
        <h3 className="sub-h">Signature — how far from the market average</h3>
        <p className="muted-note" style={{ marginTop: 0 }}>
          Standard deviations from the mean of the compared banks. Direction only: above is not better.
        </p>
        {bank.signature.map((s) => (
          <div className="sig-bar" key={s.label}>
            <span className="sig-bar-label">{s.label}</span>
            <div className="sig-bar-track">
              <span
                className={`sig-bar-fill ${s.direction}`}
                style={{ width: `${(Math.abs(s.sd) / signatureMax) * 50}%` }}
              />
            </div>
            <span className="sig-bar-value">{s.sd > 0 ? "+" : ""}{s.sd}</span>
          </div>
        ))}
      </div>

      <div className="profile-tables">
        <ProfileTable title="Tone" rows={bank.tone} />
        <ProfileTable title="Imagery" rows={bank.imagery} />
        <ProfileTable title="Layout" rows={bank.layout} />
        <ProfileTable title="Value proposition" rows={bank.valueProposition} />
        <ProfileTable title="Marketing principles" rows={bank.marketing} />
      </div>

      {bank.personas.length > 0 && (
        <div className="card" style={{ marginTop: 14 }}>
          <h3 className="sub-h">Personas targeted</h3>
          {bank.personas.map((p) => (
            <div className="bar-row" key={p.persona} style={{ gridTemplateColumns: "1fr 180px 46px" }}>
              <div className="bar-label">{p.label}</div>
              <div className="bar-track">
                <span className="bar-fill" style={{ left: 0, width: `${p.share * 100}%`, background: "var(--focus-ring)" }} />
              </div>
              <div className="bar-value">{(p.share * 100).toFixed(0)}%</div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

function ProfileTable({ title, rows }: { title: string; rows: Record<string, unknown> }) {
  const entries = Object.entries(rows);
  return (
    <div className="card">
      <h3 className="sub-h">{title}</h3>
      <KeyValue rows={entries} />
    </div>
  );
}

function KeyValue({ rows }: { rows: [string, unknown][] }) {
  if (rows.length === 0) return <div className="muted-note">No data.</div>;
  return (
    <table className="kv">
      <tbody>
        {rows.map(([k, v]) => (
          <tr key={k}>
            <th>{k}</th>
            <td>{format(v)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function Capture({ bankKey, name }: { bankKey: string; name: string }) {
  const [failed, setFailed] = useState(false);
  if (failed) {
    return <div className="muted-note">Capture not served — start <code>python3 scripts/serve_web.py</code>.</div>;
  }
  return (
    <img
      className="capture"
      src={`/api/capture/${encodeURIComponent(bankKey)}`}
      alt={`${name} page capture`}
      onError={() => setFailed(true)}
    />
  );
}

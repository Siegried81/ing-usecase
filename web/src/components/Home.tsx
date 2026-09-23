import { useEffect, useState } from "react";
import type { Deliverable, Operations, Report } from "../types";
import { downloadUrl, fetchDownloads } from "../api";

/**
 * The landing view Streamlit opened on: what was collected, which banks are in
 * the comparison, and the deliverables this run produced.
 *
 * The four metrics and the per-bank status come from operations.json (written
 * by the exporter), never recounted here. The download list is the one live
 * call, because those files live in outputs/ and are not part of the bundle.
 */
export function Home({ report, operations }: { report: Report; operations: Operations }) {
  const metrics = operations.collection.metrics;
  const scope = report.scope;

  const statusOf = (bank: Operations["collection"]["banks"][number]) =>
    bank.in_scope
      ? { text: "In scope", cls: "in" }
      : bank.excluded_no_page
        ? { text: "Out of scope — no page in this product family", cls: "out" }
        : { text: "Captured, currently out of scope", cls: "warn" };

  return (
    <>
      <div className="metrics">
        <Metric k="Banks with captures" v={metrics.banks} />
        <Metric k="Pages collected" v={metrics.pages} />
        <Metric k="Features in the dictionary" v={operations.dictionary.length} />
        <Metric k="Banks in scope" v={scope.banks.length} />
      </div>

      <div className="card" style={{ marginTop: 16 }}>
        <div className="status-line">
          <span className={`status-dot ${report.validation.ok ? "in" : "warn"}`} />
          <strong>{report.validation.ok ? "Dataset validation passed" : "Dataset validation reported warnings"}</strong>
        </div>
        <p style={{ color: "var(--ink-2)", margin: "8px 0 0", fontSize: 14.5 }}>
          Snapshot of {report.scope.product_family_label.toLowerCase()} across {scope.banks.length} banks, captured{" "}
          {scope.captured_from ? new Date(scope.captured_from).toLocaleDateString("en-GB") : "—"}. This is a
          proof of concept, not a production study: nothing here links a design choice to a click or a sale.
        </p>
        {report.validation.warnings.length > 0 && (
          <ul className="note-list">
            {report.validation.warnings.map((w, i) => <li key={i}>{w}</li>)}
          </ul>
        )}
      </div>

      <h3 className="sub-h" style={{ marginTop: 28 }}>Banks — collection status</h3>
      <div className="card">
        {operations.collection.banks.map((bank) => {
          const status = statusOf(bank);
          return (
            <div className="status-row" key={bank.bank}>
              <span className="status-name">{bank.name}</span>
              <span className="status-cat">{bank.category ?? "—"}</span>
              <span style={{ color: "var(--ink-3)", fontSize: 13 }}>
                {bank.pages} page{bank.pages === 1 ? "" : "s"}
              </span>
              <span className={`status-tag ${status.cls}`}>{status.text}</span>
            </div>
          );
        })}
        {scope.excluded.length > 0 && (
          <div className="scope-note" style={{ marginTop: 12 }}>
            <strong>Usable captures, no page in the compared family:</strong>{" "}
            {scope.excluded.map((e) => e.bank).join(", ")} — {scope.excluded[0].reason}.
            Comparing across product families would confound every difference.
          </div>
        )}
        {scope.uncollectable.length > 0 && (
          <div className="scope-note" style={{ marginTop: 8 }}>
            <strong>Could not be captured:</strong> {scope.uncollectable.map((u) => u.bank).join(", ")}.
          </div>
        )}
      </div>

      <h3 className="sub-h" style={{ marginTop: 28 }}>Available deliverables</h3>
      <Deliverables />
    </>
  );
}

function Metric({ k, v }: { k: string; v: number | string }) {
  return (
    <div className="metric">
      <div className="metric-v">{v}</div>
      <div className="metric-k">{k}</div>
    </div>
  );
}

function Deliverables() {
  const [files, setFiles] = useState<Deliverable[] | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    fetchDownloads()
      .then((r) => setFiles(r.files))
      .catch(() => setFailed(true));
  }, []);

  if (failed) {
    return (
      <div className="card">
        <p style={{ margin: 0, color: "var(--ink-2)" }}>
          The file list is served by the backend. Start it with{" "}
          <code>python3 scripts/serve_web.py</code>, then reload.
        </p>
      </div>
    );
  }
  if (!files) return <div className="muted-note">Loading deliverables…</div>;
  if (files.length === 0) return <div className="muted-note">No deliverables in outputs/ yet.</div>;

  return (
    <div className="downloads">
      {files.map((f) => (
        <a className="download" key={f.name} href={downloadUrl(f.name)} download>
          <span className={`dl-kind ${f.kind}`}>{f.kind}</span>
          <span className="dl-name">{f.name}</span>
          <span className="dl-size">{formatBytes(f.bytes)}</span>
        </a>
      ))}
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

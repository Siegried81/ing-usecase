import type { Operations } from "../types";
import { DataTable } from "./Table";
import { Section } from "./Section";

/**
 * Collection status, carried over from the Streamlit dashboard.
 *
 * Read-only on purpose. Collection is slow (~5-8s a page) and needs a job
 * model; more importantly the robots.txt gate must stay server-side and
 * non-overridable, so there is deliberately no "run collection" button here.
 */
export function Collection({ operations }: { operations: Operations }) {
  const { metrics, pages, commands, robots_note } = operations.collection;
  const columns = pages.length > 0 ? Object.keys(pages[0]) : [];

  const tiles: [string, string | number][] = [
    ["Banks", metrics.banks],
    ["Pages", metrics.pages],
    ["Robots allowed", metrics.robots_allowed ?? "N/A"],
    ["Quality ok", metrics.quality_ok ?? "N/A"],
    ["Manual captures", metrics.manual_captures ?? "N/A"],
    ["Languages", metrics.languages.map((l) => l.toUpperCase()).join(", ") || "—"],
  ];

  return (
    <>
      <Section
        title="Collection status"
        lede="Counts straight from the exported dataset. Nothing was fetched to render this page."
      >
        <div className="metrics">
          {tiles.map(([k, v]) => (
            <div className="metric" key={k}>
              <div className="metric-v">{v}</div>
              <div className="metric-k">{k}</div>
            </div>
          ))}
        </div>
      </Section>

      <Section
        title="Status per bank"
        lede="In scope means a usable page in the compared product family. A capture outside that family is kept, but not compared."
      >
        <div className="card">
          {operations.collection.banks.map((bank) => {
            const status = bank.in_scope
              ? { text: "In scope", cls: "in" }
              : bank.excluded_no_page
                ? { text: "No page in family", cls: "out" }
                : { text: "Captured, out of scope", cls: "warn" };
            return (
              <div className="status-row" key={bank.bank}>
                <span className="status-name">{bank.name}</span>
                <span className="status-cat">{bank.category ?? "—"}</span>
                <span style={{ color: "var(--ink-3)", fontSize: 13 }}>
                  {bank.usable_pages}/{bank.pages} usable
                </span>
                <span className={`status-tag ${status.cls}`}>{status.text}</span>
              </div>
            );
          })}
        </div>
      </Section>

      <Section title="Detailed pages" lede="Provenance per capture: how it was collected, at what quality, and from which source.">
        <DataTable columns={columns} rows={pages} maxHeight={420} minWidth={760} empty="No pages in the dataset." />
      </Section>

      <Section title="Collection pipeline" lede="The commands that produced this dataset. The UI does not run them.">
        <div className="card">
          <ul className="command-list">
            {commands.map((c) => <li key={c}><code>{c}</code></li>)}
          </ul>
          <div className="scope-note" style={{ marginTop: 12 }}>{robots_note}</div>
        </div>
      </Section>
    </>
  );
}

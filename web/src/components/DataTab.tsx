import { useMemo, useState } from "react";
import type { Operations } from "../types";
import { DataTable, format } from "./Table";
import { Section } from "./Section";

/**
 * The dataset explorer and the feature dictionary.
 *
 * Both are read-only by design: the dictionary is the frozen contract (P-04)
 * and hand-editing an extracted feature would destroy the audit trail. The
 * filters only choose which stored rows to show; no value is recomputed.
 */
export function DataTab({ operations }: { operations: Operations }) {
  const [view, setView] = useState<"dataset" | "dictionary">("dataset");
  return (
    <>
      <div className="tabs" style={{ marginTop: 0 }}>
        <button className={`tab${view === "dataset" ? " active" : ""}`} onClick={() => setView("dataset")}>
          Dataset
        </button>
        <button className={`tab${view === "dictionary" ? " active" : ""}`} onClick={() => setView("dictionary")}>
          Feature dictionary
        </button>
      </div>
      {view === "dataset" ? <DatasetExplorer operations={operations} /> : <DictionaryView operations={operations} />}
    </>
  );
}

const CONTEXT_COLUMNS = [
  "page_id", "bank", "bank_category", "product_family", "language",
  "data_source", "collection_method", "capture_quality", "captured_at", "url",
];

function DatasetExplorer({ operations }: { operations: Operations }) {
  const { columns, rows } = operations.dataset_table;
  const [bank, setBank] = useState("all");
  const [family, setFamily] = useState("all");
  const [allColumns, setAllColumns] = useState(false);

  const bankOptions = useMemo(() => {
    const key = columns.includes("bank") ? "bank" : null;
    return key ? [...new Set(rows.map((r) => String(r[key])))].sort() : [];
  }, [columns, rows]);

  const familyOptions = useMemo(
    () => [...new Set(rows.map((r) => r["product_family"]).filter(Boolean).map(String))].sort(),
    [rows],
  );

  const filtered = rows.filter(
    (r) =>
      (bank === "all" || String(r["bank"]) === bank) &&
      (family === "all" || String(r["product_family"]) === family),
  );

  const visible = allColumns ? columns : columns.filter((c) => CONTEXT_COLUMNS.includes(c));

  return (
    <Section
      title={`campaigns — ${operations.dataset_table.page_count} pages × ${columns.length} columns`}
      lede="Each row is one captured campaign page. Regenerated from the raw captures; the exporter reads the library, not these CSVs."
    >
      <div className="filter-row">
        <label className="rec-lang">
          <span>Bank</span>
          <select value={bank} onChange={(e) => setBank(e.target.value)}>
            <option value="all">All banks</option>
            {bankOptions.map((b) => <option key={b} value={b}>{b}</option>)}
          </select>
        </label>
        <label className="rec-lang">
          <span>Product family</span>
          <select value={family} onChange={(e) => setFamily(e.target.value)}>
            <option value="all">All families</option>
            {familyOptions.map((f) => <option key={f} value={f}>{f}</option>)}
          </select>
        </label>
        <label className="rec-check" style={{ marginLeft: "auto" }}>
          <input type="checkbox" checked={allColumns} onChange={(e) => setAllColumns(e.target.checked)} />
          Show all {columns.length} columns
        </label>
      </div>

      <div className="muted-note" style={{ margin: "8px 0" }}>
        Showing {filtered.length} of {rows.length} pages.
      </div>

      <button
        className="btn-action"
        disabled={filtered.length === 0}
        onClick={() => downloadCsv("campaigns.csv", columns, filtered)}
      >
        Download filtered CSV
      </button>

      <div style={{ marginTop: 14 }}>
        <DataTable columns={visible} rows={filtered} maxHeight={460} minWidth={allColumns ? 2200 : 900} />
      </div>
    </Section>
  );
}

function DictionaryView({ operations }: { operations: Operations }) {
  const [query, setQuery] = useState("");
  const features = operations.dictionary;

  const mapped = features
    .filter((f) => {
      const q = query.trim().toLowerCase();
      if (!q) return true;
      return [f.name, f.label, f.dimension, f.definition].some((v) => v.toLowerCase().includes(q));
    })
    .map((f) => ({
      Feature: f.name,
      Dimension: f.dimension,
      Type: f.type,
      Extraction: f.extraction,
      Comparability: f.comparability,
      Tier: f.tier,
      Required: f.required ? "Yes" : "No",
      Definition: f.definition,
    }));

  return (
    <Section
      title={`Feature dictionary — ${features.length} features`}
      lede="config/feature_dictionary.yaml is the single source of truth. Frozen after Day 2; editing it from a form would undo the freeze rule."
    >
      <input
        className="text-input"
        placeholder="Filter by name, dimension or definition…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <div style={{ marginTop: 12 }}>
        <DataTable
          columns={["Feature", "Dimension", "Type", "Extraction", "Comparability", "Tier", "Required", "Definition"]}
          rows={mapped}
          maxHeight={560}
          minWidth={980}
          empty="No feature matches that filter."
        />
      </div>
    </Section>
  );
}

function downloadCsv(name: string, columns: string[], rows: Record<string, unknown>[]) {
  const escape = (value: unknown) => {
    const s = format(value) === "—" ? "" : format(value);
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const text = [
    columns.join(","),
    ...rows.map((r) => columns.map((c) => escape(r[c])).join(",")),
  ].join("\n");
  const url = URL.createObjectURL(new Blob([text], { type: "text/csv;charset=utf-8" }));
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

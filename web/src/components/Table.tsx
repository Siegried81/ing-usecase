/**
 * A plain scrollable table for rows the Python side already flattened.
 *
 * The UI renders values verbatim: null becomes an em dash, a list is joined.
 * Nothing here sorts, filters or aggregates - that happens in the exporter, so
 * there is no second definition of a number on screen.
 */
export function DataTable<T extends object>({
  columns,
  rows,
  maxHeight,
  minWidth,
  empty = "No rows.",
  rowClass,
}: {
  columns: string[];
  rows: T[];
  maxHeight?: number;
  minWidth?: number;
  empty?: string;
  rowClass?: (row: T, index: number) => string | undefined;
}) {
  if (rows.length === 0) {
    return <div className="muted-note">{empty}</div>;
  }
  return (
    <div className="table-scroll" style={{ maxHeight }}>
      <table className="claims" style={{ minWidth }}>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c}>{c.replace(/_/g, " ")}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className={rowClass?.(row, i)}>
              {columns.map((c) => (
                <td key={c}>{format((row as Record<string, unknown>)[c])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function format(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "yes" : "no";
  if (Array.isArray(value)) return value.length ? value.join(", ") : "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

/**
 * The one section shell every tab uses: a heading, an optional one-line lede,
 * and the content. Kept out of App.tsx so the operator tabs can reach it too.
 */
export function Section({ title, lede, children }: { title: string; lede?: string; children: React.ReactNode }) {
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

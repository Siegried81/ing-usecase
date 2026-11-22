-- ING vs competitors Google Trends brand-notoriety schema.
-- trends_data is created by collectors/trends_collector.py; kept here too
-- for reference and so a fresh database can be built from this file alone.

CREATE TABLE IF NOT EXISTS trends_data (
    product_id TEXT NOT NULL,
    product_label TEXT NOT NULL,
    term TEXT NOT NULL,
    bank TEXT NOT NULL,
    language TEXT NOT NULL,
    date TEXT NOT NULL,
    value INTEGER NOT NULL,
    UNIQUE (product_id, term, date)
);

CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    product_label TEXT NOT NULL,
    term_count INTEGER NOT NULL
);

-- Term resolution audit trail for the new-bank extension (six-bank rollout):
-- one row per candidate term tested by collectors/term_resolver.py, for each
-- pytrends call it appeared in. Read by data/term_validation_report.md and
-- by the app/export flag lookups; never read by the collector itself, which
-- only ever reads the final terms written into config.PRODUCTS by hand.
--
-- scope: 'brand' (a single brand-name candidate, product_id is a synthetic
-- '__brand__{BANK}' id), 'product' (a candidate for one slot of one product
-- fiche), 'brand_fiche' or 'context_fiche' (a control call on a finished
-- brand/context fiche composition, no candidate selection involved).
CREATE TABLE IF NOT EXISTS term_validation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL CHECK (scope IN ('brand', 'product', 'brand_fiche', 'context_fiche')),
    product_id TEXT NOT NULL,
    bank TEXT NOT NULL,
    slot_language TEXT NOT NULL,
    candidate_rank INTEGER NOT NULL,
    term TEXT NOT NULL,
    term_kind TEXT NOT NULL CHECK (term_kind IN ('string', 'topic')),
    topic_title TEXT,
    topic_type TEXT,
    call_index INTEGER NOT NULL,
    nonzero_points INTEGER NOT NULL,
    total_points INTEGER NOT NULL,
    coverage REAL NOT NULL,
    mean_value REAL NOT NULL,
    verdict TEXT NOT NULL CHECK (verdict IN ('selected', 'selected_low_coverage', 'rejected', 'dropped', 'info_only')),
    flags TEXT,
    tested_at TEXT NOT NULL,
    UNIQUE (scope, product_id, bank, slot_language, term, call_index)
);

-- Share-of-search chaining (analysis/share_of_search.py): rescales every
-- generic-brand sheet onto one common 0-100 scale via their shared ING/KBC
-- anchor, then derives each bank's weekly share of the whole panel. Fully
-- derived from trends_data: wiped and recomputed on every run.
CREATE TABLE IF NOT EXISTS brand_share_of_search (
    bank TEXT NOT NULL,
    date TEXT NOT NULL,
    source_fiche TEXT NOT NULL,
    raw_value INTEGER NOT NULL,
    scale_factor REAL NOT NULL,
    rescaled_value REAL NOT NULL,
    share_pct REAL NOT NULL,
    UNIQUE (bank, date)
);

-- KBC vs ING Google Trends benchmark schema.
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

-- anomaly_type: 'isolated_spike' (a single flagged week) or
-- 'sustained_trend' (two or more consecutive flagged weeks). See
-- analysis/anomaly_detection.py for the exact detection logic.
CREATE TABLE IF NOT EXISTS anomalies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL,
    term TEXT NOT NULL,
    bank TEXT NOT NULL,
    date TEXT NOT NULL,
    value INTEGER NOT NULL,
    anomaly_type TEXT NOT NULL CHECK (anomaly_type IN ('isolated_spike', 'sustained_trend')),
    deviation_score REAL NOT NULL,
    UNIQUE (product_id, term, date)
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

-- Share-of-search chaining (analysis/share_of_search.py): rescales the 3
-- generic-brand sheets onto one common 0-100 scale via their shared ING/KBC
-- anchor, then derives each bank's weekly share of the 9-bank panel. Fully
-- derived from trends_data - wiped and recomputed on every run, same
-- refresh policy as `anomalies`.
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

-- Downstream pipeline (campaigns/): catalogs real ad/marketing campaigns and
-- matches them against anomalies already detected above. Populated by
-- campaigns/load_campaigns.py, consumed by campaigns/scoring.py.
--
-- start_date/end_date may be a partial date (YYYY, YYYY-MM, YYYY-Qn) when
-- that is the real precision of the source - see campaigns/date_utils.py,
-- which is the single place that interprets these strings into a match
-- window. Do not assume full YYYY-MM-DD precision when reading this column.
CREATE TABLE IF NOT EXISTS campaigns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bank TEXT NOT NULL CHECK (bank IN ('KBC', 'CBC', 'ING')),
    name TEXT NOT NULL,
    language TEXT NOT NULL CHECK (language IN ('FR', 'NL', 'FR+NL')),
    start_date TEXT NOT NULL,
    end_date TEXT,
    date_confidence TEXT NOT NULL CHECK (date_confidence IN ('exact', 'approximate', 'month_only')),
    agency TEXT,
    campaign_type TEXT NOT NULL CHECK (campaign_type IN ('brand', 'product', 'sponsoring', 'csr')),
    target_fiches TEXT,
    channels TEXT,
    source_url TEXT,
    notes TEXT,
    UNIQUE (bank, name, start_date)
);

-- One row per (campaign, anomaly) match found by the attribution window in
-- campaigns/scoring.py. contribution is this match's weighted, adjusted
-- share of the campaign's raw score (after seasonal-confound and
-- overlapping-campaign adjustments, before the breadth bonus).
CREATE TABLE IF NOT EXISTS campaign_anomaly_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_id INTEGER NOT NULL REFERENCES campaigns(id),
    anomaly_id INTEGER NOT NULL REFERENCES anomalies(id),
    delay_days INTEGER NOT NULL,
    possible_seasonal_confound INTEGER NOT NULL DEFAULT 0,
    overlapping_campaign_ids TEXT,
    contribution REAL NOT NULL,
    UNIQUE (campaign_id, anomaly_id)
);

-- One row per campaign: final score and the audit detail behind it.
-- status='not_scorable' campaigns keep a reason instead of a score, rather
-- than being silently scored 0 or dropped from the comparison.
CREATE TABLE IF NOT EXISTS campaign_scores (
    campaign_id INTEGER PRIMARY KEY REFERENCES campaigns(id),
    status TEXT NOT NULL CHECK (status IN ('scorable', 'not_scorable')),
    not_scorable_reason TEXT,
    anomaly_count INTEGER,
    fiches_touched INTEGER,
    seasonal_confound_count INTEGER,
    raw_score REAL,
    breadth_multiplier REAL,
    final_score REAL
);

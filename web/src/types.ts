/** Mirrors scripts/export_web_report.py. If you change one, change the other. */

export type Category = "traditional" | "challenger";

export interface Scope {
  product_family: string | null;
  product_family_label: string;
  pages: number;
  banks: string[];
  traditional: string[];
  challenger: string[];
  excluded: { bank: string; reason: string }[];
  uncollectable: { bank: string; reason: string }[];
  languages: string[];
  captured_from: string | null;
  captured_to: string | null;
  total_collected: number;
  n_features: number;
}

export interface PositionedBank {
  bank: string;
  key: string;
  category: Category;
  score: number;
  isFocus: boolean;
}

export interface PeerGap {
  feature: string;
  label: string;
  dimension: string;
  extraction: string;
  focusValue: number | null;
  peerMean: number | null;
  gapSd: number;
  direction: "above" | "below";
}

export interface Separation {
  feature: string;
  label: string;
  extraction: string;
  traditional: number | null;
  challenger: number | null;
  effect: number;
  higherAt: Category;
}

/** sieg 19/09: one target_personas value, aggregated to a share of this bank's pages. */
export interface Persona {
  persona: string;
  label: string;
  share: number;
}

/** sieg 19/09: comparator/ai_score.py axis key -> score (0-10), null when the bank has no data for it. */
export type AiScore = Record<string, number | null>;

/** sieg 19/09: radar legend entry, mirrors comparator/ai_score.py's AXES. */
export interface AiScoreAxis {
  key: string;
  label: string;
}

export interface BankProfile {
  key: string;
  name: string;
  category: Category;
  pages: number;
  signature: { label: string; sd: number; direction: "above" | "below" }[];
  tone: Record<string, unknown>;
  imagery: Record<string, unknown>;
  layout: Record<string, unknown>;
  valueProposition: Record<string, unknown>;
  palette: { dominant: string | null; brandShare: number | null; backgroundLuminance: number | null };
  marketing: Record<string, unknown>;
  personas: Persona[];
  aiScore: AiScore;
  /** sieg 19/09: comparator/cross_sell.py's score_bank() - share of possible other products cross-sold, 0-1. */
  crossSellScore: number | null;
}

/** sieg 19/09: comparator/cross_sell.py's cross_sell_matrix(), flattened for the UI. */
export interface CrossSellMatrix {
  products: string[];
  matrix: number[][];
  mostAssociated: { from: string; to: string; count: number }[];
  /** confirmed: enough pages to trust the zero. insufficient_data: too few pages to say. */
  neverPaired: {
    confirmed: { from: string; to: string }[];
    insufficient_data: { from: string; to: string }[];
  };
}

export interface GeneratedCampaign {
  variant: string;
  title: string;
  headline: string;
  subheading: string;
  body: string[];
  cta: string;
  additionalCtas: string[];
  layout: string;
  background: string;
  accent: string;
  imageBriefs: string[];
  disclaimer: string;
  levers: string[];
  model: string | null;
  promptHash: string | null;
  scorecard: { label: string; target: string; actual: unknown; result: string }[];
  hitRate: number | null;
}

export type Priority = "high" | "medium" | "low";

/** Analysis recommendations come from the measured pages; trends and
 *  reputation ones are added on top from context (search interest / news
 *  themes) and never cite page features. sieg 21/09: added "reputation". */
export type RecommendationBasis = "analysis" | "trends" | "reputation";

export interface Recommendation {
  id: string;
  title: string;
  priority: Priority;
  finding: string;
  recommendation: string;
  features: string[];
  page_targets: string[];
  basis?: RecommendationBasis;
  market_context?: string | null;
  reputation_context?: string | null;
}

export interface RecommendationPayload {
  available: boolean;
  generated_at?: string;
  model?: string;
  summary: string | null;
  recommendations: Recommendation[];
  used_trends?: boolean;
  used_reputation?: boolean;
}

export interface SitePage {
  slug: string;
  nav: string;
  title: string;
  file: string;
  used_fallback: boolean;
  recommendations_implemented: string[];
}

export interface SiteManifest {
  language: string;
  locale: string;
  generated_at: string | null;
  model: string;
  /** True when the pages were rendered with the per-section explanation boxes. */
  explained?: boolean;
  pages: SitePage[];
  recommendations: { id: string; title: string; priority: Priority }[];
  asset_warnings: string[];
}

export interface SiteStatus {
  status: "idle" | "generating" | "ready" | "error";
  progress: number;
  total: number;
  page: string | null;
  error: string | null;
  ready: boolean;
  manifest: SiteManifest | null;
  site_url: string | null;
}

/** Pointer to the Trends tab payload. The series themselves live in trends.json. */
export interface TrendsSummary {
  available: boolean;
  source: string;
  window: { start: string | null; end: string | null };
  covered: string[];
  uncovered: string[];
  n_series: number;
  data_url: string;
}

/** [YYYY-MM-DD, value] - one weekly Google Trends point. */
export type TrendPoint = [string, number];

export interface TrendTerm {
  term: string;
  label: string;
  language: string;
  points: TrendPoint[];
}

export interface TrendProduct {
  id: string;
  label: string;
  terms: TrendTerm[];
}

export interface TrendBank {
  key: string;
  name: string;
  segment: Category;
  products: TrendProduct[];
}

export interface TrendEvent {
  bank: string;
  key: string;
  date: string;
  label: string;
}





/** One bank's standing in the nine-bank brand-search panel.
 * `lowConfidence` means the raw 0-100 series never cleared the measurable
 * floor because it shared a Google Trends request with a term peaking at 100 -
 * the share is quantisation as much as measurement. Never hide such a row;
 * label it. */
export interface ShareOfSearchRow {
  rank: number;
  bank: string;
  key: string;
  segment: string;
  sharePct: number;
  rawPeak: number;
  lowConfidence: boolean;
  sourceSheet: string;
}

/** A claim the payload could not compute: the only non-derived facts the
 * Trends tab may show. Source and dates are rendered next to every one. */
export interface TrendExternalReference {
  id: string;
  claim: string;
  value: string | null;
  source: string;
  url: string;
  published: string;
  retrieved: string;
  appliesToBank: string | null;
}

export interface ShareSegmentGroup {
  id: string;
  label: string;
  sharePct: number;
  count: number;
  members: { bank: string; key: string; sharePct: number }[];
}

/** One bank's sentence, pre-computed. `tieWith` non-empty means the ranking
 * cannot order this bank against those - render them level, never in order. */
export interface ShareBankReading {
  rank: number;
  bank: string;
  key: string;
  sharePct: number;
  gapToAbovePts: number | null;
  bankAbove: string | null;
  tieWith: string[];
  tieSpreadPts: number | null;
  segment: string;
  segmentLabel: string;
  pctOfSegment: number | null;
  lowConfidence: boolean;
}

export interface ShareChallengerFocus {
  bank: string;
  key: string;
  rank: number;
  sharePct: number;
  pctOfChallengerAttention: number | null;
  incumbentsAbove: number;
  lowConfidenceBanks: string[];
  reference: TrendExternalReference | null;
}

/** Reading of the ranking: market structure, concentration, per-bank lines.
 * Every figure is computed in comparator/trends.py so no sentence in the
 * component carries a literal that a later collection run would falsify. */
export interface ShareInsights {
  window: {
    firstDate: string | null;
    lastDate: string | null;
    weeks: number;
    banks: number;
    fiches: number;
  };
  segments: {
    groups: ShareSegmentGroup[];
    bigFourAreTopFour: boolean;
    topFour: { bank: string; key: string; rank: number; sharePct: number }[];
  };
  concentration: { hhi: number; equivalentBrands: number | null };
  ties: { thresholdPts: number; groups: string[][] };
  banks: ShareBankReading[];
  challengerFocus: ShareChallengerFocus | null;
  measurablePeakFloor: number;
  references: TrendExternalReference[];
}

/** Share of search across more banks than one Trends request can hold.
 * Every figure here is computed in comparator/trends.py - the UI does no
 * arithmetic, so there is no second definition of any number on screen. */
export interface ShareOfSearch {
  ranking: ShareOfSearchRow[];
  series: { bank: string; key: string; points: TrendPoint[] }[];
  window: { start: string | null; end: string | null };
  weeks: number;
  headline: {
    sentence: string;
    leader: string;
    leaderShare: number;
    focusRank: number | null;
    focusShare: number | null;
    traditionalShare: number;
    challengerShare: number;
    segmentSentence: string;
  };
  method: {
    why: string;
    referenceSheet: string;
    anchors: string[];
    scaleFactors: Record<string, number>;
    aggregation: string;
  };
  lowConfidence: string[];
  insights: ShareInsights;
  caveat: string;
}

/** One year of weekly points, anchored on the last week and counted back. */
export interface TrendPeriod {
  index: number;
  label: string;
  start: string;
  end: string;
}

/** Level change plus momentum. `robust` is false when the direction only
 *  holds with the first period, which straddles Google's 2022 method change. */
export interface TrendTrajectory {
  periodShares: number[];
  meanSharePct: number;
  deltaPts: number;
  slopePtsPerYear: number | null;
  relativeSlopePctPerYear: number | null;
  relativeSlopeExFirstPeriod: number | null;
  direction: "up" | "flat" | "down" | null;
  robust: boolean;
}

export interface TrendSegmentTrajectory extends TrendTrajectory {
  id: string;
  label: string;
}

/** A flagged bank carries no per-period figure at all, so no view can render
 *  one by accident - only its aggregated share and the flag. */
export interface TrendBankTrajectory {
  bank: string;
  key: string;
  aggregatedSharePct: number;
  lowConfidence: boolean;
  periodShares: number[] | null;
  deltaPts: number | null;
  relativeSlopePctPerYear: number | null;
  direction: "up" | "flat" | "down" | null;
  robust: boolean | null;
}

export interface TrendRankStability {
  banks: { bank: string; ranks: number[]; bestRank: number; worstRank: number; changes: number }[];
  overtakes: { bank: string; passed: string }[];
  pairsKept: number;
  pairsTotal: number;
}

export interface TrendBenchmark {
  bank: string;
  roles: string[];
  lastSharePct: number;
  deltaPts: number;
  relativeSlopePctPerYear: number | null;
  direction: "up" | "flat" | "down" | null;
  robust: boolean;
  gapToSubjectPts: number;
  onlyMeasurable?: boolean;
}

export interface TrendBenchmarkScope {
  subject: string;
  traditionalCandidates: number;
  challengerCandidates: number;
  benchmarks: TrendBenchmark[];
  challenger: TrendBenchmark | null;
  excludedChallengers: string[];
  subjectContext: {
    bank: string;
    lastSharePct: number;
    deltaPts: number;
    relativeSlopePctPerYear: number | null;
    direction: "up" | "flat" | "down" | null;
    robust: boolean;
  };
}

/** How attention moved. Every figure is computed in comparator/trends.py. */
export interface TrendsTrajectoryPayload {
  periods: TrendPeriod[];
  droppedWeeks: number;
  weeksPerPeriod: number;
  flatBandPct: number;
  methodChangeDate: string;
  segments: TrendSegmentTrajectory[];
  banks: TrendBankTrajectory[];
  /** Always a measurable incumbent, so deltaPts is set whenever present. */
  biggestRise: (TrendBankTrajectory & { deltaPts: number }) | null;
  biggestFall: (TrendBankTrajectory & { deltaPts: number }) | null;
  rankStability: TrendRankStability;
  benchmark: TrendBenchmarkScope;
  lowConfidenceBanks: string[];
}

export interface TrendsPayload {
  available: boolean;
  trajectory: TrendsTrajectoryPayload | null;
  source: string;
  window: { start: string | null; end: string | null };
  coverage: { covered: string[]; uncovered: string[] };
  shareOfSearch: ShareOfSearch | null;
  banks: TrendBank[];
  events: TrendEvent[];
  guardrail: string;
}

/** sieg 21/09: a notable headline, with its source URL when one was found. */
export interface ReputationHeadline {
  title: string;
  url: string | null;
}

/** sieg 19/09: comparator/reputation.py - themes only, never sentiment. */
export interface BankReputation {
  headline_count: number;
  themes: Record<string, number>;
  /** sieg 21/09: every headline behind a theme's count, for the hover popup. */
  theme_headlines: Record<string, ReputationHeadline[]>;
  notable_headlines: ReputationHeadline[];
}

export interface ReputationPayload {
  available: boolean;
  banks: Record<string, BankReputation | null>;
}

/** sieg 20/09: comparator/geo_trends.py - Google Trends by Belgian region, a
 * standalone module (own pytrends calls), not part of the Trends tab's bridge
 * to Dan's exports. regions: e.g. {"Bruxelles": 100, "Région Flamande": 74}. */
export interface GeoTrendsBank {
  name: string;
  regions: Record<string, number>;
}

export interface GeoTrendsPayload {
  available: boolean;
  banks: Record<string, GeoTrendsBank>;
}

/** One row of config/feature_dictionary.yaml as the Data tab shows it. */
export interface DictionaryFeature {
  name: string;
  label: string;
  dimension: string;
  type: string;
  extraction: string;
  comparability: string;
  tier: string;
  required: boolean;
  nullable: boolean;
  definition: string;
  values: string[] | null;
  range: [number, number] | null;
  unit: string | null;
}

/** The collected dataset, flattened. `rows` are the raw page captures. */
export interface DatasetTable {
  columns: string[];
  rows: Record<string, unknown>[];
  page_count: number;
  bank_count: number;
}

export interface CollectionBankStatus {
  bank: string;
  name: string;
  category: string | null;
  pages: number;
  usable_pages: number;
  in_scope: boolean;
  excluded_no_page: boolean;
}

export interface CollectionPayload {
  metrics: {
    banks: number;
    pages: number;
    robots_allowed: number | null;
    quality_ok: number | null;
    manual_captures: number | null;
    languages: string[];
  };
  banks: CollectionBankStatus[];
  pages: Record<string, unknown>[];
  commands: string[];
  robots_note: string;
}

export interface RubricRater {
  name: string;
  label: string;
  pages: number;
  columns: string[];
  rows: Record<string, unknown>[];
}

export interface RubricFeature {
  name: string;
  label: string;
  definition: string;
  values: string[] | null;
  range: [number, number] | null;
  rubric: Record<string, string> | null;
  notes: string | null;
}

/** One row of comparator.rubric.agreement() - raw % match, chance not removed. */
export interface AgreementRow {
  feature: string;
  pages: number;
  agreement: number;
  basis: string;
}

/** One row of comparator.rubric.kappa_agreement() - chance-corrected. */
export interface KappaRow {
  feature: string;
  raters: string;
  pages: number;
  kappa: number;
}

export interface RubricPayload {
  raters: RubricRater[];
  agreement: AgreementRow[];
  kappa: KappaRow[];
  features: RubricFeature[];
}

/** Mirrors scripts/export_web_report.py's build_operations() output. */
export interface Operations {
  generated_at: string;
  dataset: string;
  product_family: string | null;
  validation: { ok: boolean; warnings: string[] };
  dictionary: DictionaryFeature[];
  dataset_table: DatasetTable;
  collection: CollectionPayload;
  rubric: RubricPayload;
}

/** comparator/research.py - title, abstract, url, year. */
export interface ResearchPaper {
  title: string | null;
  abstract: string | null;
  url: string | null;
  year: number | null;
}

/** One file in outputs/ offered for download by the backend. */
export interface Deliverable {
  name: string;
  kind: string;
  bytes: number;
}

export interface Report {
  generated_at: string;
  dataset: string;
  scope: Scope;
  headline: { focus: string; score: number | null; verdict: string | null; has_focus: boolean };
  positioning: PositionedBank[];
  peerGaps: PeerGap[];
  excludedGaps: { label: string; note: string }[];
  separation: Separation[];
  banks: BankProfile[];
  aiScoreAxes: AiScoreAxis[];
  crossSellMatrix: CrossSellMatrix;
  similarity: { banks: string[]; matrix: number[][] };
  clusters: { cluster: number; banks: string[] }[];
  nearestToFocus: { bank: string; distance: number }[];
  deckClaims: { id: string; bank: string; claim: string; verdict: string; evidence: string }[];
  limitations: { blocking: string[]; material: string[]; standing: string[] };
  validation: { ok: boolean; warnings: string[] };
  generated: GeneratedCampaign[];
  trends: TrendsSummary | null;
  reputation: ReputationPayload;
  geoTrends: GeoTrendsPayload;
}

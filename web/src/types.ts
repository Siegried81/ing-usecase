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

/** Analysis recommendations come from the measured pages; trends ones are
 *  added on top from search-interest context and never cite page features. */
export type RecommendationBasis = "analysis" | "trends";

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
}

export interface RecommendationPayload {
  available: boolean;
  generated_at?: string;
  model?: string;
  summary: string | null;
  recommendations: Recommendation[];
  used_trends?: boolean;
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
  n_anomalies: number;
  n_campaigns: number;
  data_url: string;
}

/** [YYYY-MM-DD, value] - one weekly Google Trends point. */
export type TrendPoint = [string, number];

export interface TrendAnomaly {
  date: string;
  value: number;
  type: "isolated_spike" | "sustained_trend";
  label: string;
  score: number;
}

export interface TrendTerm {
  term: string;
  label: string;
  language: string;
  points: TrendPoint[];
  anomalies: TrendAnomaly[];
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

export interface CampaignScore {
  id: number;
  bank: string;
  key: string;
  name: string;
  language: string;
  startDate: string | null;
  endDate: string | null;
  confidence: string;
  type: string;
  targetFiches: string[];
  status: string;
  reason: string | null;
  anomalyCount: number;
  fichesTouched: number;
  seasonalConfounds: number;
  rawScore: number;
  finalScore: number;
}

export interface CampaignMatch {
  campaignId: number;
  campaignName: string;
  campaignBank: string;
  productId: string;
  term: string;
  date: string;
  type: string;
  label: string;
  score: number | null;
  delayDays: number | null;
  seasonalConfound: boolean;
  contribution: number | null;
}

export interface CampaignSummary {
  bank: string;
  catalogued: number;
  scorable: number;
  totalScore: number;
  averageScore: number;
  successRate: number;
}

export interface CampaignTypeMix {
  bank: string;
  brand: number;
  product: number;
  sponsoring: number;
  csr: number;
  other: number;
}

export interface TrendsPayload {
  available: boolean;
  source: string;
  window: { start: string | null; end: string | null };
  coverage: { covered: string[]; uncovered: string[] };
  banks: TrendBank[];
  events: TrendEvent[];
  campaigns: {
    catalogued: number;
    scorable: number;
    scorecards: CampaignScore[];
    matches: CampaignMatch[];
    summary: CampaignSummary[];
    byType: CampaignTypeMix[];
  };
  guardrail: string;
}

/** sieg 19/09: comparator/reputation.py - themes only, never sentiment. */
export interface BankReputation {
  headline_count: number;
  themes: Record<string, number>;
  notable_headlines: string[];
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

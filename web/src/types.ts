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

export interface Recommendation {
  id: string;
  title: string;
  priority: Priority;
  finding: string;
  recommendation: string;
  features: string[];
  page_targets: string[];
}

export interface RecommendationPayload {
  available: boolean;
  generated_at?: string;
  model?: string;
  summary: string | null;
  recommendations: Recommendation[];
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
  similarity: { banks: string[]; matrix: number[][] };
  clusters: { cluster: number; banks: string[] }[];
  nearestToFocus: { bank: string; distance: number }[];
  deckClaims: { id: string; bank: string; claim: string; verdict: string; evidence: string }[];
  limitations: { blocking: string[]; material: string[]; standing: string[] };
  validation: { ok: boolean; warnings: string[] };
  generated: GeneratedCampaign[];
  trends: {
    rows: { bank: string; family: string; recent: number | null; baseline: number | null;
            changePct: number | null; direction: string }[];
    uncovered: string[];
  } | null;
}

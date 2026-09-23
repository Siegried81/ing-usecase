import type { Deliverable, Operations, RecommendationPayload, ResearchPaper, SiteStatus } from "./types";

/**
 * Thin client for the recommendation / site backend.
 *
 * In dev, Vite proxies /api and /site to the FastAPI server (see
 * vite.config.ts). A built bundle served by that same server needs no proxy at
 * all, so relative paths are correct in both shapes.
 */

async function json<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let detail = `${response.status}`;
    try {
      const body = await response.json();
      if (body?.detail) detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* keep the status code */
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export async function fetchRecommendations(): Promise<RecommendationPayload> {
  return json<RecommendationPayload>(await fetch("/api/recommendations"));
}

export async function generateRecommendations(
  includeReputation = false,
): Promise<RecommendationPayload> {
  return json<RecommendationPayload>(
    await fetch("/api/recommendations/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ include_reputation: includeReputation }),
    }),
  );
}

export async function generateSite(
  recommendationIds: string[],
  language: string,
  explain = false,
): Promise<{ status: string; total: number }> {
  return json(
    await fetch("/api/site/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recommendation_ids: recommendationIds, language, explain }),
    }),
  );
}

export async function fetchSiteStatus(): Promise<SiteStatus> {
  return json<SiteStatus>(await fetch("/api/site/status"));
}

/**
 * The operator snapshot (dictionary, dataset, collection, rubric). Written by
 * `scripts/export_web_report.py` next to report.json, so the Analysis tab and
 * these views come from one run. Missing means the exporter has not been run.
 */
export async function fetchOperations(): Promise<Operations> {
  const response = await fetch(`${import.meta.env.BASE_URL}operations.json`);
  if (!response.ok) throw new Error(`${response.status}`);
  return response.json() as Promise<Operations>;
}

/** Semantic Scholar search - server-side, because it is a live external call. */
export async function searchResearch(
  query: string,
  limit: number,
): Promise<{ papers: ResearchPaper[]; available: boolean }> {
  const params = new URLSearchParams({ q: query, limit: String(limit) });
  return json(await fetch(`/api/research/search?${params}`));
}

/** Files in outputs/ the backend is willing to serve. */
export async function fetchDownloads(): Promise<{ available: boolean; files: Deliverable[] }> {
  return json(await fetch("/api/downloads"));
}

export function downloadUrl(name: string): string {
  return `/api/downloads/${encodeURIComponent(name)}`;
}

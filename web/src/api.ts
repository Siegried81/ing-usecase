import type { RecommendationPayload, SiteStatus } from "./types";

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
  includeTrends = false,
): Promise<RecommendationPayload> {
  return json<RecommendationPayload>(
    await fetch("/api/recommendations/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ include_trends: includeTrends }),
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

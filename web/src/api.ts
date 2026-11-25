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

const TOKEN_KEY = "ing-api-token";

/**
 * POST to a route that spends LLM credit.
 *
 * The server only checks X-API-Token when API_TOKEN is set on its side, so in
 * local development no token exists and nothing is asked. On a 401 the user is
 * asked once; the answer is kept in sessionStorage (gone when the tab closes)
 * and the call is retried a single time. A wrong token is dropped so the next
 * click asks again instead of failing forever.
 */
async function postWithToken(url: string, body: unknown): Promise<Response> {
  const send = (token: string | null) =>
    fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { "X-API-Token": token } : {}),
      },
      body: JSON.stringify(body),
    });

  let response = await send(sessionStorage.getItem(TOKEN_KEY));
  if (response.status !== 401) return response;

  const entered = window.prompt("This server needs an access token to call the model.");
  if (!entered) return response;
  response = await send(entered);
  if (response.ok) sessionStorage.setItem(TOKEN_KEY, entered);
  else if (response.status === 401) sessionStorage.removeItem(TOKEN_KEY);
  return response;
}

export async function fetchRecommendations(): Promise<RecommendationPayload> {
  return json<RecommendationPayload>(await fetch("/api/recommendations"));
}

export async function generateRecommendations(
  includeReputation = false,
): Promise<RecommendationPayload> {
  return json<RecommendationPayload>(
    await postWithToken("/api/recommendations/generate", { include_reputation: includeReputation }),
  );
}

export async function generateSite(
  recommendationIds: string[],
  language: string,
  explain = false,
): Promise<{ status: string; total: number }> {
  return json(
    await postWithToken("/api/site/generate", {
      recommendation_ids: recommendationIds,
      language,
      explain,
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

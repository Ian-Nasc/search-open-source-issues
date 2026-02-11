import type { Company, Issue, PaginatedResponse, Stats } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_V1 = `${API_BASE}/api/v1`;

async function fetchAPI<T>(
  path: string,
  params?: Record<string, unknown>
): Promise<T> {
  const url = new URL(`${API_V1}${path}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          value.forEach((v) => url.searchParams.append(key, String(v)));
        } else {
          url.searchParams.set(key, String(value));
        }
      }
    });
  }
  const res = await fetch(url.toString());
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export const api = {
  issues: {
    list: (params: Record<string, unknown>) =>
      fetchAPI<PaginatedResponse<Issue>>("/issues/", params),
    get: (id: number) => fetchAPI<Issue>(`/issues/${id}`),
  },
  companies: {
    list: () => fetchAPI<Company[]>("/companies/"),
  },
  search: {
    query: (params: Record<string, unknown>) =>
      fetchAPI<PaginatedResponse<Issue>>("/search/", params),
  },
  stats: {
    get: () => fetchAPI<Stats>("/stats/"),
  },
};

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import type { IssueFilters } from "@/lib/types";

export function useIssues(
  filters: IssueFilters & { page: number; page_size: number }
) {
  return useQuery({
    queryKey: ["issues", filters],
    queryFn: () =>
      api.issues.list(filters as unknown as Record<string, unknown>),
    placeholderData: keepPreviousData,
    staleTime: 5 * 60 * 1000,
  });
}

export function useSearchIssues(
  query: string,
  filters: Partial<IssueFilters> & { page: number; page_size: number }
) {
  return useQuery({
    queryKey: ["search", query, filters],
    queryFn: () =>
      api.search.query({
        q: query,
        ...filters,
      } as unknown as Record<string, unknown>),
    enabled: query.length >= 2,
    placeholderData: keepPreviousData,
    staleTime: 2 * 60 * 1000,
  });
}

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export function useCompanies() {
  return useQuery({
    queryKey: ["companies"],
    queryFn: () => api.companies.list(),
    staleTime: 10 * 60 * 1000,
  });
}

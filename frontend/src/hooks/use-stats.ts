import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";

export function useStats() {
  return useQuery({
    queryKey: ["stats"],
    queryFn: () => api.stats.get(),
    staleTime: 10 * 60 * 1000,
  });
}

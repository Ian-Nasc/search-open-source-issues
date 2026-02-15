"use client";

import { useState, useEffect, useRef } from "react";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { IssueFiltersPanel } from "@/components/issues/issue-filters";
import { IssueList } from "@/components/issues/issue-list";
import { SearchBar } from "@/components/search/search-bar";
import { StatsBar } from "@/components/stats/stats-bar";
import { Pagination } from "@/components/common/pagination";
import { useDebounce } from "@/hooks/use-debounce";
import { useIssues, useSearchIssues } from "@/hooks/use-issues";
import { useStats } from "@/hooks/use-stats";
import { useCompanies } from "@/hooks/use-companies";
import { trackEvent } from "@/lib/posthog";
import type { IssueFilters } from "@/lib/types";

export function IssuesBrowser() {
  const [searchQuery, setSearchQuery] = useState("");
  const [filters, setFilters] = useState<IssueFilters>({});
  const [page, setPage] = useState(1);
  const debouncedQuery = useDebounce(searchQuery, 300);

  const isSearching = debouncedQuery.length >= 2;
  const lastTrackedQuery = useRef("");

  useEffect(() => {
    if (debouncedQuery.length >= 2 && debouncedQuery !== lastTrackedQuery.current) {
      lastTrackedQuery.current = debouncedQuery;
      trackEvent("search_performed", {
        query: debouncedQuery,
        filters: filters,
      });
    }
  }, [debouncedQuery, filters]);

  const issuesQuery = useIssues({
    ...filters,
    page,
    page_size: 20,
  });

  const searchResultsQuery = useSearchIssues(debouncedQuery, {
    ...filters,
    page,
    page_size: 20,
  });

  const activeQuery = isSearching ? searchResultsQuery : issuesQuery;

  const statsQuery = useStats();
  const companiesQuery = useCompanies();

  const handleLanguageToggle = (language: string) => {
    const current = filters.language || [];
    const next = current.includes(language)
      ? current.filter((l) => l !== language)
      : [...current, language];
    setFilters({ ...filters, language: next.length > 0 ? next : undefined });
    setPage(1);
  };

  const handleFiltersChange = (newFilters: IssueFilters) => {
    setFilters(newFilters);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <StatsBar
        stats={statsQuery.data}
        activeLanguages={filters.language}
        onLanguageClick={handleLanguageToggle}
      />

      <Tabs defaultValue="all">
        <TabsList>
          <TabsTrigger value="all">All Issues</TabsTrigger>
          <TabsTrigger value="bookmarked" disabled>
            Bookmarked
          </TabsTrigger>
        </TabsList>
      </Tabs>

      <SearchBar value={searchQuery} onChange={(v) => { setSearchQuery(v); setPage(1); }} />

      <IssueFiltersPanel
        filters={filters}
        onChange={handleFiltersChange}
        stats={statsQuery.data}
        companies={companiesQuery.data}
      />

      <IssueList
        issues={activeQuery.data?.items}
        isLoading={activeQuery.isLoading}
        total={activeQuery.data?.total}
      />

      <Pagination
        page={page}
        totalPages={activeQuery.data?.total_pages || 0}
        onPageChange={setPage}
      />
    </div>
  );
}

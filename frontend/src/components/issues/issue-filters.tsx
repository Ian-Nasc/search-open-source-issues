"use client";

import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp, Filter, X } from "lucide-react";
import { LABEL_PRESETS } from "@/lib/constants";
import type { IssueFilters, Stats, Company } from "@/lib/types";

interface IssueFiltersProps {
  filters: IssueFilters;
  onChange: (filters: IssueFilters) => void;
  stats?: Stats;
  companies?: Company[];
}

export function IssueFiltersPanel({
  filters,
  onChange,
  stats,
  companies,
}: IssueFiltersProps) {
  const [expanded, setExpanded] = useState(false);

  const toggleLanguage = (lang: string) => {
    const current = filters.language || [];
    const next = current.includes(lang)
      ? current.filter((l) => l !== lang)
      : [...current, lang];
    onChange({ ...filters, language: next.length > 0 ? next : undefined });
  };

  const toggleCompany = (slug: string) => {
    const current = filters.company || [];
    const next = current.includes(slug)
      ? current.filter((c) => c !== slug)
      : [...current, slug];
    onChange({ ...filters, company: next.length > 0 ? next : undefined });
  };

  const toggleLabel = (label: string) => {
    const current = filters.label || [];
    const next = current.includes(label)
      ? current.filter((l) => l !== label)
      : [...current, label];
    onChange({ ...filters, label: next.length > 0 ? next : undefined });
  };

  const clearFilters = () => {
    onChange({});
  };

  const hasFilters =
    (filters.language && filters.language.length > 0) ||
    (filters.company && filters.company.length > 0) ||
    (filters.label && filters.label.length > 0);

  return (
    <div className="rounded-lg border border-border/50 bg-card">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between p-4 text-left"
      >
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">Filters</span>
          {hasFilters && (
            <Badge variant="secondary" className="text-xs">
              Active
            </Badge>
          )}
        </div>
        {expanded ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        )}
      </button>

      {expanded && (
        <div className="space-y-4 border-t border-border/50 p-4">
          {stats && stats.languages.length > 0 && (
            <div>
              <p className="mb-2 text-sm font-medium text-muted-foreground">
                Language
              </p>
              <div className="flex flex-wrap gap-2">
                {stats.languages.slice(0, 12).map((lang) => (
                  <Badge
                    key={lang.language}
                    variant={
                      filters.language?.includes(lang.language)
                        ? "default"
                        : "outline"
                    }
                    className="cursor-pointer transition-colors hover:bg-accent"
                    onClick={() => toggleLanguage(lang.language)}
                  >
                    {lang.language} ({lang.count})
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {companies && companies.length > 0 && (
            <div>
              <p className="mb-2 text-sm font-medium text-muted-foreground">
                Company
              </p>
              <div className="flex flex-wrap gap-2">
                {companies.map((c) => (
                  <Badge
                    key={c.slug}
                    variant={
                      filters.company?.includes(c.slug) ? "default" : "outline"
                    }
                    className="cursor-pointer transition-colors hover:bg-accent"
                    onClick={() => toggleCompany(c.slug)}
                  >
                    {c.name}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          <div>
            <p className="mb-2 text-sm font-medium text-muted-foreground">
              Labels
            </p>
            <div className="flex flex-wrap gap-2">
              {LABEL_PRESETS.map((label) => (
                <Badge
                  key={label}
                  variant={
                    filters.label?.includes(label) ? "default" : "outline"
                  }
                  className="cursor-pointer transition-colors hover:bg-accent"
                  onClick={() => toggleLabel(label)}
                >
                  {label}
                </Badge>
              ))}
            </div>
          </div>

          {hasFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearFilters}
              className="gap-1"
            >
              <X className="h-3 w-3" />
              Clear filters
            </Button>
          )}
        </div>
      )}
    </div>
  );
}

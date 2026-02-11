"use client";

import { Badge } from "@/components/ui/badge";
import { LANGUAGE_COLORS } from "@/lib/constants";
import type { Stats } from "@/lib/types";

interface StatsBarProps {
  stats?: Stats;
  activeLanguages?: string[];
  onLanguageClick?: (language: string) => void;
}

export function StatsBar({
  stats,
  activeLanguages,
  onLanguageClick,
}: StatsBarProps) {
  if (!stats) return null;

  return (
    <div className="space-y-3">
      <p className="text-sm text-muted-foreground">
        <span className="font-semibold text-foreground">
          {stats.total_issues.toLocaleString()}
        </span>{" "}
        issues from{" "}
        <span className="font-semibold text-foreground">
          {stats.total_companies}
        </span>{" "}
        companies
      </p>
      <div className="flex flex-wrap gap-2">
        {stats.languages.slice(0, 10).map((lang) => {
          const color = LANGUAGE_COLORS[lang.language] || "#888";
          const isActive = activeLanguages?.includes(lang.language);
          return (
            <Badge
              key={lang.language}
              variant={isActive ? "default" : "secondary"}
              className="cursor-pointer gap-1.5 transition-colors hover:opacity-80"
              onClick={() => onLanguageClick?.(lang.language)}
            >
              <span
                className="inline-block h-2 w-2 rounded-full"
                style={{ backgroundColor: color }}
              />
              {lang.language} ({lang.count})
            </Badge>
          );
        })}
      </div>
    </div>
  );
}

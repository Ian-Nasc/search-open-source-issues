"use client";

import { Card } from "@/components/ui/card";
import { CompanyAvatar } from "@/components/common/company-avatar";
import { LabelBadge } from "@/components/common/label-badge";
import { LanguageBadge } from "@/components/common/language-badge";
import { ExternalLink, MessageSquare, Star } from "lucide-react";
import type { Issue } from "@/lib/types";
import { trackEvent } from "@/lib/posthog";

interface IssueCardProps {
  issue: Issue;
}

export function IssueCard({ issue }: IssueCardProps) {
  const handleClick = () => {
    trackEvent("issue_clicked", {
      issue_id: issue.id,
      issue_number: issue.number,
      repository: issue.repository.full_name,
      company: issue.company.name,
      language: issue.repository.primary_language,
    });
  };

  return (
    <Card className="group flex items-start gap-4 border-border/50 p-4 transition-all duration-200 hover:border-emerald-500/30 hover:shadow-lg hover:shadow-emerald-500/5">
      <CompanyAvatar company={issue.company} size={40} />

      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
          <span>{issue.company.name}</span>
          <span className="text-muted-foreground/50">/</span>
          <span className="font-medium text-foreground">
            {issue.repository.name}
          </span>
          <span className="text-xs text-muted-foreground/50">
            #{issue.number}
          </span>
        </div>

        <a
          href={issue.url}
          target="_blank"
          rel="noopener noreferrer"
          onClick={handleClick}
          className="mt-1 block font-medium leading-snug text-foreground transition-colors hover:text-emerald-400 hover:underline"
        >
          {issue.title}
          <ExternalLink className="ml-1 inline h-3 w-3 opacity-0 transition-opacity group-hover:opacity-100" />
        </a>

        {issue.label_details && issue.label_details.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {issue.label_details.map((label) => (
              <LabelBadge key={label.name} label={label} />
            ))}
          </div>
        )}
      </div>

      <div className="flex flex-col items-end gap-1.5 text-xs text-muted-foreground">
        <LanguageBadge language={issue.repository.primary_language} />
        <div className="flex items-center gap-1">
          <Star className="h-3 w-3" />
          <span>{issue.repository.stars.toLocaleString()}</span>
        </div>
        <div className="flex items-center gap-1">
          <MessageSquare className="h-3 w-3" />
          <span>{issue.comment_count}</span>
        </div>
      </div>
    </Card>
  );
}

import { Skeleton } from "@/components/ui/skeleton";
import { IssueCard } from "./issue-card";
import type { Issue } from "@/lib/types";

interface IssueListProps {
  issues: Issue[] | undefined;
  isLoading: boolean;
  total?: number;
}

export function IssueList({ issues, isLoading, total }: IssueListProps) {
  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="flex gap-4 rounded-lg border border-border/50 p-4">
            <Skeleton className="h-10 w-10 rounded-full" />
            <div className="flex-1 space-y-2">
              <Skeleton className="h-4 w-1/4" />
              <Skeleton className="h-5 w-3/4" />
              <div className="flex gap-2">
                <Skeleton className="h-5 w-16" />
                <Skeleton className="h-5 w-20" />
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (!issues || issues.length === 0) {
    return (
      <div className="py-12 text-center text-muted-foreground">
        <p className="text-lg">No issues found</p>
        <p className="mt-1 text-sm">Try adjusting your search or filters</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {total !== undefined && (
        <p className="text-sm text-muted-foreground">
          {total.toLocaleString()} issue{total !== 1 ? "s" : ""} found
        </p>
      )}
      {issues.map((issue) => (
        <IssueCard key={issue.id} issue={issue} />
      ))}
    </div>
  );
}

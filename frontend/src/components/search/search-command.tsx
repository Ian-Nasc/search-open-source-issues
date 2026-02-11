"use client";

import { useEffect, useState } from "react";
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { useDebounce } from "@/hooks/use-debounce";
import { useSearchIssues } from "@/hooks/use-issues";
import { ExternalLink } from "lucide-react";

interface SearchCommandProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SearchCommand({ open, onOpenChange }: SearchCommandProps) {
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounce(query, 300);
  const { data } = useSearchIssues(debouncedQuery, {
    page: 1,
    page_size: 8,
  });

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        onOpenChange(!open);
      }
    };
    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, [open, onOpenChange]);

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput
        placeholder="Search issues..."
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        <CommandEmpty>
          {debouncedQuery.length < 2
            ? "Type at least 2 characters to search..."
            : "No issues found."}
        </CommandEmpty>
        {data?.items && data.items.length > 0 && (
          <CommandGroup heading="Issues">
            {data.items.map((issue) => (
              <CommandItem
                key={issue.id}
                onSelect={() => window.open(issue.url, "_blank")}
                className="cursor-pointer"
              >
                <div className="flex flex-1 items-center gap-2">
                  <span className="text-xs text-muted-foreground">
                    {issue.company.name}/{issue.repository.name}
                  </span>
                  <span className="flex-1 truncate">{issue.title}</span>
                  <ExternalLink className="h-3 w-3 text-muted-foreground" />
                </div>
              </CommandItem>
            ))}
          </CommandGroup>
        )}
      </CommandList>
    </CommandDialog>
  );
}

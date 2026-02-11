"use client";

import { useState } from "react";
import { GitFork, Search } from "lucide-react";
import { SearchCommand } from "@/components/search/search-command";

export function Header() {
  const [commandOpen, setCommandOpen] = useState(false);

  return (
    <>
      <header className="sticky top-0 z-50 border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center justify-between">
          <div className="flex items-center gap-2">
            <GitFork className="h-5 w-5 text-emerald-500" />
            <span className="text-lg font-semibold">OSS Issue Finder</span>
          </div>
          <button
            onClick={() => setCommandOpen(true)}
            className="inline-flex items-center gap-2 rounded-md border border-border/50 bg-muted/50 px-3 py-1.5 text-sm text-muted-foreground transition-colors hover:bg-muted"
          >
            <Search className="h-4 w-4" />
            <span className="hidden sm:inline">Search issues...</span>
            <kbd className="pointer-events-none rounded bg-muted px-1.5 py-0.5 text-xs font-medium">
              Cmd+K
            </kbd>
          </button>
        </div>
      </header>
      <SearchCommand open={commandOpen} onOpenChange={setCommandOpen} />
    </>
  );
}

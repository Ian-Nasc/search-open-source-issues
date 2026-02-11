"use client";

import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
}

export function SearchBar({ value, onChange }: SearchBarProps) {
  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        type="text"
        placeholder="Ex: React, AI, authentication, backend engineer..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-11 pl-10 text-sm"
      />
    </div>
  );
}

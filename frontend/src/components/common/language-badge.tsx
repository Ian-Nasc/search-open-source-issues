import { Badge } from "@/components/ui/badge";
import { LANGUAGE_COLORS } from "@/lib/constants";

interface LanguageBadgeProps {
  language: string | null;
  onClick?: () => void;
  active?: boolean;
}

export function LanguageBadge({ language, onClick, active }: LanguageBadgeProps) {
  if (!language) return null;
  const color = LANGUAGE_COLORS[language] || "#888";
  return (
    <Badge
      variant={active ? "default" : "outline"}
      className="cursor-pointer gap-1.5 text-xs transition-colors hover:bg-accent"
      onClick={onClick}
    >
      <span
        className="inline-block h-2.5 w-2.5 rounded-full"
        style={{ backgroundColor: color }}
      />
      {language}
    </Badge>
  );
}

import { Badge } from "@/components/ui/badge";
import type { LabelDetail } from "@/lib/types";

interface LabelBadgeProps {
  label: LabelDetail;
}

export function LabelBadge({ label }: LabelBadgeProps) {
  const bgColor = `#${label.color}20`;
  const textColor = `#${label.color}`;
  const borderColor = `#${label.color}40`;

  return (
    <Badge
      variant="outline"
      className="text-xs"
      style={{
        backgroundColor: bgColor,
        borderColor: borderColor,
        color: textColor,
      }}
    >
      {label.name}
    </Badge>
  );
}

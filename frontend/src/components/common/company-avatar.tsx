import type { Company } from "@/lib/types";

interface CompanyAvatarProps {
  company: Pick<Company, "name" | "logo_url">;
  size?: number;
}

export function CompanyAvatar({ company, size = 40 }: CompanyAvatarProps) {
  if (company.logo_url) {
    return (
      <img
        src={company.logo_url}
        alt={company.name}
        width={size}
        height={size}
        className="rounded-full"
      />
    );
  }

  const initials = company.name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <div
      className="flex items-center justify-center rounded-full bg-muted text-sm font-medium text-muted-foreground"
      style={{ width: size, height: size }}
    >
      {initials}
    </div>
  );
}

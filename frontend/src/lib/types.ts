export interface Company {
  id: number;
  name: string;
  slug: string;
  logo_url: string | null;
  website: string | null;
  description: string | null;
  github_org: string;
  repository_count?: number;
  issue_count?: number;
}

export interface Repository {
  id: number;
  name: string;
  full_name: string;
  primary_language: string | null;
  stars: number;
  url: string;
}

export interface LabelDetail {
  name: string;
  color: string;
  description?: string;
}

export interface Issue {
  id: number;
  github_id: number;
  number: number;
  title: string;
  url: string;
  state: string;
  labels: string[] | null;
  label_details: LabelDetail[] | null;
  comment_count: number;
  github_created_at: string | null;
  github_updated_at: string | null;
  repository: Repository;
  company: Company;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface IssueFilters {
  language?: string[];
  company?: string[];
  label?: string[];
  min_stars?: number;
  sort_by?: "updated" | "created" | "stars";
  sort_order?: "asc" | "desc";
}

export interface LanguageStat {
  language: string;
  count: number;
}

export interface LabelStat {
  label: string;
  count: number;
}

export interface Stats {
  total_issues: number;
  total_repositories: number;
  total_companies: number;
  languages: LanguageStat[];
  top_labels: LabelStat[];
  last_scraped_at: string | null;
}

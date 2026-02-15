import { Header } from "@/components/layout/header";
import { ContributeForm } from "@/components/contribute/contribute-form";
import { GitFork, Building2, Github } from "lucide-react";

export const metadata = {
  title: "Contribute - OSS Issue Finder",
  description: "Suggest a company to add to the OSS Issue Finder",
};

export default function ContributePage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      <main className="container mx-auto max-w-2xl px-4 py-12">
        <div className="mb-8 text-center">
          <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/10">
            <Building2 className="h-6 w-6 text-emerald-500" />
          </div>
          <h1 className="text-3xl font-bold">Suggest a Company</h1>
          <p className="mt-2 text-muted-foreground">
            Know a company with great open source projects? Help us grow the
            directory.
          </p>
        </div>

        <ContributeForm />

        <div className="mt-8 rounded-lg border border-border/50 bg-muted/30 p-6">
          <h2 className="mb-4 flex items-center gap-2 font-medium">
            <Github className="h-5 w-5" />
            What makes a good suggestion?
          </h2>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li className="flex items-start gap-2">
              <GitFork className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-500" />
              Active open source presence with issues labeled for contributors
            </li>
            <li className="flex items-start gap-2">
              <GitFork className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-500" />
              Maintained repositories with recent activity
            </li>
            <li className="flex items-start gap-2">
              <GitFork className="mt-0.5 h-4 w-4 flex-shrink-0 text-emerald-500" />
              Projects that welcome community contributions
            </li>
          </ul>
        </div>
      </main>
    </div>
  );
}

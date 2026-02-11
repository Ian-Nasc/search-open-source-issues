import { Header } from "@/components/layout/header";
import { HeroSection } from "@/components/hero-section";
import { IssuesBrowser } from "@/components/issues-browser";

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />
      <main className="container mx-auto max-w-[1280px] px-4 py-8">
        <HeroSection />
        <IssuesBrowser />
      </main>
    </div>
  );
}

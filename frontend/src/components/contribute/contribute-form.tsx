"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { api } from "@/lib/api";
import { trackEvent } from "@/lib/posthog";
import type { SuggestionCreate } from "@/lib/types";
import { CheckCircle, Loader2, AlertCircle } from "lucide-react";

export function ContributeForm() {
  const [formData, setFormData] = useState<SuggestionCreate>({
    name: "",
    github_org: "",
    email: "",
    reason: "",
  });

  const mutation = useMutation({
    mutationFn: api.suggestions.submit,
    onSuccess: (data) => {
      trackEvent("suggestion_submitted", {
        suggestion_id: data.id,
        github_org: data.github_org,
      });
      setFormData({ name: "", github_org: "", email: "", reason: "" });
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data: SuggestionCreate = {
      name: formData.name,
      github_org: formData.github_org,
    };
    if (formData.email) data.email = formData.email;
    if (formData.reason) data.reason = formData.reason;
    mutation.mutate(data);
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  if (mutation.isSuccess) {
    return (
      <Card className="border-emerald-500/30 bg-emerald-500/5 p-6">
        <div className="flex items-center gap-3">
          <CheckCircle className="h-6 w-6 text-emerald-500" />
          <div>
            <h3 className="font-medium text-emerald-400">
              Suggestion submitted!
            </h3>
            <p className="text-sm text-muted-foreground">
              Thanks for your contribution. We&apos;ll review it soon.
            </p>
          </div>
        </div>
        <Button
          variant="outline"
          className="mt-4"
          onClick={() => mutation.reset()}
        >
          Submit another
        </Button>
      </Card>
    );
  }

  return (
    <Card className="border-border/50 p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <label htmlFor="name" className="text-sm font-medium">
            Company Name <span className="text-red-500">*</span>
          </label>
          <Input
            id="name"
            name="name"
            placeholder="e.g., Vercel"
            value={formData.name}
            onChange={handleChange}
            required
          />
        </div>

        <div className="space-y-2">
          <label htmlFor="github_org" className="text-sm font-medium">
            GitHub Organization <span className="text-red-500">*</span>
          </label>
          <Input
            id="github_org"
            name="github_org"
            placeholder="e.g., vercel"
            value={formData.github_org}
            onChange={handleChange}
            pattern="^[a-zA-Z0-9_-]+$"
            title="Only letters, numbers, hyphens, and underscores"
            required
          />
          <p className="text-xs text-muted-foreground">
            The org name from github.com/org-name
          </p>
        </div>

        <div className="space-y-2">
          <label htmlFor="email" className="text-sm font-medium">
            Your Email{" "}
            <span className="text-muted-foreground">(optional)</span>
          </label>
          <Input
            id="email"
            name="email"
            type="email"
            placeholder="you@example.com"
            value={formData.email}
            onChange={handleChange}
          />
          <p className="text-xs text-muted-foreground">
            We&apos;ll notify you when the company is added
          </p>
        </div>

        <div className="space-y-2">
          <label htmlFor="reason" className="text-sm font-medium">
            Why add this company?{" "}
            <span className="text-muted-foreground">(optional)</span>
          </label>
          <textarea
            id="reason"
            name="reason"
            placeholder="Great open source projects, active community..."
            value={formData.reason}
            onChange={handleChange}
            maxLength={1000}
            rows={3}
            className="w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-xs placeholder:text-muted-foreground focus-visible:border-ring focus-visible:outline-none focus-visible:ring-[3px] focus-visible:ring-ring/50"
          />
        </div>

        {mutation.isError && (
          <div className="flex items-center gap-2 rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-400">
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
            <span>{mutation.error.message}</span>
          </div>
        )}

        <Button
          type="submit"
          className="w-full bg-emerald-600 hover:bg-emerald-700"
          disabled={mutation.isPending}
        >
          {mutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Submitting...
            </>
          ) : (
            "Submit Suggestion"
          )}
        </Button>
      </form>
    </Card>
  );
}

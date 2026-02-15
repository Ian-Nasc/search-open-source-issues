import posthog from "posthog-js";

export const initPostHog = () => {
  if (typeof window === "undefined") return;

  const key = process.env.NEXT_PUBLIC_POSTHOG_KEY;
  if (!key) return;

  posthog.init(key, {
    api_host: process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://app.posthog.com",
    capture_pageview: false, // We handle this manually in the provider
    capture_pageleave: true,
    persistence: "localStorage",
  });
};

export const trackEvent = (
  event: string,
  properties?: Record<string, unknown>
) => {
  if (typeof window === "undefined") return;
  if (!process.env.NEXT_PUBLIC_POSTHOG_KEY) return;

  posthog.capture(event, properties);
};

export { posthog };

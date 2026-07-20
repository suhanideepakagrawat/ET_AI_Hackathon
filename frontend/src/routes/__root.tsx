import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  useRouter,
  HeadContent,
  Scripts,
} from "@tanstack/react-router";
import { useEffect, type ReactNode } from "react";

import appCss from "../styles.css?url";
import { reportLovableError } from "../lib/lovable-error-reporting";

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <div className="chip mx-auto mb-6">404 · No signal</div>
        <h1 className="font-display text-4xl text-foreground">Location not indexed</h1>
        <p className="mono mt-3 text-sm text-muted-foreground">
          The route you requested is not part of the current pipeline.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="mono inline-flex items-center justify-center border border-accent px-4 py-2 text-xs uppercase tracking-wider text-accent transition-colors hover:bg-accent hover:text-accent-foreground"
          >
            Return to overview
          </Link>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: { error: Error; reset: () => void }) {
  console.error(error);
  const router = useRouter();
  useEffect(() => {
    reportLovableError(error, { boundary: "tanstack_root_error_component" });
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <div className="chip mx-auto mb-6" style={{ borderColor: "var(--source-burning)", color: "var(--source-burning)" }}>Pipeline error</div>
        <h1 className="font-display text-2xl text-foreground">This view failed to load</h1>
        <p className="mono mt-3 text-sm text-muted-foreground">
          A component in the request chain did not respond. Retry or return to the overview.
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <button
            onClick={() => { router.invalidate(); reset(); }}
            className="mono border border-accent bg-accent px-4 py-2 text-xs uppercase tracking-wider text-accent-foreground"
          >
            Retry
          </button>
          <a href="/" className="mono border border-border px-4 py-2 text-xs uppercase tracking-wider text-foreground hover:border-accent-dim">
            Overview
          </a>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "AirGrid NCR" },
      { name: "description", content: "Hyperlocal air quality forecasts for Delhi-NCR with source attribution, wind-corridor evidence, and ward-level enforcement priorities." },
      { name: "author", content: "AirGrid" },
      { property: "og:title", content: "AirGrid NCR" },
      { property: "og:description", content: "Hyperlocal air quality forecasts for Delhi-NCR with source attribution, wind-corridor evidence, and ward-level enforcement priorities." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "twitter:title", content: "AirGrid NCR" },
      { name: "twitter:description", content: "Hyperlocal air quality forecasts for Delhi-NCR with source attribution, wind-corridor evidence, and ward-level enforcement priorities." },
      { property: "og:image", content: "https://pub-bb2e103a32db4e198524a2e9ed8f35b4.r2.dev/66def51c-43f7-4d8d-9f4f-a46db62cddfe/id-preview-1fe05ae2--b27f28df-0e83-42e8-99f6-ade9c994fb18.lovable.app-1784554358281.png" },
      { name: "twitter:image", content: "https://pub-bb2e103a32db4e198524a2e9ed8f35b4.r2.dev/66def51c-43f7-4d8d-9f4f-a46db62cddfe/id-preview-1fe05ae2--b27f28df-0e83-42e8-99f6-ade9c994fb18.lovable.app-1784554358281.png" },
    ],
    links: [
      { rel: "stylesheet", href: appCss },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      { rel: "stylesheet", href: "https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;600&display=swap" },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootShell({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  const { queryClient } = Route.useRouteContext();
  return (
    <QueryClientProvider client={queryClient}>
      <Outlet />
    </QueryClientProvider>
  );
}

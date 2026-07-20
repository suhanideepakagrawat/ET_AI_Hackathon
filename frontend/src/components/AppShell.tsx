import { useQuery } from "@tanstack/react-query";
import { Link, useRouterState } from "@tanstack/react-router";
import type { ReactNode } from "react";
import { CITIZEN_APP_URL, healthQuery } from "@/lib/api";

const NAV = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/attribution", label: "Attribution" },
  { to: "/enforcement", label: "Enforcement" },
  { to: "/health", label: "Citizen advisory" },
] as const;

export function AppShell({ children, right }: { children: ReactNode; right?: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const api = useQuery(healthQuery);
  const live = api.isSuccess;
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <header className="flex items-center justify-between border-b border-border bg-panel px-5 py-3">
        <div className="flex items-center gap-8">
          <Link to="/" className="flex items-center gap-2">
            <LogoMark />
            <span className="text-sm font-bold tracking-tight">
              AirGrid<span className="text-accent-dim">·</span>NCR
            </span>
          </Link>
          <nav className="flex items-center gap-1">
            {NAV.map((n) => {
              const active = pathname === n.to;
              return (
                <Link
                  key={n.to}
                  to={n.to}
                  className={`px-3 py-1.5 text-[14px] font-semibold transition-colors ${
                    active
                      ? "border-b-2 border-accent-dim text-accent"
                      : "border-b-2 border-transparent text-text-dim hover:text-foreground"
                  }`}
                >
                  {n.label}
                </Link>
              );
            })}
          </nav>
        </div>
        <div className="flex items-center gap-4">
          {right}
          <a
            href={CITIZEN_APP_URL}
            target="_blank"
            rel="noopener"
            className="hidden rounded-full bg-accent px-3.5 py-1.5 text-[12px] font-semibold text-white hover:bg-[#064a42] md:inline-flex"
          >
            Open VayuMitra →
          </a>
          <div
            className="mono flex items-center gap-2 text-[11px] text-text-dim"
            title={live ? "Backend API connected" : "Backend unreachable — showing bundled sample data"}
          >
            <span className={`h-1.5 w-1.5 rounded-full ${live ? "bg-[#009966]" : "bg-[#ff9933]"}`} />
            {live ? "Live API" : "Sample data"}
          </div>
        </div>
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}

export function LogoMark({ className = "" }: { className?: string }) {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" className={className} aria-hidden>
      <rect x="1" y="1" width="6" height="6" rx="1.5" fill="var(--accent)" fillOpacity="0.3" />
      <rect x="8" y="1" width="6" height="6" rx="1.5" fill="var(--accent)" fillOpacity="0.65" />
      <rect x="15" y="1" width="6" height="6" rx="1.5" fill="var(--accent)" />
      <rect x="1" y="8" width="6" height="6" rx="1.5" fill="var(--accent)" fillOpacity="0.5" />
      <rect x="8" y="8" width="6" height="6" rx="1.5" fill="var(--accent)" fillOpacity="0.85" />
      <rect x="15" y="8" width="6" height="6" rx="1.5" fill="var(--accent)" fillOpacity="0.35" />
      <rect x="1" y="15" width="6" height="6" rx="1.5" fill="var(--accent)" fillOpacity="0.15" />
      <rect x="8" y="15" width="6" height="6" rx="1.5" fill="var(--accent)" fillOpacity="0.4" />
      <rect x="15" y="15" width="6" height="6" rx="1.5" fill="var(--accent)" fillOpacity="0.7" />
    </svg>
  );
}

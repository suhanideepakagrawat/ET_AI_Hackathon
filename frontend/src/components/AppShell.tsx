import { Link, useRouterState } from "@tanstack/react-router";
import type { ReactNode } from "react";

const NAV = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/attribution", label: "Attribution" },
  { to: "/enforcement", label: "Enforcement" },
  { to: "/health", label: "Health" },
] as const;

export function AppShell({ children, right }: { children: ReactNode; right?: ReactNode }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <header className="flex items-center justify-between border-b border-border bg-bg-secondary px-5 py-3">
        <div className="flex items-center gap-8">
          <Link to="/" className="flex items-center gap-2">
            <LogoMark />
            <span className="font-display text-sm font-semibold tracking-tight">
              AirGrid<span className="text-accent">·</span>NCR
            </span>
          </Link>
          <nav className="flex items-center gap-1">
            {NAV.map((n) => {
              const active = pathname === n.to || (n.to === "/dashboard" && pathname === "/dashboard");
              return (
                <Link
                  key={n.to}
                  to={n.to}
                  className={`mono px-3 py-1.5 text-[11px] uppercase tracking-wider transition-colors ${
                    active
                      ? "border-b border-accent text-accent"
                      : "border-b border-transparent text-text-dim hover:text-foreground"
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
          <div className="mono flex items-center gap-2 text-[11px] text-text-dim">
            <span className="h-1.5 w-1.5 rounded-full bg-accent cell-pulse" />
            RUN · 2026-07-20 · 09:00 IST
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
      <rect x="1" y="1" width="6" height="6" fill="var(--accent)" fillOpacity="0.3" />
      <rect x="8" y="1" width="6" height="6" fill="var(--accent)" fillOpacity="0.65" />
      <rect x="15" y="1" width="6" height="6" fill="var(--accent)" />
      <rect x="1" y="8" width="6" height="6" fill="var(--accent)" fillOpacity="0.5" />
      <rect x="8" y="8" width="6" height="6" fill="var(--accent)" fillOpacity="0.85" />
      <rect x="15" y="8" width="6" height="6" fill="var(--accent)" fillOpacity="0.35" />
      <rect x="1" y="15" width="6" height="6" fill="var(--accent)" fillOpacity="0.15" />
      <rect x="8" y="15" width="6" height="6" fill="var(--accent)" fillOpacity="0.4" />
      <rect x="15" y="15" width="6" height="6" fill="var(--accent)" fillOpacity="0.7" />
    </svg>
  );
}

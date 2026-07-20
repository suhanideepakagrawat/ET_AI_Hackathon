import { createFileRoute, Link } from "@tanstack/react-router";
import { MapView } from "@/components/MapView";
import { LogoMark } from "@/components/AppShell";
import { SOURCE_COLORS, SOURCE_EVIDENCE, SOURCE_LABELS, type SourceKey } from "@/lib/air-data";
import { CITIZEN_APP_URL } from "@/lib/api";

export const Route = createFileRoute("/")({
  component: Landing,
});

function Landing() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Top bar */}
      <header className="relative z-20 flex items-center justify-between px-6 py-5">
        <div className="flex items-center gap-2">
          <LogoMark />
          <span className="font-display text-sm font-semibold">
            AirGrid<span className="text-accent">·</span>NCR
          </span>
        </div>
        <nav className="mono hidden items-center gap-6 text-[11px] text-text-dim md:flex">
          <a href="#attribution" className="hover:text-foreground">Attribution</a>
          <a href="#forecast" className="hover:text-foreground">Forecast</a>
          <a href="#audiences" className="hover:text-foreground">For operators</a>
          <a href="#method" className="hover:text-foreground">Method</a>
        </nav>
        <Link
          to="/dashboard"
          className="mono border border-accent px-3 py-1.5 text-[11px] text-accent hover:bg-accent hover:text-accent-foreground"
        >
          Open dashboard →
        </Link>
      </header>

      {/* Hero — ambient map + thesis */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 opacity-70">
          <MapView ambient height="100%" />
        </div>
        <div className="absolute inset-0 bg-gradient-to-b from-bg-primary/60 via-bg-primary/30 to-bg-primary" />

        <div className="relative z-10 mx-auto max-w-6xl px-6 pb-32 pt-24 md:pt-32">
          <div className="chip mb-6" style={{ color: "var(--accent)", borderColor: "var(--accent-dim)" }}>
            <span className="h-1.5 w-1.5 rounded-full bg-accent cell-pulse" />
            Delhi-NCR pilot · live pipeline · English + हिन्दी
          </div>
          <h1 className="max-w-4xl text-4xl font-bold leading-[1.08] tracking-tight md:text-6xl">
            Air quality forecasts that name the source —
            <span className="text-accent"> and where to act.</span>
          </h1>
          <p className="mt-6 max-w-2xl text-base text-text-dim md:text-lg">
            Every 1 km cell across the National Capital Region carries a 24–72 hour AQI forecast,
            a dominant emission source attributed with a confidence score, and the physical evidence
            behind that call — wind corridor, land use, satellite fire detections. And every citizen
            gets it as personal, health-band-cited advice in their language.
          </p>

          <div className="mt-10 flex flex-wrap items-center gap-4">
            <Link
              to="/dashboard"
              className="inline-flex items-center gap-2 rounded-full bg-accent px-6 py-3 text-sm font-semibold text-white hover:bg-[#064a42]"
            >
              Open live dashboard
              <span aria-hidden>→</span>
            </Link>
            <a
              href={CITIZEN_APP_URL}
              target="_blank"
              rel="noopener"
              className="inline-flex items-center gap-2 rounded-full border-[1.5px] border-accent-dim px-6 py-3 text-sm font-semibold text-accent hover:bg-accent hover:text-white"
            >
              Try VayuMitra — citizen app
            </a>
            <a
              href="#attribution"
              className="inline-flex items-center gap-2 px-2 py-3 text-sm font-semibold text-text-dim hover:text-foreground"
            >
              How attribution works
            </a>
          </div>

          {/* Coordinate readout */}
          <div className="mono mt-16 grid max-w-3xl grid-cols-2 gap-x-8 gap-y-3 border-t border-border pt-6 text-[11px] text-text-mute md:grid-cols-4">
            <Readout k="Grid" v="1.0 km²" />
            <Readout k="Horizon" v="24 / 48 / 72 h" />
            <Readout k="Sources" v="4 attributed" />
            <Readout k="Coverage" v="28.4°N 76.9°E → 28.9°N 77.6°E" />
          </div>
        </div>
      </section>

      {/* Attribution section */}
      <section id="attribution" className="border-t border-border">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="mb-12 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="chip mb-3">Attribution</div>
              <h2 className="max-w-2xl font-display text-3xl font-semibold md:text-4xl">
                Four sources. Each detectable from independent physical evidence.
              </h2>
            </div>
            <p className="max-w-md text-sm text-text-dim">
              The engine does not average a national blend. It separates traffic, industry,
              construction dust, and regional biomass burning per cell — and states why.
            </p>
          </div>

          <div className="grid gap-px overflow-hidden border border-border bg-border md:grid-cols-2">
            {(Object.keys(SOURCE_LABELS) as SourceKey[]).map((k) => (
              <SourceCard key={k} k={k} />
            ))}
          </div>
        </div>
      </section>

      {/* Forecast horizon */}
      <section id="forecast" className="border-t border-border bg-bg-secondary">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="mb-10">
            <div className="chip mb-3">Forecast horizon</div>
            <h2 className="max-w-2xl font-display text-3xl font-semibold md:text-4xl">
              Grid-resolution forecasts, 24 to 72 hours out.
            </h2>
            <p className="mt-4 max-w-2xl text-sm text-text-dim">
              Every cell you see is a real forecast unit — not a smoothed municipal average.
              Confidence saturation shows which cells the model is sure about.
            </p>
          </div>
          <div className="overflow-hidden border border-border">
            <div className="grid grid-cols-3 border-b border-border bg-bg-primary">
              {["+24 h", "+48 h", "+72 h"].map((h, i) => (
                <div key={h} className={`px-5 py-3 ${i === 0 ? "border-r-0" : "border-l border-border"}`}>
                  <div className="mono text-[11px] text-text-mute">Horizon</div>
                  <div className="mono mt-1 text-lg text-accent">{h}</div>
                </div>
              ))}
            </div>
            <div className="h-[420px] bg-bg-secondary">
              <MapView ambient height="100%" />
            </div>
          </div>
        </div>
      </section>

      {/* Dual audience */}
      <section id="audiences" className="border-t border-border">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="mb-10">
            <div className="chip mb-3">Who uses this</div>
            <h2 className="max-w-3xl font-display text-3xl font-semibold md:text-4xl">
              Built for operators making decisions. Legible enough for the citizens they serve.
            </h2>
          </div>
          <div className="grid gap-6 md:grid-cols-2">
            <AudiencePanel
              tag="Enforcement"
              title="A ranked action list, not a wall of numbers."
              body="Priority scores fuse forecast severity, source attribution, and proximity to registered emission points. Every entry links to the cell evidence that justifies it."
              stat="7"
              statLabel="High-priority actions today"
              cta={{ to: "/enforcement", label: "Enforcement queue" }}
            />
            <AudiencePanel
              tag="Citizen"
              title="Exposure at your address, in plain language."
              body="Instead of a single color, you get: what tomorrow looks like, which source is driving it, and — if you're in a vulnerable group — what to actually do about it."
              stat="1,306"
              statLabel="Sensitive-population sites indexed"
              cta={{ to: "/health", label: "Health advisory" }}
            />
          </div>
        </div>
      </section>

      {/* Method / CTA */}
      <section id="method" className="border-t border-border bg-bg-secondary">
        <div className="mx-auto max-w-6xl px-6 py-24 text-center">
          <div className="chip mx-auto mb-6">Ready when you are</div>
          <h2 className="mx-auto max-w-3xl font-display text-3xl font-semibold md:text-5xl">
            Stop asking <span className="text-text-mute">"how bad is it?"</span>
            <br />Start asking <span className="text-accent">"what do we do about it?"</span>
          </h2>
          <div className="mt-10 flex flex-wrap justify-center gap-3">
            <Link
              to="/dashboard"
              className="mono inline-flex items-center gap-2 border border-accent bg-accent px-6 py-3 text-xs text-accent-foreground hover:brightness-110"
            >
              Open the dashboard →
            </Link>
            <Link
              to="/attribution"
              className="mono inline-flex items-center gap-2 border border-border px-6 py-3 text-xs text-text-dim hover:border-accent-dim hover:text-foreground"
            >
              City-wide trends
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-border">
        <div className="mono mx-auto flex max-w-6xl flex-col items-start gap-4 px-6 py-8 text-[11px] text-text-mute md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-2">
            <LogoMark />
            <span>AirGrid · NCR pipeline v0.4</span>
          </div>
          <div className="flex gap-6">
            <span>Data: CPCB · IMD · MODIS/VIIRS · DPCC</span>
            <span>Not an official government product</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

function Readout({ k, v }: { k: string; v: string }) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-text-mute">{k}</span>
      <span className="text-foreground">{v}</span>
    </div>
  );
}

function SourceCard({ k }: { k: SourceKey }) {
  return (
    <div className="bg-bg-primary p-6">
      <div className="mb-4 flex items-center gap-3">
        <span
          className="h-2.5 w-2.5"
          style={{ background: SOURCE_COLORS[k] }}
          aria-hidden
        />
        <span className="mono text-[11px] text-text-mute">Source</span>
        <span className="font-display text-lg text-foreground">{SOURCE_LABELS[k]}</span>
      </div>
      <p className="text-sm text-text-dim">{SOURCE_EVIDENCE[k]}</p>
      <div className="mono mt-4 flex items-center gap-4 text-[11px] text-text-mute">
        <span>Evidence · wind corridor</span>
        <span>·</span>
        <span>Land use</span>
        <span>·</span>
        <span>{k === "burning" ? "Satellite fire" : "Registered permits"}</span>
      </div>
    </div>
  );
}

function AudiencePanel({
  tag,
  title,
  body,
  stat,
  statLabel,
  cta,
}: {
  tag: string;
  title: string;
  body: string;
  stat: string;
  statLabel: string;
  cta: { to: "/enforcement" | "/health"; label: string };
}) {
  return (
    <div className="panel flex flex-col p-6">
      <div className="chip w-fit" style={{ color: "var(--accent)", borderColor: "var(--accent-dim)" }}>{tag}</div>
      <h3 className="mt-4 font-display text-xl">{title}</h3>
      <p className="mt-3 flex-1 text-sm text-text-dim">{body}</p>
      <div className="mt-6 flex items-end justify-between border-t border-border pt-4">
        <div>
          <div className="mono text-3xl text-accent">{stat}</div>
          <div className="mono text-[11px] text-text-mute">{statLabel}</div>
        </div>
        <Link
          to={cta.to}
          className="mono border border-border px-3 py-1.5 text-[11px] text-text-dim hover:border-accent hover:text-accent"
        >
          {cta.label} →
        </Link>
      </div>
    </div>
  );
}

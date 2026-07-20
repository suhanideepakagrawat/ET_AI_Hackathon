import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { MapView } from "@/components/MapView";
import {
  aqiCategory,
  CELLS,
  SOURCE_COLORS,
  SOURCE_EVIDENCE,
  SOURCE_LABELS,
  ENFORCEMENT_TARGETS,
  type Cell,
  type SourceKey,
} from "@/lib/air-data";
import { wardsQuery } from "@/lib/api";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard — AirGrid NCR" },
      { name: "description", content: "Live map-first view of Delhi-NCR air quality, source attribution, and enforcement targets." },
    ],
  }),
  component: Dashboard,
});

type Horizon = "24" | "48" | "72";

function Dashboard() {
  const [selected, setSelected] = useState<Cell | null>(CELLS.find((c) => c.id === "c-5-2") ?? null);
  const [horizon, setHorizon] = useState<Horizon>("24");
  const [sourceFilter, setSourceFilter] = useState<SourceKey | "all">("all");
  const [layers, setLayers] = useState({
    windCorridor: true,
    fires: true,
    wards: false,
    enforcement: true,
    vulnerable: false,
  });

  return (
    <AppShell
      right={
        <div className="mono flex items-center gap-2">
          {(["24", "48", "72"] as Horizon[]).map((h) => (
            <button
              key={h}
              onClick={() => setHorizon(h)}
              className={`px-2 py-1 text-[11px] ${
                horizon === h
                  ? "border border-accent text-accent"
                  : "border border-transparent text-text-dim hover:text-foreground"
              }`}
            >
              +{h}h
            </button>
          ))}
        </div>
      }
    >
      <div className="grid h-[calc(100vh-57px)] grid-cols-1 md:grid-cols-[260px_1fr]">
        {/* Sidebar */}
        <aside className="hidden overflow-y-auto border-r border-border bg-bg-secondary md:block">
          <LiveWardRail />
          <FilterSection title="Layers">
            {[
              ["windCorridor", "Wind corridor"],
              ["fires", "Fire hotspots"],
              ["wards", "Ward outlines"],
              ["enforcement", "Enforcement pins"],
              ["vulnerable", "Sensitive sites"],
            ].map(([k, label]) => (
              <ToggleRow
                key={k}
                label={label}
                on={layers[k as keyof typeof layers]}
                onChange={(v) => setLayers((s) => ({ ...s, [k]: v }))}
              />
            ))}
          </FilterSection>

          <FilterSection title="Source filter">
            <button
              onClick={() => setSourceFilter("all")}
              className={`mono w-full px-2 py-1.5 text-left text-[11px] ${
                sourceFilter === "all" ? "bg-surface-1 text-accent" : "text-text-dim hover:text-foreground"
              }`}
            >
              All sources
            </button>
            {(Object.keys(SOURCE_LABELS) as SourceKey[]).map((k) => (
              <button
                key={k}
                onClick={() => setSourceFilter((s) => (s === k ? "all" : k))}
                className={`flex w-full items-center gap-2 px-2 py-1.5 text-left text-[11px] ${
                  sourceFilter === k ? "bg-surface-1" : "hover:bg-surface-1/50"
                }`}
              >
                <span className="h-2 w-2 shrink-0" style={{ background: SOURCE_COLORS[k] }} />
                <span className="mono" style={{ color: sourceFilter === k ? "var(--accent)" : "var(--text-dim)" }}>
                  {SOURCE_LABELS[k]}
                </span>
              </button>
            ))}
          </FilterSection>

          <FilterSection title="Legend">
            <div className="mono space-y-1.5 text-[11px] text-text-mute">
              <div className="flex items-center justify-between"><span>Confidence</span><span>Opacity</span></div>
              <div className="flex h-2 w-full bg-gradient-to-r from-[color:var(--accent-dim)]/15 to-accent" />
              <div className="flex items-center justify-between pt-1"><span>Low</span><span>High</span></div>
            </div>
            <div className="mt-4 mono space-y-1.5 text-[11px] text-text-mute">
              <div>Marker shapes</div>
              <div className="flex items-center gap-2 text-text-dim"><span className="inline-block h-2 w-2 rotate-45 border border-accent" /> Sensitive site</div>
              <div className="flex items-center gap-2 text-text-dim">
                <svg width="10" height="10"><polygon points="5,0 0,10 10,10" fill="var(--accent)" /></svg>
                Enforcement target
              </div>
            </div>
          </FilterSection>
        </aside>

        {/* Map + detail */}
        <section className="grid grid-rows-[1fr_auto] overflow-hidden">
          <div className="relative min-h-0 overflow-hidden border-b border-border">
            <MapView
              selectedId={selected?.id}
              onSelect={setSelected}
              layers={layers}
              sourceFilter={sourceFilter}
            />
            {/* Overlay HUD */}
            <div className="pointer-events-none absolute left-4 top-4 flex flex-col gap-1">
              <div className="chip pointer-events-auto"><span className="h-1.5 w-1.5 rounded-full bg-accent cell-pulse" /> Model grid · 336 cells (sample scene)</div>
              <div className="mono text-[11px] text-text-mute">Forecast horizon · +{horizon}h</div>
            </div>
          </div>

          <DetailPanel cell={selected} horizon={horizon} />
        </section>
      </div>
    </AppShell>
  );
}

function LiveWardRail() {
  const q = useQuery(wardsQuery());
  return (
    <FilterSection title={q.isSuccess ? `Ward feed · live API (${q.data.data_kind} data)` : "Ward feed"}>
      {q.isPending && (
        <div className="mono px-2 py-1.5 text-[11px] text-text-mute">Connecting to pipeline…</div>
      )}
      {q.isError && (
        <div className="mono px-2 py-1.5 text-[11px] text-text-mute">
          API unreachable — map shows the bundled sample scene.
        </div>
      )}
      {q.isSuccess && (
        <ul className="space-y-1">
          {q.data.wards.slice(0, 8).map((w) => {
            const cat = aqiCategory(w.aqi);
            return (
              <li key={w.zone_id} className="flex items-center justify-between gap-2 px-2 py-1">
                <span className="truncate text-[12px] text-text-dim">{w.name}</span>
                <span
                  className="mono shrink-0 rounded-md px-1.5 py-0.5 text-[11px] font-bold"
                  style={{ background: cat.color, color: cat.text }}
                  title={`${cat.label} · ${w.dominant_source ?? ""}`}
                >
                  {w.aqi}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </FilterSection>
  );
}

function FilterSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="border-b border-border p-4">
      <div className="mono mb-3 text-[11px] text-text-mute">{title}</div>
      <div className="space-y-1">{children}</div>
    </div>
  );
}

function ToggleRow({ label, on, onChange }: { label: string; on: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      onClick={() => onChange(!on)}
      className="flex w-full items-center justify-between px-2 py-1.5 text-left text-[12px] text-text-dim hover:text-foreground"
    >
      <span>{label}</span>
      <span
        className={`mono text-[11px] ${on ? "text-accent" : "text-text-mute"}`}
      >
        {on ? "● on" : "○ off"}
      </span>
    </button>
  );
}

function DetailPanel({ cell, horizon }: { cell: Cell | null; horizon: string }) {
  if (!cell) {
    return (
      <div className="border-t border-border bg-bg-secondary px-6 py-8 text-center">
        <div className="mono text-[11px] text-text-mute">
          Select a grid cell to see attribution evidence.
        </div>
      </div>
    );
  }
  const cat = aqiCategory(cell.aqi);
  const enforcement = ENFORCEMENT_TARGETS.filter((e) => e.cellId === cell.id || e.ward === cell.ward);

  return (
    <div className="grid grid-cols-1 gap-px bg-border md:grid-cols-[280px_1fr_320px]">
      {/* AQI + ward */}
      <div className="bg-bg-secondary p-5">
        <div className="mono text-[11px] text-text-mute">
          {cell.wardCode} · Cell {cell.id}
        </div>
        <div className="mt-2 text-xl font-bold">{cell.ward}</div>
        <div className="mt-5 flex items-center gap-3">
          {/* AQI indicator — filled band circle, Legible Band Rule text */}
          <div
            className="mono grid h-16 w-16 shrink-0 place-items-center rounded-full text-center leading-none"
            style={{ background: cat.color, color: cat.text }}
          >
            <div>
              <div className="text-xl font-bold">{cell.aqi}</div>
              <div className="text-[11px] opacity-85">AQI</div>
            </div>
          </div>
          <div>
            <div
              className="mono inline-block rounded-md px-2 py-0.5 text-[12px] font-bold"
              style={{ background: cat.color, color: cat.text }}
            >
              {cat.label}
            </div>
            <div className="mono mt-1 text-[11px] text-text-mute">CPCB band · +{horizon}h</div>
          </div>
        </div>
        <div className="mt-6 border-t border-border pt-3 mono text-[11px] text-text-mute">
          Coord · 28.{600 + cell.y * 8}°N 77.{100 + cell.x * 6}°E
        </div>
      </div>

      {/* Attribution */}
      <div className="bg-bg-secondary p-5">
        <div className="flex items-baseline justify-between">
          <div className="mono text-[11px] text-text-mute">Likely source</div>
          <div className="mono text-[11px] text-text-mute">
            Confidence · {Math.round(cell.confidence * 100)}%
          </div>
        </div>
        <div className="mt-2 flex items-center gap-3">
          <span className="h-3 w-3" style={{ background: SOURCE_COLORS[cell.dominantSource] }} />
          <span className="font-display text-xl">{SOURCE_LABELS[cell.dominantSource]}</span>
        </div>
        <p className="mt-3 max-w-md text-sm text-text-dim">
          {SOURCE_EVIDENCE[cell.dominantSource]}
        </p>

        <div className="mt-6">
          <div className="mono mb-2 text-[11px] text-text-mute">Source mix</div>
          <div className="flex h-3 overflow-hidden border border-border">
            {(Object.keys(SOURCE_LABELS) as SourceKey[]).map((k) => (
              <div
                key={k}
                title={`${SOURCE_LABELS[k]} · ${Math.round(cell.attribution[k] * 100)}%`}
                style={{ width: `${cell.attribution[k] * 100}%`, background: SOURCE_COLORS[k] }}
              />
            ))}
          </div>
          <div className="mono mt-3 grid grid-cols-2 gap-x-6 gap-y-1 text-[11px]">
            {(Object.keys(SOURCE_LABELS) as SourceKey[]).map((k) => (
              <div key={k} className="flex items-center justify-between">
                <span className="flex items-center gap-2 text-text-dim">
                  <span className="h-1.5 w-1.5" style={{ background: SOURCE_COLORS[k] }} />
                  {SOURCE_LABELS[k]}
                </span>
                <span className="text-foreground">{Math.round(cell.attribution[k] * 100)}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Enforcement / actions */}
      <div className="bg-bg-secondary p-5">
        <div className="mono text-[11px] text-text-mute">Nearby registered sources</div>
        {enforcement.length ? (
          <ul className="mt-3 space-y-3">
            {enforcement.map((e) => (
              <li key={e.id} className="border-l border-accent-dim pl-3">
                <div className="flex items-center justify-between">
                  <span className="font-display text-sm">{e.name}</span>
                  <span className="mono text-[11px] text-accent">P{e.priority}</span>
                </div>
                <div className="mono text-[11px] text-text-mute">{e.type}</div>
                <div className="mt-1 text-[12px] text-text-dim">{e.action}</div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="mono mt-3 text-[11px] text-text-mute">
            No registered emission sources within 1.5 km. Attribution driven by regional transport or diffuse activity.
          </div>
        )}
      </div>
    </div>
  );
}

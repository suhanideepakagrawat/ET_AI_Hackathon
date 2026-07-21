import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { MapView } from "@/components/MapView";
import {
  AqiBall,
  BandBadge,
  BandDistribution,
  DeltaTag,
  HorizonSwitch,
  HorizonTriplet,
  HORIZON_LABEL,
} from "@/components/charts";
import { MethodPanel } from "@/components/HowItWorks";
import {
  aqiCategory,
  CELLS,
  cellAqi,
  HORIZONS,
  SOURCE_COLORS,
  SOURCE_EVIDENCE,
  SOURCE_LABELS,
  ENFORCEMENT_TARGETS,
  type Cell,
  type Horizon,
  type SourceKey,
} from "@/lib/air-data";
import { wardAqiAt, wardsQuery, type LiveWard } from "@/lib/api";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard — AirGrid NCR" },
      { name: "description", content: "Live map-first view of Delhi-NCR air quality, source attribution, and enforcement targets." },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  const [selected, setSelected] = useState<Cell | null>(CELLS.find((c) => c.id === "c-5-2") ?? null);
  const [horizon, setHorizon] = useState<Horizon>("24");
  const [showMethod, setShowMethod] = useState(false);
  const [sourceFilter, setSourceFilter] = useState<SourceKey | "all">("all");
  const [layers, setLayers] = useState({
    windCorridor: true,
    fires: true,
    wards: false,
    enforcement: true,
    vulnerable: false,
  });

  const live = useQuery(wardsQuery());
  const liveWards: LiveWard[] | null =
    live.isSuccess && live.data.wards.length > 0 ? live.data.wards : null;

  return (
    <AppShell>
      <div className="flex h-[calc(100vh-57px)] flex-col">
        <PulseStrip
          horizon={horizon}
          onHorizon={setHorizon}
          liveWards={liveWards}
          dataKind={live.isSuccess ? live.data.data_kind : null}
          showMethod={showMethod}
          onToggleMethod={() => setShowMethod((s) => !s)}
        />
        {showMethod && (
          <div className="border-b border-border bg-bg-primary px-5 py-4">
            <MethodPanel method="forecast" />
          </div>
        )}

        <div className="grid min-h-0 flex-1 grid-cols-1 md:grid-cols-[260px_1fr]">
          {/* Sidebar */}
          <aside className="hidden overflow-y-auto border-r border-border bg-bg-secondary md:block">
            <LiveWardRail horizon={horizon} liveWards={liveWards} pending={live.isPending} />
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
                <div className="flex items-center justify-between"><span>Forecast load</span><span>Intensity</span></div>
                <div className="flex h-2 w-full bg-gradient-to-r from-[color:var(--accent-dim)]/15 to-accent" />
                <div className="flex items-center justify-between pt-1"><span>Cleaner</span><span>Worse</span></div>
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
          <section className="grid min-h-0 grid-rows-[1fr_auto] overflow-hidden">
            <div className="relative min-h-0 overflow-hidden border-b border-border">
              <MapView
                selectedId={selected?.id}
                onSelect={setSelected}
                layers={layers}
                sourceFilter={sourceFilter}
                horizon={horizon}
              />
              <div className="pointer-events-none absolute left-4 top-4 flex flex-col gap-1">
                <div className="chip pointer-events-auto"><span className="h-1.5 w-1.5 rounded-full bg-accent cell-pulse" /> Model grid · sample scene (live wards in the rail)</div>
                <div className="mono text-[11px] text-text-mute">Showing +{horizon} h · {HORIZON_LABEL[horizon].toLowerCase()}</div>
              </div>
            </div>

            <DetailPanel cell={selected} horizon={horizon} onHorizon={setHorizon} />
          </section>
        </div>
      </div>
    </AppShell>
  );
}

/* ------------------------------------------------------------------ */
/* City pulse — the strip where the horizon control lives              */
/* ------------------------------------------------------------------ */

function PulseStrip({
  horizon,
  onHorizon,
  liveWards,
  dataKind,
  showMethod,
  onToggleMethod,
}: {
  horizon: Horizon;
  onHorizon: (h: Horizon) => void;
  liveWards: LiveWard[] | null;
  dataKind: string | null;
  showMethod: boolean;
  onToggleMethod: () => void;
}) {
  const stats = useMemo(() => {
    if (liveWards) {
      const perHorizon = Object.fromEntries(
        HORIZONS.map((h) => [h, liveWards.map((w) => wardAqiAt(w, h))]),
      ) as Record<Horizon, number[]>;
      const mean = (xs: number[]) => Math.round(xs.reduce((a, b) => a + b, 0) / (xs.length || 1));
      const aqis = perHorizon[horizon];
      const worstIdx = aqis.indexOf(Math.max(...aqis));
      return {
        aqis,
        avg: mean(aqis),
        avg24: mean(perHorizon["24"]),
        worstName: liveWards[worstIdx]?.name ?? "—",
        worstAqi: aqis[worstIdx] ?? 0,
        unit: "wards",
        count: liveWards.length,
      };
    }
    const aqis = CELLS.map((c) => cellAqi(c, horizon));
    const aqis24 = CELLS.map((c) => c.aqi);
    const mean = (xs: number[]) => Math.round(xs.reduce((a, b) => a + b, 0) / xs.length);
    const worstIdx = aqis.indexOf(Math.max(...aqis));
    return {
      aqis,
      avg: mean(aqis),
      avg24: mean(aqis24),
      worstName: CELLS[worstIdx]?.ward ?? "—",
      worstAqi: aqis[worstIdx] ?? 0,
      unit: "cells",
      count: CELLS.length,
    };
  }, [liveWards, horizon]);

  return (
    <div className="flex flex-wrap items-center gap-x-6 gap-y-3 border-b border-border bg-panel px-5 py-3">
      <HorizonSwitch value={horizon} onChange={onHorizon} />

      <div className="flex items-center gap-3">
        <AqiBall aqi={stats.avg} size={46} />
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[14px] font-bold">Delhi average</span>
            <BandBadge aqi={stats.avg} />
          </div>
          <DeltaTag now={stats.avg} base={stats.avg24} />
        </div>
      </div>

      <div className="hidden items-center gap-2 lg:flex">
        <span className="mono text-[11px] text-text-mute">Worst {stats.unit.slice(0, -1)}</span>
        <span className="text-[12.5px] font-bold">{stats.worstName}</span>
        <span
          className="mono rounded-md px-1.5 py-0.5 text-[11px] font-bold"
          style={{ background: aqiCategory(stats.worstAqi).color, color: aqiCategory(stats.worstAqi).text }}
        >
          {stats.worstAqi}
        </span>
      </div>

      <div className="hidden min-w-[220px] max-w-[340px] flex-1 xl:block">
        <BandDistribution
          aqis={stats.aqis}
          caption={`${stats.count} ${stats.unit} · ${dataKind === "real" ? "real pipeline forecast" : dataKind === "mock" ? "pipeline sample" : "sample scene"} · +${horizon} h`}
        />
      </div>

      <button
        onClick={onToggleMethod}
        aria-expanded={showMethod}
        className={`ml-auto rounded-full border px-3.5 py-1.5 text-[12px] font-semibold transition-colors ${
          showMethod
            ? "border-accent bg-accent text-white"
            : "border-border text-text-dim hover:border-accent-dim hover:text-accent"
        }`}
      >
        {showMethod ? "Hide the method" : "How is this predicted?"}
      </button>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Ward rail — live per-horizon values, re-ranked on switch            */
/* ------------------------------------------------------------------ */

function LiveWardRail({
  horizon,
  liveWards,
  pending,
}: {
  horizon: Horizon;
  liveWards: LiveWard[] | null;
  pending: boolean;
}) {
  const rows = useMemo(() => {
    if (!liveWards) return null;
    return [...liveWards]
      .map((w) => ({ id: w.zone_id, name: w.name, aqi: wardAqiAt(w, horizon) }))
      .sort((a, b) => b.aqi - a.aqi)
      .slice(0, 8);
  }, [liveWards, horizon]);

  return (
    <FilterSection title={rows ? `Worst wards · live · +${horizon} h` : "Ward feed"}>
      {pending && (
        <div className="mono px-2 py-1.5 text-[11px] text-text-mute">Connecting to pipeline…</div>
      )}
      {!pending && !rows && (
        <div className="mono px-2 py-1.5 text-[11px] text-text-mute">
          API unreachable — map shows the bundled sample scene.
        </div>
      )}
      {rows && (
        <ul className="space-y-1">
          {rows.map((w) => {
            const cat = aqiCategory(w.aqi);
            return (
              <li key={w.id} className="flex items-center justify-between gap-2 px-2 py-1">
                <span className="truncate text-[12px] text-text-dim">{w.name}</span>
                <span
                  className="mono shrink-0 rounded-md px-1.5 py-0.5 text-[11px] font-bold"
                  style={{ background: cat.color, color: cat.text }}
                  title={cat.label}
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
      <span className={`mono text-[11px] ${on ? "text-accent" : "text-text-mute"}`}>
        {on ? "● on" : "○ off"}
      </span>
    </button>
  );
}

/* ------------------------------------------------------------------ */
/* Cell detail — forecast trajectory + attribution + actions           */
/* ------------------------------------------------------------------ */

function DetailPanel({
  cell,
  horizon,
  onHorizon,
}: {
  cell: Cell | null;
  horizon: Horizon;
  onHorizon: (h: Horizon) => void;
}) {
  if (!cell) {
    return (
      <div className="border-t border-border bg-bg-secondary px-6 py-8 text-center">
        <div className="mono text-[11px] text-text-mute">
          Select a grid cell to see attribution evidence.
        </div>
      </div>
    );
  }
  const aqiNow = cellAqi(cell, horizon);
  const cat = aqiCategory(aqiNow);
  const values = Object.fromEntries(HORIZONS.map((h) => [h, cellAqi(cell, h)])) as Record<Horizon, number>;
  const enforcement = ENFORCEMENT_TARGETS.filter((e) => e.cellId === cell.id || e.ward === cell.ward);

  return (
    <div className="grid grid-cols-1 gap-px bg-border md:grid-cols-[300px_240px_1fr_300px]">
      {/* AQI + ward */}
      <div className="bg-bg-secondary p-5">
        <div className="mono text-[11px] text-text-mute">
          {cell.wardCode} · Cell {cell.id}
        </div>
        <div className="mt-2 text-xl font-bold">{cell.ward}</div>
        <div className="mt-5 flex items-center gap-3">
          <AqiBall aqi={aqiNow} size={64} />
          <div>
            <BandBadge aqi={aqiNow} />
            <div className="mono mt-1 text-[11px] text-text-mute">CPCB band · +{horizon} h</div>
            <div className="mt-1"><DeltaTag now={aqiNow} base={values["24"]} /></div>
          </div>
        </div>
        <div className="mt-5 border-t border-border pt-3 mono text-[11px] text-text-mute">
          Coord · 28.{600 + cell.y * 8}°N 77.{100 + cell.x * 6}°E
        </div>
      </div>

      {/* 72-hour trajectory — the prediction, visible */}
      <div className="bg-bg-secondary p-5">
        <div className="mono text-[11px] text-text-mute">72-hour forecast</div>
        <div className="mt-2">
          <HorizonTriplet values={values} active={horizon} onSelect={onHorizon} height={72} />
        </div>
        <div className="mono mt-1 text-[11px] text-text-mute">Tap a bar to switch the whole view.</div>
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

        <div className="mt-5">
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
              <li key={e.id}>
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

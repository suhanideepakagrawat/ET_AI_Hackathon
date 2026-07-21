import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { AppShell } from "@/components/AppShell";
import { MapView } from "@/components/MapView";
import { MethodPanel } from "@/components/HowItWorks";
import { aqiCategory, CELLS, ENFORCEMENT_TARGETS, type Cell } from "@/lib/air-data";
import { deploymentQuery } from "@/lib/api";

export const Route = createFileRoute("/enforcement")({
  head: () => ({
    meta: [
      { title: "Enforcement — AirGrid NCR" },
      { name: "description", content: "Live ward-level inspector deployment plan and ranked enforcement targets from the pipeline." },
    ],
  }),
  component: Enforcement,
});

function Enforcement() {
  const dep = useQuery(deploymentQuery);
  const live = dep.isSuccess && dep.data.available && dep.data.items.length > 0;
  const [showMethod, setShowMethod] = useState(false);

  const sorted = [...ENFORCEMENT_TARGETS].sort((a, b) => b.priority - a.priority);
  const [selectedId, setSelectedId] = useState<string>(sorted[0].id);
  const target = sorted.find((t) => t.id === selectedId)!;
  const cell: Cell | undefined = CELLS.find((c) => c.id === target.cellId);

  // Which teams the plan sends out, and how often — the "one glance" summary.
  const teamMix = useMemo(() => {
    if (!live) return [];
    const counts = new Map<string, number>();
    for (const w of dep.data!.items) {
      if (!w.recommended_team) continue;
      counts.set(w.recommended_team, (counts.get(w.recommended_team) ?? 0) + 1);
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [live, dep.data]);

  const maxScore = live
    ? Math.max(...dep.data!.items.map((w) => w.deployment_score ?? 0), 1)
    : 1;

  return (
    <AppShell>
      <div className="grid h-[calc(100vh-57px)] grid-cols-1 md:grid-cols-[1fr_440px]">
        <section className="min-h-0 overflow-hidden border-r border-border">
          <MapView
            selectedId={cell?.id}
            layers={{ enforcement: true, windCorridor: true, fires: false }}
          />
        </section>

        <aside className="overflow-y-auto bg-panel">
          <div className="border-b border-border p-5">
            <div className="chip mb-3">
              {live ? "Ward deployment plan · live pipeline" : "Enforcement queue"}
            </div>
            <h1 className="text-xl font-bold">Where to send inspectors first</h1>
            <p className="mono mt-1 text-[11px] text-text-mute">
              {live
                ? `${dep.data.items.length} wards ranked by deployment score (severity × source × persistence)`
                : `${sorted.length} sample targets · ranked by fused priority score`}
            </p>
            {teamMix.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-1.5">
                {teamMix.map(([team, n]) => (
                  <span key={team} className="mono rounded-full bg-surface-1 px-2.5 py-1 text-[11px] text-text-dim">
                    {team} <b className="text-foreground">×{n}</b>
                  </span>
                ))}
              </div>
            )}
            <button
              onClick={() => setShowMethod((s) => !s)}
              aria-expanded={showMethod}
              className={`mt-3 rounded-full border px-3 py-1.5 text-[12px] font-semibold transition-colors ${
                showMethod
                  ? "border-accent bg-accent text-white"
                  : "border-border text-text-dim hover:border-accent-dim hover:text-accent"
              }`}
            >
              {showMethod ? "Hide the method" : "How is this ranked?"}
            </button>
            {showMethod && (
              <div className="mt-4 border-t border-border pt-4">
                <MethodPanel method="enforcement" compact />
              </div>
            )}
          </div>

          {live ? (
            <ul>
              {dep.data.items.map((w) => {
                const cat = aqiCategory(w.max_aqi ?? 0);
                return (
                  <li key={`${w.rank}-${w.ward_no}`} className="border-b border-border px-5 py-4">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-sm font-semibold">
                        <span className="mono mr-2 text-text-mute">#{w.rank}</span>
                        {w.ward_name}
                      </span>
                      <span
                        className="mono shrink-0 rounded-md px-2 py-0.5 text-[12.5px] font-bold"
                        style={{ background: cat.color, color: cat.text }}
                        title={`Peak forecast AQI · ${cat.label}`}
                      >
                        {Math.round(w.max_aqi ?? 0)}
                      </span>
                    </div>
                    <div className="mono mt-1 flex flex-wrap gap-x-3 text-[11px] text-text-mute">
                      <span>Ward {w.ward_no}</span>
                      <span>·</span>
                      <span>{w.hotspots} hotspot cells</span>
                      <span>·</span>
                      <span>score {Math.round(w.deployment_score ?? 0)}</span>
                    </div>
                    <div
                      className="mt-2 h-1.5 overflow-hidden rounded-full bg-surface-1"
                      role="img"
                      aria-label={`Deployment score ${Math.round(w.deployment_score ?? 0)} of ${Math.round(maxScore)}`}
                    >
                      <div
                        className="h-full rounded-full bg-accent transition-all duration-300"
                        style={{ width: `${((w.deployment_score ?? 0) / maxScore) * 100}%` }}
                      />
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-2 text-[12.5px] text-text-dim">
                      {w.dominant_source && (
                        <span className="rounded-md bg-surface-1 px-2 py-0.5">{w.dominant_source}</span>
                      )}
                      {w.recommended_team && (
                        <span className="rounded-md bg-surface-1 px-2 py-0.5">→ {w.recommended_team}</span>
                      )}
                    </div>
                  </li>
                );
              })}
            </ul>
          ) : (
            <ul>
              {sorted.map((t) => {
                const active = t.id === selectedId;
                return (
                  <li key={t.id}>
                    <button
                      onClick={() => setSelectedId(t.id)}
                      className={`block w-full border-b border-border px-5 py-4 text-left transition-colors ${
                        active ? "bg-surface-1" : "hover:bg-surface-1/40"
                      }`}
                    >
                      <div className="flex items-baseline justify-between">
                        <span className={`text-sm font-semibold ${active ? "text-accent" : "text-foreground"}`}>
                          {t.name}
                        </span>
                        <span className="mono text-xs text-accent">P{t.priority}</span>
                      </div>
                      <div className="mono mt-1 flex gap-3 text-[11px] text-text-mute">
                        <span>{t.type}</span>
                        <span>·</span>
                        <span>{t.ward}</span>
                      </div>
                      <div className="mt-2 text-[12.5px] text-text-dim">{t.action}</div>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </aside>
      </div>
    </AppShell>
  );
}

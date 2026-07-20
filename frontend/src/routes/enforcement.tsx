import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { MapView } from "@/components/MapView";
import { CELLS, ENFORCEMENT_TARGETS, type Cell } from "@/lib/air-data";

export const Route = createFileRoute("/enforcement")({
  head: () => ({
    meta: [
      { title: "Enforcement — AirGrid NCR" },
      { name: "description", content: "Ranked list of priority enforcement targets against registered emission sources across the NCR." },
    ],
  }),
  component: Enforcement,
});

function Enforcement() {
  const sorted = [...ENFORCEMENT_TARGETS].sort((a, b) => b.priority - a.priority);
  const [selectedId, setSelectedId] = useState<string>(sorted[0].id);
  const target = sorted.find((t) => t.id === selectedId)!;
  const cell: Cell | undefined = CELLS.find((c) => c.id === target.cellId);

  return (
    <AppShell>
      <div className="grid h-[calc(100vh-57px)] grid-cols-1 md:grid-cols-[1fr_420px]">
        <section className="min-h-0 overflow-hidden border-r border-border">
          <MapView
            selectedId={cell?.id}
            layers={{ enforcement: true, windCorridor: true, fires: false }}
          />
        </section>

        <aside className="overflow-y-auto bg-bg-secondary">
          <div className="border-b border-border p-5">
            <div className="chip mb-3">Enforcement queue</div>
            <h1 className="font-display text-xl">Priority actions · today</h1>
            <p className="mono mt-1 text-[11px] uppercase tracking-wider text-text-mute">
              {sorted.length} targets · ranked by fused priority score
            </p>
          </div>
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
                      <span className={`font-display text-sm ${active ? "text-accent" : "text-foreground"}`}>
                        {t.name}
                      </span>
                      <span className="mono text-xs text-accent">P{t.priority}</span>
                    </div>
                    <div className="mono mt-1 flex gap-3 text-[10px] uppercase tracking-wider text-text-mute">
                      <span>{t.type}</span>
                      <span>·</span>
                      <span>{t.ward}</span>
                    </div>
                    <div className="mt-2 text-[12px] text-text-dim">{t.action}</div>
                  </button>
                </li>
              );
            })}
          </ul>
        </aside>
      </div>
    </AppShell>
  );
}

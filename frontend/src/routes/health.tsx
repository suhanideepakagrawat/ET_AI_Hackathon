import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { MapView } from "@/components/MapView";
import { CELLS, VULNERABLE_SITES, aqiCategory } from "@/lib/air-data";

export const Route = createFileRoute("/health")({
  head: () => ({
    meta: [
      { title: "Health advisory — AirGrid NCR" },
      { name: "description", content: "Vulnerable-population overlay and multilingual health advisories for NCR forecast severity." },
    ],
  }),
  component: Health,
});

function Health() {
  // Match sites to their cell AQI
  const rows = VULNERABLE_SITES.map((v) => {
    const cell = CELLS.find((c) => c.x === v.x && c.y === v.y);
    const aqi = cell?.aqi ?? 0;
    return { ...v, aqi, cat: aqiCategory(aqi) };
  }).sort((a, b) => b.aqi - a.aqi);

  return (
    <AppShell>
      <div className="grid h-[calc(100vh-57px)] grid-cols-1 md:grid-cols-[1fr_460px]">
        <section className="min-h-0 overflow-hidden border-r border-border">
          <MapView layers={{ vulnerable: true, windCorridor: false, fires: false }} />
        </section>

        <aside className="overflow-y-auto bg-bg-secondary">
          <div className="border-b border-border p-5">
            <div className="chip mb-3">Health advisory</div>
            <h1 className="font-display text-xl">Who is affected here</h1>
            <p className="mt-2 text-sm text-text-dim">
              Sensitive sites (schools, hospitals, elderly care) sorted by forecast severity in
              their cell. Advisories below apply to the group at that site, not a generic public.
            </p>
          </div>

          <ul>
            {rows.map((r) => (
              <li key={r.id} className="border-b border-border p-5">
                <div className="flex items-baseline justify-between">
                  <span className="font-display text-sm">{r.name}</span>
                  <span className="mono text-lg" style={{ color: r.cat.color }}>{r.aqi}</span>
                </div>
                <div className="mono mt-1 flex items-center gap-3 text-[10px] uppercase tracking-wider text-text-mute">
                  <span>{r.type}</span>
                  <span>·</span>
                  <span>{r.exposed} exposed</span>
                  <span>·</span>
                  <span style={{ color: r.cat.color }}>{r.cat.label}</span>
                </div>
                <div className="mt-3 border-l border-accent-dim pl-3 text-[13px] text-text-dim">
                  {advisoryFor(r.type, r.aqi)}
                </div>
                <div className="mono mt-2 text-[10px] uppercase tracking-wider text-text-mute">
                  हिंदी · {advisoryHi(r.type, r.aqi)}
                </div>
              </li>
            ))}
          </ul>
        </aside>
      </div>
    </AppShell>
  );
}

function advisoryFor(type: string, aqi: number): string {
  if (aqi > 300) {
    if (type === "School") return "Suspend outdoor activities. Move PE indoors. Distribute N95 masks at gate.";
    if (type === "Hospital") return "Elevate respiratory triage capacity. Pre-position nebulisers in OPD.";
    return "Restrict residents to indoor areas with sealed windows. Run HEPA filtration continuously.";
  }
  if (aqi > 200) {
    if (type === "School") return "Limit outdoor activities to under 30 minutes. Reschedule sports to early morning.";
    if (type === "Hospital") return "Advise vulnerable outpatients to defer non-urgent visits.";
    return "Limit outdoor time to essential trips. Windows closed 06:00–10:00.";
  }
  return "Normal activity acceptable. Monitor next forecast run.";
}

function advisoryHi(type: string, aqi: number): string {
  if (aqi > 300) return "बाहरी गतिविधियाँ रोकें · मास्क अनिवार्य";
  if (aqi > 200) return "बाहरी समय सीमित करें";
  return "सामान्य गतिविधि ठीक है";
}

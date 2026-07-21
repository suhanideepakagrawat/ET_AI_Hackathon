import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { AppShell } from "@/components/AppShell";
import { MethodPanel } from "@/components/HowItWorks";
import { CELLS, VULNERABLE_SITES, aqiCategory } from "@/lib/air-data";
import { CITIZEN_APP_URL, wardsQuery } from "@/lib/api";

export const Route = createFileRoute("/health")({
  head: () => ({
    meta: [
      { title: "Citizen advisory — AirGrid NCR" },
      { name: "description", content: "Vulnerable-population overlay and the multilingual VayuMitra citizen advisory, live from the deployed pipeline." },
    ],
  }),
  component: Health,
});

// Site type -> the advisory persona it maps to in VayuMitra.
const PERSONA_FOR: Record<string, string> = {
  School: "Child / school persona",
  Hospital: "Asthma & heart-patient persona",
  "Elderly care": "Elderly persona",
};

function Health() {
  const live = useQuery(wardsQuery());
  const [showMethod, setShowMethod] = useState(false);

  // Match sites to their cell AQI (sample scene), worst first.
  const rows = VULNERABLE_SITES.map((v) => {
    const cell = CELLS.find((c) => c.x === v.x && c.y === v.y);
    const aqi = cell?.aqi ?? 0;
    return { ...v, aqi, cat: aqiCategory(aqi) };
  }).sort((a, b) => b.aqi - a.aqi);

  return (
    <AppShell>
      <div className="grid h-[calc(100vh-57px)] grid-cols-1 md:grid-cols-[1fr_440px]">
        {/* VayuMitra — the real deployed citizen product, embedded live */}
        <section className="relative min-h-0 overflow-hidden border-r border-border bg-surface-1">
          <div className="flex items-center justify-between border-b border-border bg-panel px-5 py-3">
            <div>
              <h1 className="text-base font-bold">VayuMitra — citizen advisory</h1>
              <p className="text-[12px] text-text-dim">
                The live multilingual assistant (English · हिन्दी, voice-enabled), embedded from the deployed service.
              </p>
            </div>
            <a
              href={CITIZEN_APP_URL}
              target="_blank"
              rel="noopener"
              className="shrink-0 rounded-full bg-accent px-4 py-2 text-[12px] font-semibold text-white hover:bg-[#064a42]"
            >
              Open full app →
            </a>
          </div>
          <iframe
            src={CITIZEN_APP_URL}
            title="VayuMitra citizen advisory (live)"
            className="h-[calc(100%-61px)] w-full border-0 bg-white"
            loading="lazy"
            allow="microphone; autoplay"
          />
        </section>

        {/* Vulnerable sites, persona-mapped */}
        <aside className="overflow-y-auto bg-panel">
          <div className="border-b border-border p-5">
            <div className="chip mb-3">Sensitive sites</div>
            <h2 className="text-lg font-bold">Who is affected here</h2>
            <p className="mt-2 text-sm text-text-dim">
              Schools, hospitals and elderly-care sites sorted by forecast severity in their cell
              (sample scene). Each maps to a VayuMitra persona, so the advisory speaks to that
              group — not a generic public.
            </p>
            {live.isSuccess && (
              <p className="mono mt-2 text-[11px] text-text-mute">
                Live ward feed connected · {live.data.count} zones · worst now:{" "}
                {live.data.wards[0]?.name} (AQI {live.data.wards[0]?.aqi})
              </p>
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
              {showMethod ? "Hide the method" : "How is the advice made?"}
            </button>
            {showMethod && (
              <div className="mt-4 border-t border-border pt-4">
                <MethodPanel method="advisory" compact />
              </div>
            )}
          </div>

          <ul>
            {rows.map((r) => (
              <li key={r.id} className="border-b border-border p-5">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-semibold">{r.name}</span>
                  <span
                    className="mono shrink-0 rounded-md px-2 py-0.5 text-[12px] font-bold"
                    style={{ background: r.cat.color, color: r.cat.text }}
                  >
                    {r.aqi}
                  </span>
                </div>
                <div className="mono mt-1 flex flex-wrap items-center gap-x-3 text-[11px] text-text-mute">
                  <span>{r.type}</span>
                  <span>·</span>
                  <span>{r.exposed.toLocaleString()} people exposed</span>
                  <span>·</span>
                  <span>{r.cat.label}</span>
                </div>
                <div className="mt-3 rounded-md bg-surface-1 px-3 py-2 text-[14px] text-text-dim">
                  {advisoryFor(r.type, r.aqi)}
                </div>
                <div className="mono mt-2 text-[11px] text-text-mute">
                  {PERSONA_FOR[r.type] ?? "General persona"} · हिंदी: {advisoryHi(r.aqi)}
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
    if (type === "School") return "Suspend outdoor activities. Move PE indoors. Distribute N95 masks at the gate.";
    if (type === "Hospital") return "Elevate respiratory triage capacity. Pre-position nebulisers in OPD.";
    return "Keep residents indoors with sealed windows. Run HEPA filtration continuously.";
  }
  if (aqi > 200) {
    if (type === "School") return "Limit outdoor activities to under 30 minutes. Reschedule sports to early morning.";
    if (type === "Hospital") return "Advise vulnerable outpatients to defer non-urgent visits.";
    return "Limit outdoor time to essential trips. Windows closed 06:00–10:00.";
  }
  return "Normal activity acceptable. Monitor the next forecast run.";
}

function advisoryHi(aqi: number): string {
  if (aqi > 300) return "बाहरी गतिविधियाँ रोकें · मास्क अनिवार्य";
  if (aqi > 200) return "बाहरी समय सीमित करें";
  return "सामान्य गतिविधि ठीक है";
}

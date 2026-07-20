import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/AppShell";
import { CELLS, SOURCE_COLORS, SOURCE_LABELS, type SourceKey } from "@/lib/air-data";

export const Route = createFileRoute("/attribution")({
  head: () => ({
    meta: [
      { title: "Attribution — AirGrid NCR" },
      { name: "description", content: "City-wide source attribution trends across Delhi-NCR grid cells." },
    ],
  }),
  component: Attribution,
});

function Attribution() {
  const totals: Record<SourceKey, number> = { traffic: 0, industry: 0, construction: 0, burning: 0 };
  CELLS.forEach((c) => {
    (Object.keys(totals) as SourceKey[]).forEach((k) => (totals[k] += c.attribution[k] * c.aqi));
  });
  const sum = Object.values(totals).reduce((a, b) => a + b, 0);
  const shares = (Object.keys(totals) as SourceKey[]).map((k) => ({
    k,
    pct: totals[k] / sum,
  }));

  // Fake 24h series per source
  const hours = 24;
  const series: Record<SourceKey, number[]> = {
    traffic: Array.from({ length: hours }, (_, i) => 40 + Math.sin(i / 3) * 12 + (i > 8 && i < 20 ? 20 : 0)),
    industry: Array.from({ length: hours }, (_, i) => 30 + Math.cos(i / 4) * 8 + (i < 8 ? 15 : 0)),
    construction: Array.from({ length: hours }, (_, i) => 20 + Math.sin(i / 5) * 6 + (i > 6 && i < 18 ? 12 : 0)),
    burning: Array.from({ length: hours }, (_, i) => 55 + Math.sin((i + 4) / 6) * 20 + (i < 10 ? 25 : -10)),
  };

  return (
    <AppShell>
      <div className="mx-auto max-w-6xl px-6 py-8">
        <div className="chip mb-3">Attribution · city-wide</div>
        <h1 className="font-display text-3xl">Source contribution across the NCR grid</h1>
        <p className="mt-2 max-w-2xl text-sm text-text-dim">
          Aggregated share of forecast AQI by source over the current run. Numbers weighted
          by cell AQI so heavily-loaded cells count more than clean ones.
        </p>

        <div className="mt-8 grid gap-6 md:grid-cols-[1fr_1fr]">
          <div className="panel p-6">
            <div className="mono text-[11px] text-text-mute">Contribution mix</div>
            <div className="mt-4 flex h-4 overflow-hidden border border-border">
              {shares.map((s) => (
                <div key={s.k} style={{ width: `${s.pct * 100}%`, background: SOURCE_COLORS[s.k] }} title={`${SOURCE_LABELS[s.k]} · ${Math.round(s.pct * 100)}%`} />
              ))}
            </div>
            <ul className="mono mt-6 space-y-2 text-sm">
              {shares.map((s) => (
                <li key={s.k} className="flex items-center justify-between border-b border-border pb-2 last:border-0">
                  <span className="flex items-center gap-2 text-text-dim">
                    <span className="h-2 w-2" style={{ background: SOURCE_COLORS[s.k] }} />
                    {SOURCE_LABELS[s.k]}
                  </span>
                  <span className="text-foreground">{(s.pct * 100).toFixed(1)}%</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="panel p-6">
            <div className="mono text-[11px] text-text-mute">24-hour source load · μg/m³ equiv</div>
            <TrendChart series={series} />
          </div>
        </div>

        <div className="panel mt-6 p-6">
          <div className="mono text-[11px] text-text-mute">Top cells by AQI · +24h</div>
          <table className="mono mt-4 w-full text-sm">
            <thead className="mono text-[11px] text-text-mute">
              <tr className="border-b border-border">
                <th className="py-2 text-left">Cell</th>
                <th className="text-left">Ward</th>
                <th className="text-right">AQI</th>
                <th className="text-left pl-6">Dominant</th>
                <th className="text-right">Confidence</th>
              </tr>
            </thead>
            <tbody>
              {[...CELLS].sort((a, b) => b.aqi - a.aqi).slice(0, 10).map((c) => (
                <tr key={c.id} className="border-b border-border/50 last:border-0">
                  <td className="py-2 text-text-dim">{c.id}</td>
                  <td className="text-text-dim">{c.ward}</td>
                  <td className="text-right text-foreground">{c.aqi}</td>
                  <td className="pl-6">
                    <span className="flex items-center gap-2 text-text-dim">
                      <span className="h-1.5 w-1.5" style={{ background: SOURCE_COLORS[c.dominantSource] }} />
                      {SOURCE_LABELS[c.dominantSource]}
                    </span>
                  </td>
                  <td className="text-right text-accent">{Math.round(c.confidence * 100)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AppShell>
  );
}

function TrendChart({ series }: { series: Record<SourceKey, number[]> }) {
  const width = 520;
  const height = 220;
  const hours = 24;
  const max = Math.max(...(Object.values(series).flat()));
  const x = (i: number) => (i / (hours - 1)) * (width - 20) + 10;
  const y = (v: number) => height - 20 - (v / max) * (height - 40);

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="mt-4 h-56 w-full">
      {[0, 0.25, 0.5, 0.75, 1].map((t) => (
        <line key={t} x1={10} x2={width - 10} y1={height - 20 - t * (height - 40)} y2={height - 20 - t * (height - 40)} stroke="var(--accent-dim)" strokeOpacity="0.12" />
      ))}
      {(Object.keys(series) as SourceKey[]).map((k) => {
        const pts = series[k].map((v, i) => `${x(i)},${y(v)}`).join(" ");
        return <polyline key={k} points={pts} fill="none" stroke={`var(--source-${k})`} strokeWidth="1.5" />;
      })}
      {Array.from({ length: 5 }).map((_, i) => {
        const h = (i * 6) % 24;
        return (
          <text key={i} x={x(h)} y={height - 4} fontSize="9" fill="var(--text-mute)" className="mono" textAnchor="middle">
            {String(h).padStart(2, "0")}:00
          </text>
        );
      })}
    </svg>
  );
}

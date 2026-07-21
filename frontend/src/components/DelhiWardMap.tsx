// The real Delhi ward map — actual MCD boundaries from the pipeline's
// shapefile, pre-projected to SVG paths at build time (src/data/delhi-wards.json).
// Wards are filled with their CPCB band color at the active horizon, so
// switching +24/+48/+72 recolors the actual city. Click a ward to focus it.

import { useMemo, useState } from "react";
import WARD_GEO from "@/data/delhi-wards.json";
import { aqiCategory, type Horizon } from "@/lib/air-data";
import { wardAqiAt, type LiveWard } from "@/lib/api";

type WardShape = { id: string; name: string; d: string; cx: number; cy: number };

const GEO = WARD_GEO as { w: number; h: number; wards: WardShape[] };

export function DelhiWardMap({
  liveWards,
  horizon,
  selectedId,
  onPick,
  badges,
  ambient = false,
  className = "",
}: {
  liveWards: LiveWard[] | null;
  horizon: Horizon;
  selectedId?: string | null;
  onPick?: (w: LiveWard) => void;
  /** Small numbered markers, e.g. deployment ranks: [{id: "W133", label: "1"}] */
  badges?: { id: string; label: string }[];
  ambient?: boolean;
  className?: string;
}) {
  const [hoverId, setHoverId] = useState<string | null>(null);

  const byId = useMemo(() => {
    const m = new Map<string, LiveWard>();
    for (const w of liveWards ?? []) m.set(String(w.zone_id), w);
    return m;
  }, [liveWards]);

  const badgeById = useMemo(() => {
    const m = new Map<string, string>();
    for (const b of badges ?? []) m.set(b.id, b.label);
    return m;
  }, [badges]);

  const hovered = hoverId ? byId.get(hoverId) : null;
  const hoveredShape = hoverId ? GEO.wards.find((s) => s.id === hoverId) : null;

  return (
    <div className={`relative h-full w-full ${className}`}>
      <svg
        viewBox={`0 0 ${GEO.w} ${GEO.h}`}
        preserveAspectRatio="xMidYMid meet"
        className="h-full w-full"
        role={ambient ? "img" : "group"}
        aria-label="Delhi ward map, colored by forecast AQI"
      >
        {GEO.wards.map((s) => {
          const live = byId.get(s.id);
          const isSel = selectedId === s.id;
          const isHover = hoverId === s.id;
          const cat = live ? aqiCategory(wardAqiAt(live, horizon)) : null;
          return (
            <path
              key={s.id + s.name}
              d={s.d}
              fill={cat ? cat.color : "var(--surface-2)"}
              fillOpacity={cat ? (ambient ? 0.5 : isHover || isSel ? 0.95 : 0.72) : 0.45}
              stroke={isSel ? "var(--accent)" : isHover ? "var(--accent-dim)" : "var(--panel)"}
              strokeWidth={isSel ? 2.5 : isHover ? 1.8 : 0.7}
              style={{ transition: "fill 0.3s ease-out, fill-opacity 0.2s ease-out", cursor: !ambient && live && onPick ? "pointer" : "default" }}
              onMouseEnter={() => !ambient && setHoverId(s.id)}
              onMouseLeave={() => !ambient && setHoverId(null)}
              onClick={() => !ambient && live && onPick?.(live)}
            >
              {!ambient && <title>{live ? `${live.name} · AQI ${wardAqiAt(live, horizon)}` : `${s.name} · outside the forecast set`}</title>}
            </path>
          );
        })}

        {/* Selected ward re-drawn on top so its outline is never underlapped */}
        {selectedId &&
          (() => {
            const s = GEO.wards.find((x) => x.id === selectedId);
            if (!s) return null;
            return <path d={s.d} fill="none" stroke="var(--accent)" strokeWidth="2.5" />;
          })()}

        {/* Numbered markers (deployment ranks) */}
        {(badges ?? []).map((b) => {
          const s = GEO.wards.find((x) => x.id === b.id);
          if (!s) return null;
          return (
            <g key={`badge-${b.id}`} pointerEvents="none">
              <circle cx={s.cx} cy={s.cy} r="11" fill="var(--accent)" stroke="var(--panel)" strokeWidth="1.5" />
              <text x={s.cx} y={s.cy + 3.5} textAnchor="middle" fontSize="11" fontWeight="700" fill="#ffffff" className="mono">
                {b.label}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Hover card — name, AQI, band, dominant source */}
      {!ambient && hovered && hoveredShape && (
        <div
          className="pointer-events-none absolute z-10 -translate-x-1/2 rounded-md border border-border bg-panel px-3 py-2 shadow-[0_2px_8px_rgba(9,20,28,0.12)]"
          style={{
            left: `${(hoveredShape.cx / GEO.w) * 100}%`,
            top: `calc(${(hoveredShape.cy / GEO.h) * 100}% - 56px)`,
          }}
        >
          <div className="flex items-center gap-2 whitespace-nowrap">
            <span className="text-[12.5px] font-bold">{hovered.name}</span>
            <span
              className="mono rounded-md px-1.5 py-0.5 text-[11px] font-bold"
              style={{
                background: aqiCategory(wardAqiAt(hovered, horizon)).color,
                color: aqiCategory(wardAqiAt(hovered, horizon)).text,
              }}
            >
              {wardAqiAt(hovered, horizon)}
            </span>
          </div>
          <div className="mono mt-0.5 whitespace-nowrap text-[11px] text-text-mute">
            {aqiCategory(wardAqiAt(hovered, horizon)).label}
            {hovered.dominant_source ? ` · ${hovered.dominant_source}` : ""}
          </div>
        </div>
      )}
    </div>
  );
}

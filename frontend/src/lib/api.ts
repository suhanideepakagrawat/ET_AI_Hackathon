// Live-data bridge to the deployed PS5 backend (FastAPI on Render).
// Every fetcher degrades gracefully: if the API is unreachable the UI keeps
// rendering the bundled sample scene and says so honestly ("sample" badge),
// so the demo never breaks (RULE 1 of the implementation plan).

export const API_BASE: string =
  (import.meta as any).env?.VITE_API_URL?.replace(/\/$/, "") ||
  "https://vayumitra-advisory.onrender.com";

export const CITIZEN_APP_URL = API_BASE; // the VayuMitra chat is served at "/"

async function get<T>(path: string, timeoutMs = 8000): Promise<T> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const r = await fetch(`${API_BASE}${path}`, { signal: ctrl.signal });
    if (!r.ok) throw new Error(`${path} -> ${r.status}`);
    return (await r.json()) as T;
  } finally {
    clearTimeout(t);
  }
}

export type LiveWard = {
  zone_id: string;
  name: string;
  lat: number;
  lon: number;
  aqi: number;
  band: string;
  band_label: string;
  color: string;
  dominant_source: string | null;
  dominant_source_pct: number;
  confidence: number | null;
};

export type WardsResponse = {
  city: string;
  data_kind: "real" | "mock";
  count: number;
  wards: LiveWard[];
};

export type CitySummary = {
  city: string;
  name: string;
  zones: number;
  avg_aqi: number;
  max_aqi: number;
  worst_zone: { name: string; aqi: number };
  source_mix: { traffic: number; industry: number; construction: number };
  dominant_source: string | null;
  intervention: { avg_aqi_before: number; avg_aqi_after: number; reduction_pct: number; note: string };
  data_kind: "real" | "mock";
};

export const fetchHealth = () => get<{ status: string; llm: string; voice: string }>("/health", 5000);
export const fetchWards = (city?: string) =>
  get<WardsResponse>(`/wards${city ? `?city=${encodeURIComponent(city)}` : ""}`);
export const fetchCompare = () => get<{ cities: CitySummary[]; note: string }>("/compare");

// Query configs shared by routes (react-query is already in the root context).
export const wardsQuery = (city?: string) => ({
  queryKey: ["wards", city ?? "default"],
  queryFn: () => fetchWards(city),
  staleTime: 5 * 60_000,
  retry: 1,
});

export const healthQuery = {
  queryKey: ["api-health"],
  queryFn: fetchHealth,
  staleTime: 60_000,
  retry: 0,
};

export const compareQuery = {
  queryKey: ["compare"],
  queryFn: fetchCompare,
  staleTime: 5 * 60_000,
  retry: 1,
};

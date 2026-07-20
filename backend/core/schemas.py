from pydantic import BaseModel
from typing import Optional

class ForecastResponse(BaseModel):
    cell_id: int
    lat: Optional[float] = None
    lon: Optional[float] = None
    is_estimated: Optional[int] = None
    nearest_station: Optional[str] = None
    nearest_dist_km: Optional[float] = None
    source_timestamp: Optional[str] = None
    target_timestamp: Optional[str] = None
    horizon_hours: Optional[int] = None
    forecast_aqi: Optional[float] = None
    source_aqi: Optional[float] = None

class AttributionResponse(BaseModel):
    cell_id: int
    lat: Optional[float] = None
    lon: Optional[float] = None
    horizon_hours: Optional[int] = None
    forecast_aqi: Optional[float] = None
    aqi_severity: Optional[str] = None
    dominant_source: Optional[str] = None
    dominant_source_pct: Optional[float] = None
    traffic_pct: Optional[float] = None
    industry_pct: Optional[float] = None
    construction_pct: Optional[float] = None
    confidence: Optional[float] = None
    confidence_label: Optional[str] = None
    attribution_status: Optional[str] = None
    evidence_summary: Optional[str] = None

class EnforcementTarget(BaseModel):
    cell_id: int
    lat: Optional[float] = None
    lon: Optional[float] = None
    horizon_hours: Optional[int] = None
    forecast_aqi: Optional[float] = None
    severity: Optional[str] = None
    priority_band: Optional[str] = None
    dominant_source: Optional[str] = None
    confidence: Optional[float] = None
    priority_score: Optional[float] = None
    recommended_action: Optional[str] = None
    evidence: Optional[str] = None
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from backend.core.schemas import ForecastResponse, AttributionResponse, EnforcementTarget
from backend.services.data_service import get_forecasts, get_attribution, get_enforcement

router = APIRouter()

@router.get("/forecasts", response_model=List[ForecastResponse], tags=["Forecasting"])
async def fetch_forecasts(
    cell_id: Optional[int] = Query(None, description="Filter by Grid Cell ID"),
    horizon_hours: Optional[int] = Query(None, description="Filter by horizon (24, 48, 72)")
):
    """Retrieve 24h/48h/72h AQI forecasts."""
    try:
        return get_forecasts(cell_id, horizon_hours)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/attribution", response_model=List[AttributionResponse], tags=["Attribution"])
async def fetch_attribution(
    cell_id: Optional[int] = Query(None, description="Filter by Grid Cell ID")
):
    """Retrieve geospatial source attribution scores and dominance."""
    try:
        return get_attribution(cell_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/enforcement", response_model=List[EnforcementTarget], tags=["Enforcement"])
async def fetch_enforcement(
    limit: int = Query(20, description="Limit the number of targets returned"),
    priority_band: Optional[str] = Query(None, description="Filter by priority band (e.g., CRITICAL, HIGH)")
):
    """Retrieve ranked enforcement targets and recommended actions based on priority scores."""
    try:
        return get_enforcement(limit, priority_band)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
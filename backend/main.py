import os
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any

# ==========================================
# 1. Application Initialization & Config
# ==========================================

app = FastAPI(
    title="Urban Air Quality Intelligence API",
    description="Backend services for AQI Forecasting, Source Attribution, and Enforcement Prioritization.",
    version="1.0.0"
)

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Resolve paths to the data directory (Assumes backend/main.py structure)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

# ==========================================
# 2. Data Loading Utilities
# ==========================================

def load_csv_data(filename: str) -> pd.DataFrame:
    """
    Utility function to load CSV data into a Pandas DataFrame.
    Returns an empty DataFrame if the file does not exist.
    """
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file {filename} not found at {filepath}")
    return pd.read_csv(filepath)

def filter_dataframe(df: pd.DataFrame, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Applies key-value filters to a DataFrame and returns a list of dictionaries.
    """
    for key, value in filters.items():
        if value is not None and key in df.columns:
            df = df[df[key] == value]
    
    # Replace NaNs with None for valid JSON serialization
    df = df.where(pd.notnull(df), None)
    return df.to_dict(orient="records")

# ==========================================
# 3. API Endpoints
# ==========================================

@app.get("/health", tags=["System"])
async def health_check():
    """Standard health check endpoint."""
    return {"status": "Operational", "service": "AQI Predictor Backend"}


@app.get("/api/v1/forecasts", tags=["Forecasting"])
async def get_forecasts(
    cell_id: Optional[int] = Query(None, description="Filter by specific Grid Cell ID"),
    horizon_hours: Optional[int] = Query(None, description="Filter by horizon (24, 48, or 72)")
):
    """
    Retrieve 24h/48h/72h AQI forecasts.
    """
    try:
        df = load_csv_data("future_aqi_forecast.csv")
        filters = {"cell_id": cell_id, "horizon_hours": horizon_hours}
        results = filter_dataframe(df, filters)
        return {"count": len(results), "data": results}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/attribution", tags=["Attribution"])
async def get_source_attribution(
    cell_id: Optional[int] = Query(None, description="Filter by specific Grid Cell ID")
):
    """
    Retrieve geospatial source attribution scores and dominance.
    """
    try:
        df = load_csv_data("source_attribution.csv")
        filters = {"cell_id": cell_id}
        results = filter_dataframe(df, filters)
        return {"count": len(results), "data": results}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/enforcement", tags=["Enforcement"])
async def get_enforcement_priorities(
    limit: int = Query(20, description="Limit the number of top targets returned"),
    priority_band: Optional[str] = Query(None, description="Filter by priority band (e.g., CRITICAL, HIGH)")
):
    """
    Retrieve ranked enforcement targets and recommended actions based on priority scores.
    """
    try:
        df = load_csv_data("enforcement_priorities.csv")
        
        if priority_band and "priority_band" in df.columns:
            df = df[df["priority_band"].str.upper() == priority_band.upper()]
            
        # Ensure it's sorted by priority_score descending
        if "priority_score" in df.columns:
            df = df.sort_values("priority_score", ascending=False)
            
        df = df.head(limit)
        
        # Replace NaNs with None for valid JSON serialization
        df = df.where(pd.notnull(df), None)
        results = df.to_dict(orient="records")
        
        return {"count": len(results), "data": results}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
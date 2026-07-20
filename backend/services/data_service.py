import os
import pandas as pd
import numpy as np
from typing import List, Dict, Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, "data")

def load_csv(filename: str) -> pd.DataFrame:
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Data file {filename} not found at {filepath}")
    return pd.read_csv(filepath)

def get_forecasts(cell_id: int = None, horizon: int = None, limit: int = 50) -> List[Dict[str, Any]]:
    df = load_csv("future_aqi_forecast.csv")
    if cell_id is not None:
        df = df[df['cell_id'] == cell_id]
    if horizon is not None:
        df = df[df['horizon_hours'] == horizon]
    
    df = df.head(limit)
    df = df.replace([np.nan, np.inf, -np.inf], None)
    return df.to_dict(orient="records")

def get_attribution(cell_id: int = None, limit: int = 50) -> List[Dict[str, Any]]:
    df = load_csv("source_attribution.csv")
    if cell_id is not None:
        df = df[df['cell_id'] == cell_id]  # Filter first!
        
    df = df.head(limit)                   # Then apply limit
    df = df.replace([np.nan, np.inf, -np.inf], None)
    return df.to_dict(orient="records")

def get_enforcement(limit: int = 20, priority_band: str = None) -> List[Dict[str, Any]]:
    df = load_csv("enforcement_priorities.csv")
    if priority_band and "priority_band" in df.columns:
        df = df[df["priority_band"].str.upper() == priority_band.upper()]
    if "priority_score" in df.columns:
        df = df.sort_values("priority_score", ascending=False)
        
    df = df.head(limit)
    df = df.replace([np.nan, np.inf, -np.inf], None)
    return df.to_dict(orient="records")
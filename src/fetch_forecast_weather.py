"""
fetch_forecast_weather.py
--------------------------
Fetches the next 72h of hourly forecast weather for Delhi from
Open-Meteo's FORECAST endpoint (not archive — this is the live
inference piece the train_forecaster.py docstring explicitly requires).

WHY THIS EXISTS
---------------
train_forecaster.py uses `target_wind_speed`, `target_temp`, etc. —
weather AT the future timestamp t+horizon. During training, that was
historical-actual weather (already happened, from Open-Meteo archive).
At live inference the future hasn't happened yet, so you MUST replace
it with a real forecast. This script fetches exactly that.

No API key required — Open-Meteo forecast is free and unauthenticated.
One HTTP request covers all 72 hours for the whole city (city-level
weather, same as what was used during training).

OUTPUT
------
data/forecast_weather.csv
    timestamp, target_temp, target_humidity, target_wind_speed,
    target_wind_dir

Column names match what train_forecaster.py's FEATURE_COLS_BASE
expects at inference time — rename the historical columns to these
before calling model.predict().

USAGE
-----
Standalone (writes CSV):
    python3 src/fetch_forecast_weather.py

As a module (returns DataFrame directly):
    from fetch_forecast_weather import get_forecast_weather
    fw = get_forecast_weather()   # DataFrame, 72 rows, one per hour
"""

import os
import requests
import pandas as pd
from datetime import datetime, timezone

CITY = {
    "name":       "Delhi",
    "lat_center": 28.65,
    "lon_center": 77.10,
}

# Open-Meteo forecast endpoint — free, no key, up to 16 days ahead
OPENMETEO_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
FORECAST_HOURS = 96   # 24h buffer beyond the 72h model horizon — see inference note

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)
OUT_PATH = os.path.join(DATA_DIR, "forecast_weather.csv")


def get_forecast_weather(hours: int = FORECAST_HOURS) -> pd.DataFrame:
    """
    Fetch the next N hourly weather forecasts from Open-Meteo.

    Uses forecast_hours (not forecast_days + head()) so the series
    always starts from NOW, never from the beginning of the local day.
    Running at 7 PM with forecast_days=4 + head(72) would include
    hours that already passed — forecast_hours avoids that entirely.

    Returns a DataFrame with columns:
        timestamp          — hourly Asia/Kolkata
        target_temp        — °C
        target_humidity    — %
        target_wind_speed  — km/h  (explicit wind_speed_unit="kmh")
        target_wind_dir    — degrees (0–360)
        fetched_at         — ISO-8601 UTC, for staleness checks
    """
    params = {
        "latitude":        CITY["lat_center"],
        "longitude":       CITY["lon_center"],
        "hourly": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "wind_speed_10m,"
            "wind_direction_10m"
        ),
        "timezone":        "Asia/Kolkata",
        "forecast_hours":  hours,          # exact hours from now, not rounded days
        "wind_speed_unit": "kmh",          # match Open-Meteo archive units used during training
    }
    resp = requests.get(OPENMETEO_FORECAST_URL, params=params, timeout=30)
    resp.raise_for_status()

    payload = resp.json()
    if "hourly" not in payload:
        raise RuntimeError(f"Open-Meteo response missing 'hourly': {payload}")
    h = payload["hourly"]

    df = pd.DataFrame({
        "timestamp":        pd.to_datetime(h["time"]),
        "target_temp":      pd.to_numeric(h["temperature_2m"],      errors="coerce"),
        "target_humidity":  pd.to_numeric(h["relative_humidity_2m"], errors="coerce"),
        "target_wind_speed": pd.to_numeric(h["wind_speed_10m"],     errors="coerce"),
        "target_wind_dir":  pd.to_numeric(h["wind_direction_10m"],  errors="coerce"),
    })

    df = df.sort_values("timestamp").reset_index(drop=True)

    if df.empty:
        raise RuntimeError("Open-Meteo returned zero forecast rows.")

    weather_cols = ["target_temp", "target_humidity", "target_wind_speed", "target_wind_dir"]
    missing = df[weather_cols].isna().sum()
    if missing.any():
        print("  [WARN] Missing forecast values:\n" + missing[missing > 0].to_string())

    df["fetched_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return df


def check_staleness(df: pd.DataFrame, max_age_hours: float = 6.0):
    """
    Warn if the cached forecast is older than max_age_hours.
    Open-Meteo updates forecasts every hour — re-fetching every 6h at
    inference time is a reasonable balance between freshness and API calls.
    """
    if "fetched_at" not in df.columns or df.empty:
        return
    fetched = pd.to_datetime(df["fetched_at"].iloc[0], utc=True)
    age_hours = (datetime.now(timezone.utc) - fetched).total_seconds() / 3600
    if age_hours > max_age_hours:
        print(f"  [WARN] Forecast weather is {age_hours:.1f}h old (fetched at {fetched}). "
              f"Re-run fetch_forecast_weather.py to refresh — "
              f"stale forecasts quietly degrade inference accuracy.")
    else:
        print(f"  [OK] Forecast weather is {age_hours:.1f}h old (within {max_age_hours}h threshold).")


def load_or_fetch(max_age_hours: float = 6.0) -> pd.DataFrame:
    """
    Load cached forecast if it exists, is structurally valid, and is fresh.
    Re-fetches if the cache is missing, corrupt, old-format, or stale.
    Use this in your inference pipeline instead of always calling
    get_forecast_weather() directly.
    """
    if os.path.exists(OUT_PATH):
        try:
            df = pd.read_csv(OUT_PATH, parse_dates=["timestamp"])

            required = {
                "timestamp", "target_temp", "target_humidity",
                "target_wind_speed", "target_wind_dir", "fetched_at",
            }
            missing_cols = required - set(df.columns)
            if missing_cols:
                print(f"  [cache invalid] Missing columns: {sorted(missing_cols)} — re-fetching ...")
            elif df.empty:
                print("  [cache invalid] Empty cache — re-fetching ...")
            else:
                fetched = pd.to_datetime(df["fetched_at"].iloc[0], utc=True, errors="coerce")
                if pd.isna(fetched):
                    print("  [cache invalid] Bad fetched_at — re-fetching ...")
                else:
                    age_hours = (datetime.now(timezone.utc) - fetched).total_seconds() / 3600
                    if 0 <= age_hours <= max_age_hours:
                        print(f"  [cache] Forecast weather loaded ({age_hours:.1f}h old).")
                        return df
                    print(f"  [stale] Cached forecast is {age_hours:.1f}h old — re-fetching ...")
        except Exception as e:
            print(f"  [cache invalid] {e} — re-fetching ...")

    df = get_forecast_weather()
    df.to_csv(OUT_PATH, index=False)
    return df


def print_summary(df: pd.DataFrame):
    print(f"\n  City          : {CITY['name']}")
    print(f"  Rows          : {len(df)} hours")
    print(f"  Window        : {df['timestamp'].min()} → {df['timestamp'].max()}")
    print(f"  Fetched at    : {df['fetched_at'].iloc[0]}")
    print(f"\n  Weather range:")
    print(f"    temp         : {df['target_temp'].min():.1f}°C – {df['target_temp'].max():.1f}°C")
    print(f"    humidity     : {df['target_humidity'].min():.0f}% – {df['target_humidity'].max():.0f}%")
    print(f"    wind speed   : {df['target_wind_speed'].min():.1f} – {df['target_wind_speed'].max():.1f} km/h")
    print(f"    wind dir     : {df['target_wind_dir'].min():.0f}° – {df['target_wind_dir'].max():.0f}°")
    print(f"\n  First 5 rows:")
    print(df[["timestamp","target_temp","target_humidity",
              "target_wind_speed","target_wind_dir"]].head(5).to_string(index=False))


def main():
    print(f"\n{'='*60}")
    print(f"  Forecast Weather — {CITY['name']} (next {FORECAST_HOURS}h)")
    print(f"  Source: Open-Meteo forecast (free, no key)")
    print(f"{'='*60}\n")

    print(f"  Fetching {FORECAST_HOURS}h hourly forecast (96h so +72h target always in range) ...")
    df = get_forecast_weather(FORECAST_HOURS)
    df.to_csv(OUT_PATH, index=False)

    print_summary(df)
    print(f"\n  ✓ Saved: {OUT_PATH}")
    print(f"\n  ⚠  UNITS CHECK (verify before inference):")
    print(f"     This script produces: temp °C, humidity %, wind km/h, wind_dir degrees.")
    print(f"     fetch_real_data.py used Open-Meteo archive with windspeed_10m (km/h by default).")
    print(f"     If your training data used m/s instead, model inputs will be wrong")
    print(f"     even though this script runs perfectly. Check data/training_dataset.csv:")
    print(f"       import pandas as pd")
    print(f"       pd.read_csv('data/training_dataset.csv')['wind_speed'].describe()")
    print(f"    from fetch_forecast_weather import load_or_fetch")
    print(f"    fw = load_or_fetch().set_index('timestamp')")
    print(f"    # fw has 96 rows (hours). For a source time t and horizon h:")
    print(f"    #   target_ts = t + pd.Timedelta(hours=h)  # e.g. +24, +48, +72")
    print(f"    #   weather_at_target = fw.loc[target_ts]")
    print(f"    # The 96h window provides buffer for +72h targets.")
    print(f"    # Inference must still verify that the exact target timestamp exists.")
    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()

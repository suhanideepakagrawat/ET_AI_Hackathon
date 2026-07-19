"""
predict_future_aqi.py
----------------------
Live inference: produces 24h / 48h / 72h AQI forecasts for all cells.

PIPELINE POSITION
------------------
    fetch_real_data.py       -> training_dataset.csv
    train_spatial_estimator  -> cell_aqi_estimated.csv   (Model 1 output)
    train_forecaster.py      -> forecaster_24h/48h/72h.json
    fetch_forecast_weather   -> forecast_weather.csv
    [THIS SCRIPT]            -> future_aqi_forecast.csv

SOURCE TIMESTAMP CHOICE
------------------------
We use one common source timestamp across all cells rather than each
cell's latest row, because cells have staggered coverage:

    2026-07-05 16:00 → only   4 cells
    2026-07-05 15:00 →      922 cells
    2026-07-04 22:00 →     1443 cells   ← used (max coverage)

All three target timestamps (source + 24/48/72h) fall inside the 96h
forecast weather window, so no missing target weather.

FEATURE ORDER (must match FEATURE_COLS in train_forecaster.py exactly)
-----------------------------------------------------------------------
    aqi_lag_1h .. aqi_lag_48h  (5)
    aqi_roll_mean_24h, aqi_roll_mean_7d, aqi_prev_day_max  (3)
    wind_speed, wind_dir, temp, humidity  (4)
    target_wind_speed, target_wind_dir, target_temp, target_humidity  (4)
    industrial_pct .. water_pct  (5)
    nearest_dist_km, is_estimated  (2)
    target_month, target_hour, target_weekday  (3)
    target_is_winter, target_is_summer, target_is_crop_burn, target_is_festival  (4)
    TOTAL: 30

LAG COMPUTATION
---------------
Uses exact-timestamp indexed lookups (not groupby().shift(n)) to match
the method in train_forecaster.py. A missing hour stays NaN rather than
silently pointing to a wrong row. Rolling stats use continuous-hourly
reindexing per cell so gaps don't corrupt window sizes.
"""

import os, math, argparse
import numpy as np
import pandas as pd
from datetime import timezone

try:
    from xgboost import XGBRegressor
    HAVE_XGB = True
except ImportError:
    HAVE_XGB = False

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

# ── Must match FEATURE_COLS in train_forecaster.py exactly ──────────────────
FEATURE_COLS = [
    "aqi_lag_1h", "aqi_lag_6h", "aqi_lag_12h", "aqi_lag_24h", "aqi_lag_48h",
    "aqi_roll_mean_24h", "aqi_roll_mean_7d", "aqi_prev_day_max",
    "wind_speed", "wind_dir", "temp", "humidity",
    "target_wind_speed", "target_wind_dir", "target_temp", "target_humidity",
    "industrial_pct", "construction_pct", "green_cover_pct", "residential_pct", "water_pct",
    "nearest_dist_km", "is_estimated",
    "target_month", "target_hour", "target_weekday",
    "target_is_winter", "target_is_summer", "target_is_crop_burn", "target_is_festival",
]

HORIZONS = [24, 48, 72]

FESTIVAL_MONTHS_DAYS = {(10,24),(10,25),(11,1),(11,12),(11,13)}
WINTER_MONTHS        = {11,12,1,2}
SUMMER_MONTHS        = {4,5,6}
CROP_BURNING_MONTHS  = {10,11}

# Default source timestamp — latest hour with broad cell coverage
DEFAULT_SOURCE_TS = None


# ─── STEP 1: Load cell AQI series ────────────────────────────────────────────

def load_cell_aqi(path: str) -> pd.DataFrame:
    """
    Load Model 1 output. Converts predicted_aqi to numeric, drops the
    small number of rows with invalid AQI (NaN / negative / > 500), renames
    to 'aqi' for internal use.
    """
    df = pd.read_csv(path, parse_dates=["timestamp"])
    before = len(df)
    df["predicted_aqi"] = pd.to_numeric(df["predicted_aqi"], errors="coerce")
    df = df[df["predicted_aqi"].notna()
            & (df["predicted_aqi"] >= 0)
            & (df["predicted_aqi"] <= 500)].copy()
    dropped = before - len(df)
    if dropped:
        print(f"  [data quality] dropped {dropped} invalid AQI rows from cell_aqi_estimated.csv")
    df = df.rename(columns={"predicted_aqi": "aqi"})
    df = df.sort_values(["cell_id", "timestamp"]).reset_index(drop=True)
    print(f"  → {len(df):,} cell-hour rows | {df['cell_id'].nunique()} unique cells")
    return df


# ─── STEP 2: Load static features from training dataset ──────────────────────

def load_static_and_weather(dataset_path: str) -> pd.DataFrame:
    """
    Loads source-time weather (wind/temp/humidity) and static per-cell
    features (land use %, nearest_dist_km) from the training dataset.
    Only columns actually needed are loaded to save memory.
    """
    needed = [
        "cell_id", "timestamp",
        "wind_speed", "wind_dir", "temp", "humidity",
        "industrial_pct", "construction_pct", "green_cover_pct",
        "residential_pct", "water_pct",
        "nearest_dist_km",
    ]
    header = pd.read_csv(dataset_path, nrows=0).columns.tolist()
    usecols = [c for c in needed if c in header]
    df = pd.read_csv(dataset_path, usecols=usecols, parse_dates=["timestamp"])
    df = df.drop_duplicates(subset=["cell_id","timestamp"]).reset_index(drop=True)
    print(f"  → {len(df):,} rows loaded from {os.path.basename(dataset_path)}")
    return df


# ─── STEP 3: Lag + rolling features (time-based, matching train_forecaster) ──

def compute_lag_features(aqi_df: pd.DataFrame) -> pd.DataFrame:
    """
    Exact-timestamp indexed lags — NOT groupby().shift(n).
    A missing hour stays NaN rather than silently shifting to a wrong row.
    Rolling stats use continuous hourly reindexing per cell so gaps
    don't corrupt window sizes (same method as train_forecaster.py).
    """
    print("  Computing time-based lag features ...")
    df = aqi_df.copy()

    # Deduplicate before indexing
    before = len(df)
    df = df.drop_duplicates(subset=["cell_id","timestamp"], keep="first")
    if len(df) < before:
        print(f"  [WARN] deduped {before-len(df)} duplicate (cell_id, timestamp) rows")

    aqi_lookup = df.set_index(["cell_id","timestamp"])["aqi"].sort_index()

    for h in [1, 6, 12, 24, 48]:
        lag_keys = pd.MultiIndex.from_arrays(
            [df["cell_id"], df["timestamp"] - pd.Timedelta(hours=h)]
        )
        df[f"aqi_lag_{h}h"] = aqi_lookup.reindex(lag_keys).to_numpy(dtype="float32")

    # Rolling stats on continuous hourly grid
    roll_frames = []
    for cell_id, grp in df.groupby("cell_id"):
        s = grp.set_index("timestamp")["aqi"].sort_index()
        full_idx = pd.date_range(s.index.min(), s.index.max(), freq="h")
        s_full   = s.reindex(full_idx)
        roll_frames.append(pd.DataFrame({
            "cell_id":           cell_id,
            "timestamp":         full_idx,
            "aqi_roll_mean_24h": s_full.rolling(24,  min_periods=6).mean().values,
            "aqi_roll_mean_7d":  s_full.rolling(168, min_periods=24).mean().values,
            "aqi_prev_day_max":  s_full.rolling(24,  min_periods=6).max().shift(24).values,
        }))
    roll_df = pd.concat(roll_frames, ignore_index=True)
    roll_lkp = roll_df.set_index(["cell_id","timestamp"]).sort_index()
    row_keys = pd.MultiIndex.from_arrays([df["cell_id"], df["timestamp"]])
    for c in ["aqi_roll_mean_24h", "aqi_roll_mean_7d", "aqi_prev_day_max"]:
        df[c] = roll_lkp[c].reindex(row_keys).to_numpy(dtype="float32")

    return df


# ─── STEP 4: Forecast weather lookup ─────────────────────────────────────────

def load_forecast_weather(path: str) -> pd.DataFrame:
    """
    Loads forecast_weather.csv (from fetch_forecast_weather.py).
    Indexed on timestamp for O(1) lookup per target timestamp.
    """
    df = pd.read_csv(path, parse_dates=["timestamp"])
    df = df.drop_duplicates(subset=["timestamp"]).set_index("timestamp").sort_index()
    print(f"  → forecast weather: {len(df)} hours "
          f"({df.index.min()} → {df.index.max()})")
    return df


def get_target_weather(fw: pd.DataFrame, target_ts: pd.Timestamp) -> dict:
    """
    Looks up forecast weather for target_ts with a clear error if missing.
    Do NOT call fw.loc[target_ts] without this guard — if the timestamp
    is missing, that produces a KeyError with no diagnostic information.
    """
    if target_ts not in fw.index:
        raise ValueError(
            f"No forecast weather for target timestamp {target_ts}.\n"
            f"  Available range: {fw.index.min()} → {fw.index.max()}\n"
            f"  Re-run fetch_forecast_weather.py to refresh the forecast."
        )
    row = fw.loc[target_ts]
    return {
        "target_wind_speed": float(row["target_wind_speed"]),
        "target_wind_dir":   float(row["target_wind_dir"]),
        "target_temp":       float(row["target_temp"]),
        "target_humidity":   float(row["target_humidity"]),
    }


# ─── STEP 5: Target calendar features ────────────────────────────────────────

def target_calendar(target_ts: pd.Timestamp) -> dict:
    """
    Calendar features at the TARGET time. These are known exactly in
    advance (the calendar 24h from now needs no forecasting) — no
    honesty caveat applies, unlike target-time weather.
    """
    return {
        "target_month":        target_ts.month,
        "target_hour":         target_ts.hour,
        "target_weekday":      target_ts.dayofweek,
        "target_is_winter":    1 if target_ts.month in WINTER_MONTHS else 0,
        "target_is_summer":    1 if target_ts.month in SUMMER_MONTHS else 0,
        "target_is_crop_burn": 1 if target_ts.month in CROP_BURNING_MONTHS else 0,
        "target_is_festival":  1 if (target_ts.month, target_ts.day) in FESTIVAL_MONTHS_DAYS else 0,
    }


# ─── STEP 6: Load trained forecaster models ──────────────────────────────────

def load_forecaster(horizon: int):
    if HAVE_XGB:
        path = os.path.join(DATA_DIR, f"forecaster_{horizon}h.json")
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Model not found: {path}\n"
                f"  Run train_forecaster.py first."
            )
        model = XGBRegressor()
        model.load_model(path)
        return model
    else:
        import joblib
        path = os.path.join(DATA_DIR, f"forecaster_{horizon}h.pkl")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model not found: {path}")
        return joblib.load(path)


# ─── STEP 7: Build inference feature matrix ──────────────────────────────────

def build_inference_matrix(
    source_df: pd.DataFrame,
    source_ts: pd.Timestamp,
    target_ts: pd.Timestamp,
    forecast_weather: pd.DataFrame,
    static_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Builds the 30-feature matrix for all cells at one (source_ts, target_ts) pair.
    - source_df: cell AQI series with lag/rolling features already computed
    - static_df: source-time weather + static land use per cell
    """
    # Rows at source timestamp
    src = source_df[source_df["timestamp"] == source_ts].copy()
    if src.empty:
        raise RuntimeError(
            f"No rows at source timestamp {source_ts}. "
            f"Available timestamps around that time:\n"
            + str(source_df["timestamp"].drop_duplicates().sort_values().tail(10).tolist())
        )

    # Source-time weather and static features
    static_at_src = static_df[static_df["timestamp"] == source_ts].copy()
    if static_at_src.empty:
        # Find the nearest available timestamp VALUE, then select ALL cells at it.
        # idxmin() returns a row-index label, not a timestamp — using it directly
        # in loc would select only one row (one cell) and leave all others with
        # NaN source weather. Correct fix: get unique timestamps, find the nearest
        # value, then filter the whole dataframe to that timestamp.
        available_ts = sorted(static_df["timestamp"].dropna().unique())
        if not available_ts:
            raise RuntimeError(
                f"No timestamps available in static dataset — cannot fall back "
                f"from source_timestamp {source_ts}."
            )
        nearest_ts = min(available_ts, key=lambda t: abs(pd.Timestamp(t) - source_ts))
        static_at_src = static_df[static_df["timestamp"] == nearest_ts].copy()
        print(f"  [WARN] No static features at {source_ts} — "
              f"using nearest available: {nearest_ts} "
              f"({len(static_at_src)} cells)")
    src = src.merge(static_at_src[["cell_id","wind_speed","wind_dir","temp","humidity",
                                    "industrial_pct","construction_pct","green_cover_pct",
                                    "residential_pct","water_pct","nearest_dist_km"]],
                    on="cell_id", how="left", suffixes=("","_static"))

    # Target-time forecast weather (same value for all cells — city-level)
    tw = get_target_weather(forecast_weather, target_ts)
    for col, val in tw.items():
        src[col] = val

    # Target calendar features
    tc = target_calendar(target_ts)
    for col, val in tc.items():
        src[col] = val

    return src


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Live AQI forecast — 24h/48h/72h")
    parser.add_argument(
        "--source-timestamp",
        default=None,
        help=(
            f"Optional source timestamp (YYYY-MM-DD HH:MM:SS). "
            "If omitted, the script automatically chooses the latest "
            "timestamp with sufficient cell coverage."
        ),
    )
    parser.add_argument(
        "--dataset",
        default=os.path.join(DATA_DIR, "training_dataset.csv"),
        help="Training dataset CSV for source-time weather + static features.",
    )
    parser.add_argument(
        "--estimated-csv",
        default=os.path.join(DATA_DIR, "cell_aqi_estimated.csv"),
        help="Model 1 output (cell_aqi_estimated.csv).",
    )
    parser.add_argument(
        "--forecast-weather",
        default=os.path.join(DATA_DIR, "forecast_weather.csv"),
        help="Forecast weather from fetch_forecast_weather.py.",
    )
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  Horizons: {HORIZONS}")
    print(f"{'='*60}\n")

    # ── Load inputs ──────────────────────────────────────────────────────────
    print("[1/5] Loading cell AQI series (Model 1 output)")
    aqi_df = load_cell_aqi(args.estimated_csv)
    n_cells = aqi_df["cell_id"].nunique()

    # ------------------------------------------------------------------
    print(
        f"       NOTE: {n_cells} cells available — "
        f"{'claim 1600-cell forecast only after fixing upstream grid coverage' if n_cells < 1600 else 'full 1600-cell coverage confirmed'}"
    )

    print("\n[2/5] Loading source-time weather + static features")
    static_df = load_static_and_weather(args.dataset)

    print("\n[3/5] Computing lag + rolling features (time-based)")
    aqi_with_lags = compute_lag_features(aqi_df)

    print("\n[4/5] Loading forecast weather")
    fw = load_forecast_weather(args.forecast_weather)

    # ------------------------------------------------------------------
    # Choose source timestamp AFTER loading forecast weather
    # ------------------------------------------------------------------
    if args.source_timestamp:
        source_ts = pd.Timestamp(args.source_timestamp)
        print(f"Using user-specified source timestamp: {source_ts}")
    else:
        coverage = (
            aqi_df.groupby("timestamp")["cell_id"]
            .nunique()
            .sort_index()
        )

        MIN_CELLS = 1400

        forecast_start = fw.index.min()
        forecast_end = fw.index.max()

        valid = coverage[coverage >= MIN_CELLS]

        # Keep only timestamps whose +72h target is inside the weather window
        valid = valid[
            (valid.index + pd.Timedelta(hours=24) >= forecast_start)
            &
            (valid.index + pd.Timedelta(hours=72) <= forecast_end)
        ]

        if valid.empty:
            raise RuntimeError(
                f"No AQI timestamp with >= {MIN_CELLS} cells fits inside the "
                f"forecast weather window ({forecast_start} → {forecast_end}).\n"
                f"  AQI history covers {coverage.index.min()} → {coverage.index.max()}.\n"
                f"  This is almost always a data-staleness problem, not a logic bug:\n"
                f"  forecast_weather.csv is always anchored to 'today', so if\n"
                f"  cell_aqi_estimated.csv wasn't regenerated recently, the two\n"
                f"  windows won't overlap. Re-run fetch_real_data.py and\n"
                f"  train_spatial_estimator.py to refresh the AQI history up to\n"
                f"  the present, then re-run this script."
            )

        source_ts = valid.index.max()

        print(
            f"Auto-selected source timestamp: {source_ts} "
            f"({coverage.loc[source_ts]} cells)"
        )

    # Verify all three target timestamps are in the forecast window
    for h in HORIZONS:
        target_ts = source_ts + pd.Timedelta(hours=h)
        if target_ts not in fw.index:
            raise ValueError(
                f"+{h}h target {target_ts} is outside forecast weather range "
                f"({fw.index.min()} → {fw.index.max()}). "
                f"Re-run fetch_forecast_weather.py or choose an earlier source timestamp."
            )
    print(f"  ✓ All target timestamps ({', '.join(str(source_ts + pd.Timedelta(hours=h)) for h in HORIZONS)}) "
          f"are within the forecast window.")

    print("\n[5/5] Forecasting per horizon")
    all_results = []

    for horizon in HORIZONS:
        target_ts = source_ts + pd.Timedelta(hours=horizon)
        print(f"\n  [{horizon}h] source={source_ts}  →  target={target_ts}")

        model = load_forecaster(horizon)

        X_df = build_inference_matrix(
            source_df=aqi_with_lags,
            source_ts=source_ts,
            target_ts=target_ts,
            forecast_weather=fw,
            static_df=static_df,
        )

        # Verify all 30 features are present and in correct order
        missing_features = [c for c in FEATURE_COLS if c not in X_df.columns]
        if missing_features:
            raise RuntimeError(
                f"Missing features for {horizon}h model: {missing_features}\n"
                "  Check that all upstream scripts ran successfully."
            )

        X = X_df[FEATURE_COLS].astype("float32")
        preds = model.predict(X)

        result_cols = ["cell_id", "lat", "lon", "is_estimated", "nearest_station", "nearest_dist_km"]
        missing_out_cols = [c for c in result_cols if c not in X_df.columns]
        if missing_out_cols:
            raise RuntimeError(
                f"cell_aqi_estimated.csv is missing columns needed for output: {missing_out_cols}\n"
                "  Re-run train_spatial_estimator.py to regenerate it."
            )
        result = X_df[result_cols].copy()
        result["source_timestamp"] = source_ts
        result["target_timestamp"] = target_ts
        result["horizon_hours"]    = horizon
        result["forecast_aqi"]     = preds.clip(0, 500).round(1)
        result["source_aqi"]       = X_df["aqi"].values

        n_forecast_cells = len(result)   # cells at source_ts only — less than total unique cells
        n_valid = result["forecast_aqi"].notna().sum()
        print(f"    → {n_forecast_cells} cells at source timestamp "
              f"({n_cells} unique in full history) | "
              f"AQI range: {result['forecast_aqi'].min():.0f}–{result['forecast_aqi'].max():.0f} | "
              f"mean: {result['forecast_aqi'].mean():.1f}")
        all_results.append(result)

    # ── Save ─────────────────────────────────────────────────────────────────
    out = pd.concat(all_results, ignore_index=True)
    out_path = os.path.join(DATA_DIR, "future_aqi_forecast.csv")
    out.to_csv(out_path, index=False)

    print(f"\n{'='*60}")
    print(f"  ✓ Saved: {out_path}")
    cells_per_horizon = len(out) // len(HORIZONS)   # actual rows per horizon at source_ts
    print(f"  Rows   : {len(out):,} ({len(HORIZONS)} horizons × {cells_per_horizon} cells at source timestamp)")
    print(f"  NOTE   : {n_cells} unique cells exist in full AQI history but only "
          f"{cells_per_horizon} had data at source timestamp {source_ts}.")
    print(f"  Columns: {list(out.columns)}")
    print(f"\n  Summary by horizon:")
    for h in HORIZONS:
        h_rows = out[out["horizon_hours"] == h]
        print(f"    +{h}h: {len(h_rows)} cells | "
              f"AQI {h_rows['forecast_aqi'].min():.0f}–{h_rows['forecast_aqi'].max():.0f} "
              f"(mean {h_rows['forecast_aqi'].mean():.1f})")
    print(f"\n  HONESTY NOTE: target weather columns use Open-Meteo forecast,")
    print(f"  not historical actuals. Forecast accuracy degrades at +48h/+72h")
    print(f"  as weather forecast uncertainty compounds.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
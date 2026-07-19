import pandas as pd


def add_persistence_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Persistence score:
    A cell appearing in all forecast horizons
    (24h, 48h, 72h) gets maximum persistence.
    """

    counts = (
        df.groupby("cell_id")["horizon_hours"]
        .nunique()
        .rename("persistence_count")
        .reset_index()
    )

    df = df.merge(
        counts,
        on="cell_id",
        how="left"
    )

    df["persistence_score"] = (
        df["persistence_count"] / 3.0
    ).clip(0, 1)

    return df


def severity_from_aqi(aqi: float) -> str:

    if aqi >= 300:
        return "Critical"

    if aqi >= 200:
        return "Very High"

    if aqi >= 150:
        return "High"

    if aqi >= 100:
        return "Moderate"

    return "Low"


def priority_band(score: float) -> str:

    if score >= 65:
        return "CRITICAL"

    if score >= 55:
        return "HIGH"

    if score >= 45:
        return "MEDIUM"

    return "LOW"


def compute_priority_score(df: pd.DataFrame) -> pd.DataFrame:

    # --------------------------------------------------
    # Persistence
    # --------------------------------------------------
    df = add_persistence_score(df)

    # --------------------------------------------------
    # AQI score (0-1)
    # AQI >= 300 gets maximum score
    # --------------------------------------------------
    df["aqi_score"] = (
        df["forecast_aqi"] / 300.0
    ).clip(0, 1)

    # --------------------------------------------------
    # Confidence already 0-1
    # --------------------------------------------------
    df["confidence_score_norm"] = (
        df["confidence"]
    ).clip(0, 1)

    # --------------------------------------------------
    # dominant_source_pct is 0-100
    # convert to 0-1
    # --------------------------------------------------
    df["source_strength"] = (
        df["dominant_source_pct"] / 100.0
    ).clip(0, 1)

    # --------------------------------------------------
    # Priority Score (0-100)
    # --------------------------------------------------
    df["priority_score"] = (
        50 * df["aqi_score"]
        + 20 * df["confidence_score_norm"]
        + 20 * df["source_strength"]
        + 10 * df["persistence_score"]
    )

    # --------------------------------------------------
    # AQI severity
    # --------------------------------------------------
    df["severity"] = (
        df["forecast_aqi"]
        .apply(severity_from_aqi)
    )

    # --------------------------------------------------
    # Enforcement priority band
    # --------------------------------------------------
    df["priority_band"] = (
        df["priority_score"]
        .apply(priority_band)
    )

    return df
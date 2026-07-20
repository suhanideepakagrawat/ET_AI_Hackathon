import os
import pandas as pd

from enforcement.priority_engine import compute_priority_score
from enforcement.action_recommender import get_action

DATA_DIR = "data"

INPUT_FILE = os.path.join(
    DATA_DIR,
    "source_attribution.csv"
)

OUTPUT_FILE = os.path.join(
    DATA_DIR,
    "enforcement_priorities.csv"
)


def main():

    print("\n==================================================")
    print(" Enforcement Intelligence & Prioritisation")
    print("==================================================\n")

    print("[1/4] Loading source attribution")

    df = pd.read_csv(INPUT_FILE)

    print(f"  Rows : {len(df):,}")

    print("\n[2/4] Computing priority scores")

    df = compute_priority_score(df)

    print("\n[3/4] Generating enforcement actions")

    df["recommended_action"] = (
        df["dominant_source"]
        .apply(get_action)
    )

    # --------------------------------------------------
    # Evidence string
    # dominant_source_pct is already 0-100
    # confidence is 0-1
    # --------------------------------------------------
    df["evidence"] = (
        "AQI="
        + df["forecast_aqi"].round(1).astype(str)
        + ", source="
        + df["dominant_source"].astype(str)
        + " ("
        + df["dominant_source_pct"]
            .round(1)
            .astype(str)
        + "%)"
        + ", confidence="
        + (df["confidence"] * 100)
            .round(0)
            .astype(int)
            .astype(str)
        + "%"
    )

    cols = [
        "cell_id",
        "lat",
        "lon",
        "horizon_hours",
        "forecast_aqi",
        "severity",
        "priority_band",
        "dominant_source",
        "confidence",
        "priority_score",
        "recommended_action",
        "evidence"
    ]

    df = (
        df[cols]
        .sort_values(
            "priority_score",
            ascending=False
        )
    )

    print("\n[4/4] Saving output")

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(f"\nSaved: {OUTPUT_FILE}")
    print(f"Rows : {len(df):,}")

    print("\nTop 10 Hotspots\n")

    print(
        df[
            [
                "cell_id",
                "forecast_aqi",
                "dominant_source",
                "priority_score",
                "recommended_action"
            ]
        ]
        .head(10)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
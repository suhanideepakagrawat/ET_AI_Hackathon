import pandas as pd

FORECAST_FILE = "data/future_aqi_forecast_ward.csv"
PRIORITY_FILE = "data/enforcement_priorities.csv"

OUTPUT_FILE = "data/ward_deployment_plan.csv"


TEAM_MAP = {
    "Traffic/Roads": "Traffic Enforcement Team",
    "Industry": "Industrial Inspection Team",
    "Construction/Dust": "Dust Control Team"
}


def main():

    print("\n==================================================")
    print(" Ward-Level Deployment Planning")
    print("==================================================\n")

    print("[1/4] Loading data")

    forecast = pd.read_csv(FORECAST_FILE)

    priority = pd.read_csv(PRIORITY_FILE)

    print(
        f"Forecast rows : {len(forecast):,}"
    )

    print(
        f"Priority rows : {len(priority):,}"
    )

    print("\n[2/4] Merging ward mapping")

    df = priority.merge(
        forecast[
            [
                "cell_id",
                "horizon_hours",
                "Ward_No",
                "Ward_Name"
            ]
        ],
        on=[
            "cell_id",
            "horizon_hours"
        ],
        how="left"
    )

    df = df[
        df["Ward_No"].notna()
    ].copy()

    print(
        f"Mapped rows : {len(df):,}"
    )

    print("\n[3/4] Aggregating wards")

    ward_plan = (
        df.groupby(
            [
                "Ward_No",
                "Ward_Name"
            ],
            as_index=False
        )
        .agg(
            hotspot_count=(
                "cell_id",
                "count"
            ),
            max_aqi=(
                "forecast_aqi",
                "max"
            ),
            avg_aqi=(
                "forecast_aqi",
                "mean"
            ),
            max_priority=(
                "priority_score",
                "max"
            ),
            mean_priority=(
                "priority_score",
                "mean"
            )
        )
    )

    # -----------------------------------
    # Dominant source per ward
    # -----------------------------------

    source_counts = (
        df.groupby(
            [
                "Ward_No",
                "Ward_Name",
                "dominant_source"
            ]
        )
        .size()
        .reset_index(
            name="count"
        )
    )

    source_counts = (
        source_counts
        .sort_values(
            "count",
            ascending=False
        )
        .drop_duplicates(
            subset=[
                "Ward_No",
                "Ward_Name"
            ]
        )
    )

    ward_plan = ward_plan.merge(
        source_counts[
            [
                "Ward_No",
                "Ward_Name",
                "dominant_source"
            ]
        ],
        on=[
            "Ward_No",
            "Ward_Name"
        ],
        how="left"
    )

    # -----------------------------------
    # Recommended team
    # -----------------------------------

    ward_plan[
        "recommended_team"
    ] = (
        ward_plan[
            "dominant_source"
        ]
        .map(TEAM_MAP)
        .fillna(
            "General Enforcement Team"
        )
    )

    # -----------------------------------
    # NEW DEPLOYMENT SCORE
    # -----------------------------------

    ward_plan["aqi_component"] = (
        ward_plan["max_aqi"] / 200.0
    ) * 100

    ward_plan["hotspot_component"] = (
        ward_plan["hotspot_count"]
        /
        ward_plan["hotspot_count"].max()
    ) * 100

    ward_plan["deployment_score"] = (
        0.40 * ward_plan["max_priority"]
        +
        0.40 * ward_plan["aqi_component"]
        +
        0.20 * ward_plan["hotspot_component"]
    )

    # -----------------------------------
    # Rank wards
    # -----------------------------------

    ward_plan = (
        ward_plan
        .sort_values(
            "deployment_score",
            ascending=False
        )
        .reset_index(
            drop=True
        )
    )

    ward_plan[
        "deployment_rank"
    ] = (
        ward_plan.index + 1
    )

    # -----------------------------------
    # Cleanup
    # -----------------------------------

    cols = [
        "deployment_rank",
        "Ward_No",
        "Ward_Name",
        "hotspot_count",
        "max_aqi",
        "avg_aqi",
        "max_priority",
        "deployment_score",
        "dominant_source",
        "recommended_team"
    ]

    ward_plan = ward_plan[
        cols
    ]

    print("\n[4/4] Saving output")

    ward_plan.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print(
        f"\nSaved: {OUTPUT_FILE}"
    )

    print("\nTop 20 Priority Wards\n")

    print(
        ward_plan.head(20).to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
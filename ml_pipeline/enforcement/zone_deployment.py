import pandas as pd


def main():

    df = pd.read_csv(
        "data/enforcement_report.csv"
    )

    # Approximate operational zones
    # ~2 km buckets

    df["zone_id"] = (
        df["lat"].round(2).astype(str)
        + "_"
        + df["lon"].round(2).astype(str)
    )

    zones = (
        df.groupby("zone_id")
        .agg(
            hotspot_count=("cell_id", "count"),
            critical_count=(
                "severity",
                lambda x: (x == "CRITICAL").sum()
            ),
            max_aqi=("forecast_aqi", "max"),
            max_priority=("priority_score", "max"),
            dominant_source=(
                "dominant_source",
                lambda x: x.mode().iloc[0]
            ),
            center_lat=("lat", "mean"),
            center_lon=("lon", "mean")
        )
        .reset_index()
    )

    def assign_team(source):

        if source == "Traffic/Roads":
            return "Traffic Enforcement Team"

        if source == "Industry":
            return "Industrial Inspection Team"

        if source == "Construction/Dust":
            return "Dust Control Team"

        return "General Inspection Team"

    zones["recommended_team"] = (
        zones["dominant_source"]
        .apply(assign_team)
    )

    zones = zones.sort_values(
        ["critical_count", "max_priority"],
        ascending=False
    )

    zones["deployment_rank"] = (
        range(1, len(zones) + 1)
    )

    zones.to_csv(
        "data/zone_deployment_plan.csv",
        index=False
    )

    print("\nTop Deployment Zones\n")
    print(
        zones.head(15).to_string(index=False)
    )

    print(
        "\nSaved: data/zone_deployment_plan.csv"
    )


if __name__ == "__main__":
    main()
import json
import pandas as pd
from sklearn.cluster import DBSCAN


def team_for_source(source):

    if source == "Traffic/Roads":
        return "Traffic Enforcement Team"

    if source == "Industry":
        return "Industrial Inspection Team"

    if source == "Construction/Dust":
        return "Dust Control Team"

    return "General Inspection Team"


def main():

    print("\n==================================================")
    print(" Cluster-Based Deployment Planning")
    print("==================================================")

    df = pd.read_csv(
        "data/enforcement_priorities.csv"
    )

    # Use all actionable hotspots
    hotspots = df[
        df["priority_band"].isin(
            ["CRITICAL", "HIGH"]
        )
    ].copy()

    print(
        f"\nHotspots used: {len(hotspots):,}"
    )

    coords = hotspots[
        ["lat", "lon"]
    ].values

    # ~2 km radius
    clustering = DBSCAN(
        eps=0.02,
        min_samples=3
    )

    hotspots["cluster_id"] = (
        clustering.fit_predict(coords)
    )

    hotspots = hotspots[
        hotspots["cluster_id"] >= 0
    ]

    print(
        f"Clusters found: "
        f"{hotspots['cluster_id'].nunique()}"
    )

    clusters = (
        hotspots.groupby("cluster_id")
        .agg(
            hotspot_count=("cell_id", "count"),

            max_aqi=("forecast_aqi", "max"),

            max_priority=("priority_score", "max"),

            center_lat=("lat", "mean"),

            center_lon=("lon", "mean"),

            dominant_source=(
                "dominant_source",
                lambda x: x.mode().iloc[0]
            )
        )
        .reset_index()
    )

    clusters["recommended_team"] = (
        clusters["dominant_source"]
        .apply(team_for_source)
    )

    clusters = clusters.sort_values(
        ["hotspot_count", "max_priority"],
        ascending=False
    )

    clusters["deployment_rank"] = (
        range(
            1,
            len(clusters) + 1
        )
    )

    csv_file = (
        "data/cluster_deployment_plan.csv"
    )

    clusters.to_csv(
        csv_file,
        index=False
    )

    features = []

    for _, row in clusters.iterrows():

        features.append({

            "type": "Feature",

            "geometry": {

                "type": "Point",

                "coordinates": [
                    float(row["center_lon"]),
                    float(row["center_lat"])
                ]
            },

            "properties": {

                "cluster_id":
                    int(row["cluster_id"]),

                "deployment_rank":
                    int(row["deployment_rank"]),

                "hotspot_count":
                    int(row["hotspot_count"]),

                "max_aqi":
                    float(row["max_aqi"]),

                "dominant_source":
                    str(row["dominant_source"]),

                "recommended_team":
                    str(row["recommended_team"])
            }
        })

    geojson = {

        "type": "FeatureCollection",

        "features": features
    }

    geo_file = (
        "data/deployment_zones.geojson"
    )

    with open(
        geo_file,
        "w"
    ) as f:

        json.dump(
            geojson,
            f,
            indent=2
        )

    print(
        f"\nSaved: {csv_file}"
    )

    print(
        f"Saved: {geo_file}"
    )

    print("\nTop Deployment Zones\n")

    print(
        clusters.head(15)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
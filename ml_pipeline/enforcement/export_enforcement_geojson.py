import json
import pandas as pd


TOP_N = 20


def main():

    report = pd.read_csv(
        "data/enforcement_report.csv"
    )

    attribution = pd.read_csv(
        "data/source_attribution.csv"
    )

    top_cells = set(
        report["cell_id"]
        .head(TOP_N)
        .tolist()
    )

    df = attribution[
        attribution["cell_id"].isin(top_cells)
    ].copy()

    df = (
        df.sort_values(
            "forecast_aqi",
            ascending=False
        )
        .drop_duplicates("cell_id")
    )

    features = []

    for _, row in df.iterrows():

        features.append({

            "type": "Feature",

            "geometry": {
                "type": "Point",
                "coordinates": [
                    float(row["lon"]),
                    float(row["lat"])
                ]
            },

            "properties": {

                "cell_id":
                    int(row["cell_id"]),

                "forecast_aqi":
                    float(row["forecast_aqi"]),

                "dominant_source":
                    str(row["dominant_source"]),

                "confidence":
                    float(row["confidence"]),

                "priority":
                    "HIGH",

                "recommended_action":
                    report.loc[
                        report["cell_id"]
                        == row["cell_id"],
                        "recommended_action"
                    ].iloc[0]
            }
        })

    geojson = {

        "type": "FeatureCollection",

        "features": features
    }

    out_file = (
        "data/enforcement_targets.geojson"
    )

    with open(out_file, "w") as f:

        json.dump(
            geojson,
            f,
            indent=2
        )

    print()
    print(
        f"Saved: {out_file}"
    )
    print(
        f"Features: {len(features)}"
    )


if __name__ == "__main__":
    main()
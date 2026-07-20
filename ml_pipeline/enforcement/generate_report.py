import pandas as pd


def build_report():

    targets = pd.read_csv(
        "data/top_enforcement_targets.csv"
    )

    full = pd.read_csv(
        "data/source_attribution.csv"
    )

    # Get highest-priority horizon per cell
    merged = targets.merge(
        full,
        on="cell_id",
        how="left"
    )

    report_rows = []

    for _, row in targets.iterrows():

        report_rows.append({

            "rank":
                row["rank"],

            "cell_id":
                row["cell_id"],

            "lat":
                row["lat"],

            "lon":
                row["lon"],

            "priority_score":
                row["max_priority"],

            "forecast_aqi":
                row["max_aqi"],

            "dominant_source":
                row["dominant_source"],

            "recommended_action":
                row["action"],

            "evidence":
                row["evidence"]
        })

    report = pd.DataFrame(report_rows)

    def band(score):

        if score >= 65:
            return "CRITICAL"

        if score >= 55:
            return "HIGH"

        if score >= 45:
            return "MEDIUM"

        return "LOW"

    report["severity"] = (
        report["priority_score"]
        .apply(band)
    )

    report = report[
        [
            "rank",
            "severity",
            "cell_id",
            "lat",
            "lon",
            "forecast_aqi",
            "dominant_source",
            "priority_score",
            "recommended_action",
            "evidence"
        ]
    ]

    report.to_csv(
        "data/enforcement_report.csv",
        index=False
    )

    print()
    print("Saved: data/enforcement_report.csv")
    print()

    print(
        report.head(10).to_string(index=False)
    )


if __name__ == "__main__":
    build_report()
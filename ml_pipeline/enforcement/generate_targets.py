import pandas as pd


def generate_top_targets(
    input_csv="data/enforcement_priorities.csv",
    output_csv="data/top_enforcement_targets.csv",
    top_n=20
):

    df = pd.read_csv(input_csv)

    agg = (
        df.groupby("cell_id")
        .agg(
            lat=("lat", "first"),
            lon=("lon", "first"),

            max_priority=("priority_score", "max"),

            max_aqi=("forecast_aqi", "max"),

            dominant_source=("dominant_source", lambda x: x.mode().iloc[0]),

            action=("recommended_action", "first"),

            evidence=("evidence", "first")
        )
        .reset_index()
    )

    agg = agg.sort_values(
        "max_priority",
        ascending=False
    )

    agg["rank"] = range(
        1,
        len(agg) + 1
    )

    top = agg.head(top_n)

    top.to_csv(
        output_csv,
        index=False
    )

    print()
    print("Top Enforcement Targets")
    print("=" * 60)

    print(
        top[
            [
                "rank",
                "cell_id",
                "max_aqi",
                "dominant_source",
                "max_priority"
            ]
        ]
        .to_string(index=False)
    )

    print()
    print(f"Saved: {output_csv}")


if __name__ == "__main__":
    generate_top_targets()
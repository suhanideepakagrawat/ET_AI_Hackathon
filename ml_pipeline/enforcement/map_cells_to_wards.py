import pandas as pd
import geopandas as gpd

print("Loading AQI forecasts...")

cells = pd.read_csv(
    "data/future_aqi_forecast.csv"
)

print("Loading ward boundaries...")

wards = gpd.read_file(
    "data/Delhi_Wards-SHP/Delhi_Wards.shp"
)

print(f"Wards loaded: {len(wards)}")

# ==================================================
# Create GeoDataFrame from AQI cells
# ==================================================

cells_gdf = gpd.GeoDataFrame(
    cells,
    geometry=gpd.points_from_xy(
        cells["lon"],
        cells["lat"]
    ),
    crs="EPSG:4326"
)

# ==================================================
# Reproject to metric CRS for nearest-neighbour join
# ==================================================

PROJECTED_CRS = "EPSG:3857"

cells_proj = cells_gdf.to_crs(PROJECTED_CRS)
wards_proj = wards.to_crs(PROJECTED_CRS)

print("Assigning nearest ward...")

mapped = gpd.sjoin_nearest(
    cells_proj,
    wards_proj[
        [
            "Ward_No",
            "Ward_Name",
            "geometry"
        ]
    ],
    how="left",
    distance_col="distance_to_ward"
)

# ==================================================
# Remove duplicate matches
# (some cells lie exactly on ward boundaries)
# ==================================================

mapped = (
    mapped
    .sort_values("distance_to_ward")
    .drop_duplicates(
        subset=[
            "cell_id",
            "horizon_hours"
        ],
        keep="first"
    )
)

# ==================================================
# Back to normal dataframe
# ==================================================

mapped = mapped.to_crs("EPSG:4326")

mapped.drop(
    columns=[
        "geometry",
        "index_right"
    ],
    inplace=True,
    errors="ignore"
)

# ==================================================
# Save output
# ==================================================

OUTPUT_FILE = (
    "data/future_aqi_forecast_ward.csv"
)

mapped.to_csv(
    OUTPUT_FILE,
    index=False
)

# ==================================================
# Validation
# ==================================================

print("\nResults")
print("=" * 60)

print(
    "Rows:",
    len(mapped)
)

print(
    "Missing wards:",
    mapped["Ward_No"].isna().sum()
)

print(
    "Unique wards:",
    mapped["Ward_No"].nunique()
)

dupes = mapped.duplicated(
    subset=[
        "cell_id",
        "horizon_hours"
    ]
).sum()

print(
    "Duplicate cell-horizon pairs:",
    dupes
)

print("\nSample wards:")

print(
    mapped[
        [
            "Ward_No",
            "Ward_Name"
        ]
    ]
    .drop_duplicates()
    .head(10)
    .to_string(index=False)
)

print(
    f"\nSaved: {OUTPUT_FILE}"
)
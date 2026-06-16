"""Cars data loading, cleaning, and feature preparation."""
from common import *

def infer_numeric_dtype(series):
    """Convert a messy CSV column to numeric while preserving integer columns."""
    numeric_series = pd.to_numeric(series, errors="coerce")
    non_missing_values = numeric_series.dropna()

    if non_missing_values.mod(1).eq(0).all():
        integer_dtype = "Int64" if numeric_series.hasnans else "int64"
        return numeric_series.astype(integer_dtype)

    return numeric_series

def read_ab_test_data(data_path=DATA_PATH):
    """Read the car ads dataset and coerce known numeric/date columns."""
    data_path = Path(data_path)
    if not data_path.exists() and data_path == DATA_PATH and LEGACY_DATA_PATH.exists():
        data_path = LEGACY_DATA_PATH

    dataframe = pd.read_csv(
        data_path,
        dtype={"src_ad_id": "string"},
        na_values=MISSING_VALUE_MARKERS,
    )

    for column in NUMERIC_IMPORT_COLUMNS:
        if column in dataframe.columns:
            dataframe[column] = infer_numeric_dtype(dataframe[column])

    if "ad_start_dt" in dataframe.columns:
        dataframe["ad_start_dt"] = pd.to_datetime(dataframe["ad_start_dt"], errors="coerce")

    return dataframe

def existing_columns(dataframe, requested_columns):
    """Return requested columns that are present in the dataframe."""
    return [column for column in requested_columns if column in dataframe.columns]

def prepare_ab_data(dataframe):
    """Create the A/B analysis table.

    Rows outside groups A/B are excluded from the experiment comparison, missing
    lead-event counts are treated as zero events, and the primary KPI is
    `has_any_lead`.
    """
    ab_data = dataframe.loc[dataframe["group"].isin(VALID_GROUPS)].copy()
    excluded_data = dataframe.loc[~dataframe["group"].isin(VALID_GROUPS)].copy()

    metric_columns = existing_columns(ab_data, METRIC_COLUMNS)
    # Primary outcome: one ad is successful if any lead channel records activity.
    ab_data[metric_columns] = ab_data[metric_columns].fillna(0)
    ab_data["has_any_lead"] = ab_data[metric_columns].gt(0).any(axis=1)
    ab_data["total_leads"] = ab_data[metric_columns].sum(axis=1)

    if "bouwjaar" in ab_data.columns:
        reference_year = int(ab_data["bouwjaar"].max())
        ab_data["car_age"] = reference_year - ab_data["bouwjaar"]

    return ab_data, excluded_data

def prepare_insight_data(dataframe):
    """Prepare all rows for descriptive q3 lead and segment analysis.

    Unlike `prepare_ab_data`, this keeps unassigned rows because q3 describes
    marketplace lead behavior rather than experiment lift.
    """
    insight_data = dataframe.copy()
    metric_columns = existing_columns(insight_data, METRIC_COLUMNS)
    insight_data[metric_columns] = insight_data[metric_columns].fillna(0)
    insight_data["has_any_lead"] = insight_data[metric_columns].gt(0).any(axis=1)
    insight_data["total_leads"] = insight_data[metric_columns].sum(axis=1)

    if "bouwjaar" in insight_data.columns:
        reference_year = int(insight_data["bouwjaar"].max())
        insight_data["car_age"] = reference_year - insight_data["bouwjaar"]

    return add_listing_lifecycle_fields(add_segments(insight_data))

def add_segments(dataframe):
    """Add fixed business-readable segment bands.

    These cuts use stable thresholds instead of sample quantiles so segment
    tables stay comparable across notebooks.
    """
    segmented = dataframe.copy()

    segmented["price_band"] = pd.cut(
        segmented["price"],
        bins=[0, 25000, 60000, 120000, float("inf")],
        labels=["0-25k", "25k-60k", "60k-120k", "120k+"],
        include_lowest=True,
    )
    segmented["km_band"] = pd.cut(
        segmented["kmstand"],
        bins=[0, 75000, 150000, 200000, float("inf")],
        labels=["0-75k", "75k-150k", "150k-200k", "200k+"],
        include_lowest=True,
    )
    segmented["car_age_band"] = pd.cut(
        segmented["car_age"],
        bins=[-1, 3, 7, 12, 100],
        labels=["0-3", "4-7", "8-12", "13+"],
    )
    segmented["photo_count_band"] = pd.cut(
        segmented["photo_cnt"],
        bins=[-1, 5, 12, 20, 100],
        labels=["0-5", "6-12", "13-20", "21+"],
    )

    return segmented

def add_listing_lifecycle_fields(dataframe):
    """Add q3 lifecycle and weekday fields used in time-based summaries."""
    lifecycle_data = dataframe.copy()
    lifecycle_data["days_live_band"] = pd.cut(
        lifecycle_data["days_live"],
        bins=[-1, 3, 7, 14, 31, float("inf")],
        labels=["0-3", "4-7", "8-14", "15-31", "31+"],
    )
    lifecycle_data["listing_lifecycle_stage"] = pd.cut(
        lifecycle_data["days_live"],
        bins=[-1, 7, 31, float("inf")],
        labels=["Fresh: 0-7 days", "Mid-life: 8-31 days", "Stale: 31+ days"],
    )
    lifecycle_data["start_weekday"] = lifecycle_data["ad_start_dt"].dt.day_name()
    return lifecycle_data

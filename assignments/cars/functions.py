"""Shared helpers for the cars analysis notebooks.

Includes data loading, cleaning, A/B summaries, display formatting, and plots.
"""

from pathlib import Path
from math import erfc, sqrt
from numbers import Number
import os
import tempfile

# Matplotlib can try to write config files under the user's home directory.
# Point it at /tmp so notebook execution works in restricted environments too.
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "marketplaats-matplotlib"))

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from matplotlib.colors import LinearSegmentedColormap
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ASSIGNMENT_DIR = Path(__file__).resolve().parent
DATA_FILENAME = "Adevinta Cars Dataset May 2019.csv"
DATA_PATH = ASSIGNMENT_DIR / "data" / DATA_FILENAME
LEGACY_DATA_PATH = PROJECT_ROOT / "data" / DATA_FILENAME

MISSING_VALUE_MARKERS = ["?"]
VALID_GROUPS = ["A", "B"]
SIGNIFICANCE_LEVEL = 0.05
TWO_SIDED_Z_CRITICAL_95 = 1.96

METRIC_COLUMNS = ["telclicks", "bids", "n_asq", "webclicks"]
IMPORTANT_COLUMNS = [
    "src_ad_id",
    "telclicks",
    "bids",
    "carrosserie",
    "photo_cnt",
    "aantaldeuren",
    "n_asq",
    "bouwjaar",
    "emissie",
    "energielabel",
    "brand",
    "ad_start_dt",
    "vermogen",
    "webclicks",
    "model",
    "aantalstoelen",
    "price",
    "group",
]
NUMERIC_DIMENSION_COLUMNS = [
    "price",
    "kmstand",
    "days_live",
    "photo_cnt",
    "bouwjaar",
    "aantaldeuren",
    "aantalstoelen",
    "emissie",
    "vermogen",
]
CATEGORICAL_DIMENSION_COLUMNS = [
    "brand",
    "model",
    "kleur",
    "carrosserie",
    "energielabel",
]
UNDOCUMENTED_COLUMN_NOTES = {
    "kleur": "used as an optional car-color dimension",
    "kmstand": "used as an optional mileage dimension",
    "days_live": "used as an optional ad-tenure dimension",
    "l2": "not used; meaning is unclear",
}
NUMERIC_IMPORT_COLUMNS = sorted(set(METRIC_COLUMNS + NUMERIC_DIMENSION_COLUMNS + ["l2"]))
SEGMENT_SOURCE_COLUMNS = {
    "price_band": "price",
    "km_band": "kmstand",
    "car_age_band": "car_age",
    "photo_count_band": "photo_cnt",
}
PLOT_COLORS = {
    "A": "#3B6EA8",
    "B": "#D65F3D",
    "diff": "#2F8F6B",
    "neutral": "#7A8491",
    "accent": "#8E6BBE",
    "grid": "#D9DEE7",
    "axis": "#AEB6C2",
    "text": "#222831",
    "background": "#FFFFFF",
}
PLOT_COLOR_CYCLE = [
    PLOT_COLORS["A"],
    PLOT_COLORS["B"],
    PLOT_COLORS["diff"],
    PLOT_COLORS["accent"],
    PLOT_COLORS["neutral"],
]
NUMERIC_BALANCE_AXIS_LABELS = {
    "aantaldeuren": "Aantal Deuren (Doors)",
    "aantalstoelen": "Aantal Stoelen (Seats)",
    "bouwjaar": "Bouwjaar (Build Year)",
    "car_age": "Car Age",
    "days_live": "Days Live",
    "emissie": "Emissie (Emissions)",
    "kmstand": "Kmstand (Mileage)",
    "photo_cnt": "Photo Count",
    "price": "Price",
    "vermogen": "Vermogen (Power)",
}

# Main analysis flow:
# 1. Load and prepare data: read_ab_test_data, prepare_ab_data, prepare_insight_data.
# 2. Measure A/B outcome: lead_outcome_summary, lead_rate_lift, lead_rate_inference.
# 3. Check validity: assignment_srm_summary, lead_metric_quality,
#    missing_lead_metric_sensitivity, duplicated_ad_id_sensitivity,
#    numeric_balance_summary, categorical_balance_overview.
# 4. Describe segments: add_segments, segment_outcome_summary,
#    lead_channel_mix, lead_concentration_summary, segment_insight_summary.


# ---------------------------------------------------------------------------
# General utilities
# ---------------------------------------------------------------------------


def format_percentage(series_or_number):
    """Format shares consistently for readable notebook/script output."""
    if pd.isna(series_or_number):
        return pd.NA
    return f"{series_or_number:.2%}"


def pct(series_or_number):
    """Backward-compatible short alias for percentage formatting."""
    return format_percentage(series_or_number)


def set_plot_style():
    """Apply the shared notebook visual style for charts and exports."""
    plt.rcParams.update(
        {
            "axes.prop_cycle": plt.cycler(color=PLOT_COLOR_CYCLE),
            "figure.facecolor": PLOT_COLORS["background"],
            "axes.facecolor": PLOT_COLORS["background"],
            "savefig.facecolor": PLOT_COLORS["background"],
            "axes.edgecolor": PLOT_COLORS["axis"],
            "axes.labelcolor": PLOT_COLORS["text"],
            "axes.titlecolor": PLOT_COLORS["text"],
            "text.color": PLOT_COLORS["text"],
            "xtick.color": PLOT_COLORS["text"],
            "ytick.color": PLOT_COLORS["text"],
            "grid.color": PLOT_COLORS["grid"],
            "grid.linewidth": 0.8,
            "legend.frameon": False,
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
        }
    )


def apply_plot_style():
    """Backward-compatible alias for `set_plot_style`."""
    set_plot_style()


def infer_numeric_dtype(series):
    """Convert a messy CSV column to numeric while preserving integer columns."""
    numeric_series = pd.to_numeric(series, errors="coerce")
    non_missing_values = numeric_series.dropna()

    if non_missing_values.mod(1).eq(0).all():
        integer_dtype = "Int64" if numeric_series.hasnans else "int64"
        return numeric_series.astype(integer_dtype)

    return numeric_series


# ---------------------------------------------------------------------------
# Data loading and preparation
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Data quality summaries
# ---------------------------------------------------------------------------


def column_quality_summary(dataframe, columns=IMPORTANT_COLUMNS):
    """Summarize missingness, dtype, and cardinality for selected columns."""
    columns = existing_columns(dataframe, columns)
    scoped_data = dataframe[columns]
    summary = pd.DataFrame(
        {
            "column": scoped_data.columns,
            "dtype": scoped_data.dtypes.astype(str).values,
            "missing_rows": scoped_data.isna().sum().values,
            "missing_pct": scoped_data.isna().mean().values,
            "unique_values": scoped_data.nunique(dropna=True).values,
        }
    )
    return summary.sort_values(["missing_pct", "column"], ascending=[False, True]).reset_index(drop=True)


def data_quality_checks(dataframe):
    """Return high-level row, column, and duplicate-ID checks."""
    duplicated_ad_rows = dataframe["src_ad_id"].duplicated(keep=False).sum()
    return pd.DataFrame(
        {
            "check": [
                "rows",
                "columns",
                "fully_duplicated_rows",
                "rows_with_duplicated_ad_id",
                "unique_ad_ids",
            ],
            "value": [
                len(dataframe),
                dataframe.shape[1],
                int(dataframe.duplicated().sum()),
                int(duplicated_ad_rows),
                int(dataframe["src_ad_id"].nunique(dropna=True)),
            ],
        }
    )


def undocumented_column_notes(dataframe):
    """List columns outside the documented analysis set with short notes."""
    rows = []
    for column in dataframe.columns:
        if column not in IMPORTANT_COLUMNS:
            rows.append(
                {
                    "column": column,
                    "note": UNDOCUMENTED_COLUMN_NOTES.get(column, "not used in this analysis"),
                }
            )
    return pd.DataFrame(rows)


def duplicated_ad_id_rows(dataframe, columns=IMPORTANT_COLUMNS):
    """Return all rows whose ad ID appears more than once."""
    columns = existing_columns(dataframe, columns)
    return (
        dataframe.loc[dataframe["src_ad_id"].duplicated(keep=False)]
        .sort_values(["src_ad_id", "group"])
        [columns]
        .reset_index(drop=True)
    )


def duplicated_ad_id_differences(dataframe, columns=IMPORTANT_COLUMNS):
    """Show which fields differ within each duplicated ad ID."""
    columns = existing_columns(dataframe, columns)
    duplicate_rows = duplicated_ad_id_rows(dataframe, columns=columns)
    rows = []

    for ad_id, group in duplicate_rows.groupby("src_ad_id", dropna=False):
        varying_columns = [
            column
            for column in columns
            if group[column].nunique(dropna=False) > 1
        ]
        rows.append(
            {
                "src_ad_id": ad_id,
                "rows": len(group),
                "groups_seen": ", ".join(sorted(group["group"].dropna().astype(str).unique())),
                "varying_columns": ", ".join(varying_columns),
            }
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Assignment integrity and lead metric checks
# ---------------------------------------------------------------------------


def group_size_summary(dataframe):
    """Count rows by assignment status and compute each row share."""
    assignment_status = dataframe["group"].where(dataframe["group"].isin(VALID_GROUPS), "Unassigned")
    summary = assignment_status.value_counts().rename_axis("group").reset_index(name="rows")
    group_order = pd.Categorical(summary["group"], categories=VALID_GROUPS + ["Unassigned"], ordered=True)
    summary = summary.assign(group_order=group_order).sort_values("group_order").drop(columns="group_order")
    summary["share"] = summary["rows"] / len(dataframe)
    return summary


def assignment_srm_summary(dataframe, expected_a_share=0.5):
    """Run a sample-ratio mismatch check for A/B-assigned rows."""
    group_sizes = group_size_summary(dataframe).set_index("group")
    a_rows = int(group_sizes.loc["A", "rows"])
    b_rows = int(group_sizes.loc["B", "rows"])
    ab_rows = a_rows + b_rows
    expected = pd.Series({"A": ab_rows * expected_a_share, "B": ab_rows * (1 - expected_a_share)})
    observed = pd.Series({"A": a_rows, "B": b_rows})
    chi_square = ((observed - expected) ** 2 / expected).sum()
    p_value = erfc(sqrt(chi_square / 2))

    return pd.DataFrame(
        {
            "metric": [
                "expected_A_share",
                "A rows",
                "B rows",
                "A share of assigned rows",
                "B share of assigned rows",
                "Sample-ratio p-value",
            ],
            "value": [
                expected_a_share,
                a_rows,
                b_rows,
                a_rows / ab_rows,
                b_rows / ab_rows,
                p_value,
            ],
        }
    )


def excluded_group_summary(raw_data, excluded_data):
    """Summarize how many raw rows are excluded from the A/B comparison."""
    dropped_rows = len(excluded_data)
    return pd.DataFrame(
        {
            "metric": ["raw_rows", "valid_ab_rows", "excluded_missing_group_rows"],
            "rows": [len(raw_data), len(raw_data) - dropped_rows, dropped_rows],
            "share_of_raw_rows": [1.0, (len(raw_data) - dropped_rows) / len(raw_data), dropped_rows / len(raw_data)],
        }
    )


def lead_metric_quality(dataframe):
    """Check missing, negative, zero, and max values for lead-event columns."""
    metric_columns = existing_columns(dataframe, METRIC_COLUMNS)
    return pd.DataFrame(
        {
            "metric": metric_columns,
            "missing_rows": [int(dataframe[column].isna().sum()) for column in metric_columns],
            "missing_pct": [dataframe[column].isna().mean() for column in metric_columns],
            "negative_rows": [int((dataframe[column] < 0).sum()) for column in metric_columns],
            "zero_rows": [int((dataframe[column] == 0).sum()) for column in metric_columns],
            "max_value": [dataframe[column].max() for column in metric_columns],
        }
    )


def missing_lead_metric_sensitivity(raw_data):
    """Check whether the missing-as-zero KPI choice changes the A/B conclusion."""
    metric_columns = existing_columns(raw_data, METRIC_COLUMNS)
    primary_ab_data, _ = prepare_ab_data(raw_data)
    complete_raw_data = raw_data.loc[
        raw_data["group"].isin(VALID_GROUPS) & raw_data[metric_columns].notna().all(axis=1)
    ].copy()
    complete_ab_data, _ = prepare_ab_data(complete_raw_data)

    primary = lead_rate_lift(primary_ab_data).set_index("metric")["value"]
    complete = lead_rate_lift(complete_ab_data).set_index("metric")["value"]
    dropped_rows = len(primary_ab_data) - len(complete_ab_data)

    return pd.DataFrame(
        {
            "metric": [
                "rows",
                "rows_dropped",
                "pct_rows_dropped",
                "A lead rate",
                "B lead rate",
                "B minus A lead-rate difference",
                "Relative lift vs A",
            ],
            "missing_as_zero": [
                len(primary_ab_data),
                0,
                0,
                primary["A lead rate"],
                primary["B lead rate"],
                primary["B minus A lead-rate difference"],
                primary["Relative lift vs A"],
            ],
            "excluding_missing_metric_rows": [
                len(complete_ab_data),
                dropped_rows,
                dropped_rows / len(primary_ab_data),
                complete["A lead rate"],
                complete["B lead rate"],
                complete["B minus A lead-rate difference"],
                complete["Relative lift vs A"],
            ],
        }
    )


# ---------------------------------------------------------------------------
# A/B outcome measurement
# ---------------------------------------------------------------------------


def lead_outcome_summary(dataframe):
    """Aggregate primary and supporting lead outcomes by A/B group.

    This is the source table for the result: `lead_rate` is the share of ads
    with at least one lead, while channel averages show where the lift comes from.
    """
    return (
        dataframe.groupby("group")
        .agg(
            ads=("src_ad_id", "count"),
            ads_with_any_lead=("has_any_lead", "sum"),
            lead_rate=("has_any_lead", "mean"),
            avg_total_leads=("total_leads", "mean"),
            median_total_leads=("total_leads", "median"),
            avg_telclicks=("telclicks", "mean"),
            avg_bids=("bids", "mean"),
            avg_questions=("n_asq", "mean"),
            avg_webclicks=("webclicks", "mean"),
        )
        .reset_index()
    )


def lead_rate_lift(dataframe):
    """Compute B-minus-A lead-rate lift and an unpooled normal-approximation CI."""
    by_group = lead_outcome_summary(dataframe).set_index("group")
    a = by_group.loc["A"]
    b = by_group.loc["B"]
    diff = b["lead_rate"] - a["lead_rate"]
    relative_lift = diff / a["lead_rate"]
    standard_error = (
        (a["lead_rate"] * (1 - a["lead_rate"]) / a["ads"])
        + (b["lead_rate"] * (1 - b["lead_rate"]) / b["ads"])
    ) ** 0.5

    return pd.DataFrame(
        {
            "metric": [
                "A lead rate",
                "B lead rate",
                "B minus A lead-rate difference",
                "Relative lift vs A",
                "Approx. 95% CI lower for difference",
                "Approx. 95% CI upper for difference",
            ],
            "value": [
                a["lead_rate"],
                b["lead_rate"],
                diff,
                relative_lift,
                diff - TWO_SIDED_Z_CRITICAL_95 * standard_error,
                diff + TWO_SIDED_Z_CRITICAL_95 * standard_error,
            ],
        }
    )


def lead_rate_inference(dataframe):
    """Run the primary two-proportion z-test for `has_any_lead`.

    The confidence interval uses the unpooled standard error; the p-value uses
    the pooled null standard error for equal A/B lead rates.
    """
    by_group = lead_outcome_summary(dataframe).set_index("group")
    a = by_group.loc["A"]
    b = by_group.loc["B"]

    a_leads = int(a["ads_with_any_lead"])
    b_leads = int(b["ads_with_any_lead"])
    a_ads = int(a["ads"])
    b_ads = int(b["ads"])
    diff = b["lead_rate"] - a["lead_rate"]

    unpooled_standard_error = (
        (a["lead_rate"] * (1 - a["lead_rate"]) / a_ads)
        + (b["lead_rate"] * (1 - b["lead_rate"]) / b_ads)
    ) ** 0.5
    pooled_rate = (a_leads + b_leads) / (a_ads + b_ads)
    pooled_standard_error = (
        pooled_rate
        * (1 - pooled_rate)
        * ((1 / a_ads) + (1 / b_ads))
    ) ** 0.5
    z_stat = diff / pooled_standard_error
    two_sided_p_value = erfc(abs(z_stat) / sqrt(2))

    return pd.DataFrame(
        {
            "metric": [
                "Significance level",
                "A ads with leads",
                "A ads",
                "A lead rate",
                "B ads with leads",
                "B ads",
                "B lead rate",
                "B minus A lead-rate difference",
                "Approx. 95% CI lower for difference",
                "Approx. 95% CI upper for difference",
                "z statistic",
                "Two-sided p-value",
            ],
            "value": [
                SIGNIFICANCE_LEVEL,
                a_leads,
                a_ads,
                a["lead_rate"],
                b_leads,
                b_ads,
                b["lead_rate"],
                diff,
                diff - TWO_SIDED_Z_CRITICAL_95 * unpooled_standard_error,
                diff + TWO_SIDED_Z_CRITICAL_95 * unpooled_standard_error,
                z_stat,
                two_sided_p_value,
            ],
        }
    )


def duplicated_ad_id_sensitivity(dataframe):
    """Check whether duplicated ad IDs drive the measured A/B lift."""
    without_duplicate_ids = dataframe.loc[~dataframe["src_ad_id"].duplicated(keep=False)].copy()
    dropped_rows = len(dataframe) - len(without_duplicate_ids)
    primary = lead_rate_lift(dataframe).set_index("metric")["value"]
    sensitivity = lead_rate_lift(without_duplicate_ids).set_index("metric")["value"]

    return pd.DataFrame(
        {
            "metric": [
                "rows",
                "rows_dropped",
                "pct_rows_dropped",
                "A lead rate",
                "B lead rate",
                "B minus A lead-rate difference",
                "Relative lift vs A",
            ],
            "with_duplicate_id_rows": [
                len(dataframe),
                0,
                0,
                primary["A lead rate"],
                primary["B lead rate"],
                primary["B minus A lead-rate difference"],
                primary["Relative lift vs A"],
            ],
            "excluding_duplicate_id_rows": [
                len(without_duplicate_ids),
                dropped_rows,
                dropped_rows / len(dataframe),
                sensitivity["A lead rate"],
                sensitivity["B lead rate"],
                sensitivity["B minus A lead-rate difference"],
                sensitivity["Relative lift vs A"],
            ],
        }
    )


def duplicate_id_sensitivity(dataframe):
    """Backward-compatible alias for `duplicated_ad_id_sensitivity`."""
    return duplicated_ad_id_sensitivity(dataframe)


def lead_distribution_summary(dataframe):
    """Describe the distribution of total lead counts per ad."""
    summary = dataframe["total_leads"].describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.95, 0.99]).reset_index()
    summary.columns = ["metric", "value"]
    return summary


# ---------------------------------------------------------------------------
# A/B balance and segment analysis
# ---------------------------------------------------------------------------


def numeric_balance_summary(dataframe):
    """Compare A/B assignment balance for numeric pre-outcome dimensions."""
    dimension_columns = existing_columns(dataframe, NUMERIC_DIMENSION_COLUMNS + ["car_age"])
    summary = dataframe.groupby("group")[dimension_columns].mean().T.reset_index().rename(columns={"index": "dimension"})
    if {"A", "B"}.issubset(summary.columns):
        summary["diff_B_minus_A"] = summary["B"] - summary["A"]
        summary["pct_diff_vs_A"] = summary["diff_B_minus_A"] / summary["A"]
        group_std = dataframe.groupby("group")[dimension_columns].std().T
        pooled_std = (((group_std["A"] ** 2) + (group_std["B"] ** 2)) / 2) ** 0.5
        summary["standardized_diff"] = summary["diff_B_minus_A"] / pooled_std.values
    return summary


def categorical_balance_summary(dataframe, column, top_n=8):
    """Compare group shares for the most common values in a categorical column."""
    category_values = dataframe[column].astype("object").where(dataframe[column].notna(), "Missing")
    top_values = category_values.value_counts(dropna=False).head(top_n).index
    filtered = dataframe.loc[category_values.isin(top_values)].copy()
    filtered_category_values = category_values.loc[filtered.index]
    counts = pd.crosstab(filtered_category_values, filtered["group"], dropna=False)
    shares = counts.div(dataframe["group"].value_counts(), axis=1)
    summary = shares.reset_index()
    summary = summary.rename(columns={summary.columns[0]: column})
    if {"A", "B"}.issubset(summary.columns):
        summary["share_diff_B_minus_A"] = summary["B"] - summary["A"]
    return summary


def categorical_balance_overview(dataframe, top_n=8):
    """Surface the largest categorical A/B balance gap per dimension."""
    rows = []
    for column in existing_columns(dataframe, CATEGORICAL_DIMENSION_COLUMNS):
        summary = categorical_balance_summary(dataframe, column, top_n=top_n)
        if "share_diff_B_minus_A" not in summary.columns or summary.empty:
            continue
        largest_gap = summary.assign(abs_share_diff=summary["share_diff_B_minus_A"].abs()).sort_values(
            "abs_share_diff",
            ascending=False,
        ).iloc[0]
        rows.append(
            {
                "dimension": column,
                "largest_category_gap": largest_gap[column],
                "share_A": largest_gap["A"],
                "share_B": largest_gap["B"],
                "share_diff_B_minus_A": largest_gap["share_diff_B_minus_A"],
            }
        )
    return pd.DataFrame(rows)


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


def segment_coverage_summary(dataframe, segment_columns):
    """Show how many rows are usable for each segment cut."""
    rows = []
    for column in segment_columns:
        source_column = SEGMENT_SOURCE_COLUMNS.get(column, column)
        used_rows = dataframe[column].notna().sum()
        dropped_rows = len(dataframe) - used_rows
        missing_source_rows = dataframe[source_column].isna().sum() if source_column in dataframe.columns else pd.NA
        out_of_band_rows = (
            dataframe[source_column].notna().sum() - used_rows
            if source_column in dataframe.columns
            else pd.NA
        )
        rows.append(
            {
                "segment": column,
                "source_column": source_column,
                "rows_used": used_rows,
                "rows_dropped": dropped_rows,
                "missing_source_rows": missing_source_rows,
                "out_of_band_rows": out_of_band_rows,
                "pct_rows_dropped": dropped_rows / len(dataframe),
            }
        )
    return pd.DataFrame(rows)


def segment_outcome_summary(dataframe, segment_column, min_ads_per_group=200):
    """Summarize A/B lift inside one segment and flag small cells."""
    summary = (
        dataframe.dropna(subset=[segment_column])
        .groupby([segment_column, "group"], observed=True)
        .agg(
            ads=("src_ad_id", "count"),
            lead_rate=("has_any_lead", "mean"),
            avg_total_leads=("total_leads", "mean"),
        )
        .reset_index()
    )

    wide = summary.pivot(index=segment_column, columns="group", values=["ads", "lead_rate", "avg_total_leads"])
    wide.columns = [f"{metric}_{group}" for metric, group in wide.columns]
    wide = wide.reset_index()

    if {"lead_rate_A", "lead_rate_B"}.issubset(wide.columns):
        wide["lead_rate_diff_B_minus_A"] = wide["lead_rate_B"] - wide["lead_rate_A"]
        wide["relative_lift_vs_A"] = wide["lead_rate_diff_B_minus_A"] / wide["lead_rate_A"]

    if {"ads_A", "ads_B"}.issubset(wide.columns):
        wide["small_segment_flag"] = (wide["ads_A"] < min_ads_per_group) | (wide["ads_B"] < min_ads_per_group)

    return wide


def top_category_segment_summary(dataframe, column, top_n=8, min_ads_per_group=200):
    """Run segment outcome summaries for the most frequent category values."""
    top_values = dataframe[column].value_counts().head(top_n).index
    filtered = dataframe.loc[dataframe[column].isin(top_values)].copy()
    return segment_outcome_summary(filtered, column, min_ads_per_group=min_ads_per_group)


# ---------------------------------------------------------------------------
# Question 3: descriptive lead insights
# ---------------------------------------------------------------------------


def q3_row_summary(raw_data, ab_data, excluded_data):
    """Summarize row counts used by q3 and carried over from q2."""
    return pd.DataFrame(
        {
            "metric": [
                "Rows available for q3 insights",
                "Rows assigned to A/B groups in q2",
                "Rows not assigned to an A/B group",
            ],
            "rows": [len(raw_data), len(ab_data), len(excluded_data)],
            "share_of_raw_rows": [1.0, len(ab_data) / len(raw_data), len(excluded_data) / len(raw_data)],
        }
    )


def lead_channel_mix(dataframe):
    """Show which lead channels contribute the most lead events."""
    metric_columns = existing_columns(dataframe, METRIC_COLUMNS)
    total_lead_events = dataframe[metric_columns].sum().sum()
    rows = []

    for column in metric_columns:
        rows.append(
            {
                "channel": DISPLAY_VALUE_ALIASES.get(column, column),
                "rows_with_event": int(dataframe[column].gt(0).sum()),
                "share_of_ads_with_event": dataframe[column].gt(0).mean(),
                "average_events_per_ad": dataframe[column].mean(),
                "share_of_all_lead_events": dataframe[column].sum() / total_lead_events,
            }
        )

    return pd.DataFrame(rows).sort_values("share_of_all_lead_events", ascending=False)


def lead_channel_mix_by_segment(dataframe, segment_column):
    """Return lead-channel event share within each segment value."""
    metric_columns = existing_columns(dataframe, METRIC_COLUMNS)
    channel_events = (
        dataframe.dropna(subset=[segment_column])
        .groupby(segment_column, observed=True)[metric_columns]
        .sum()
    )
    channel_share = channel_events.div(channel_events.sum(axis=1), axis=0)
    return channel_share.rename(columns=DISPLAY_VALUE_ALIASES)


def lead_concentration_summary(dataframe):
    """Return headline figures for skew and concentration of lead volume."""
    top_decile_cutoff = dataframe["total_leads"].quantile(0.90)
    top_decile = dataframe.loc[dataframe["total_leads"] >= top_decile_cutoff]

    return pd.DataFrame(
        {
            "metric": [
                "Ads with at least one lead",
                "Median total leads",
                "P90 total leads",
                "P99 total leads",
                "Lead events from top-decile ads",
            ],
            "value": [
                dataframe["has_any_lead"].mean(),
                dataframe["total_leads"].median(),
                dataframe["total_leads"].quantile(0.90),
                dataframe["total_leads"].quantile(0.99),
                top_decile["total_leads"].sum() / dataframe["total_leads"].sum(),
            ],
        }
    )


def lead_concentration_curve(dataframe, cutoffs=(0.01, 0.05, 0.10, 0.20)):
    """Prepare ranked cumulative lead-share data plus selected cutoff points."""
    ranked = dataframe.sort_values("total_leads", ascending=False).reset_index(drop=True)
    ranked["ad_share"] = (ranked.index + 1) / len(ranked)
    ranked["lead_share"] = ranked["total_leads"].cumsum() / ranked["total_leads"].sum()

    cutoff_rows = []
    for ad_share in cutoffs:
        row_count = int(len(ranked) * ad_share)
        cutoff_rows.append(
            {
                "top_ad_share": ad_share,
                "ads": row_count,
                "lead_event_share": ranked.loc[: row_count - 1, "total_leads"].sum()
                / ranked["total_leads"].sum(),
            }
        )

    return ranked, pd.DataFrame(cutoff_rows)


def listing_quality_summary(dataframe):
    """Summarize lead outcomes by photo-count band."""
    summary = (
        dataframe.dropna(subset=["photo_count_band"])
        .groupby("photo_count_band", observed=True)
        .agg(
            ads=("src_ad_id", "count"),
            lead_rate=("has_any_lead", "mean"),
            avg_total_leads=("total_leads", "mean"),
            median_days_live=("days_live", "median"),
            median_price=("price", "median"),
        )
        .reset_index()
    )
    summary["share_of_ads"] = summary["ads"] / len(dataframe)
    return summary


def segment_insight_summary(dataframe, segment_column, min_ads=500):
    """Summarize descriptive q3 lead outcomes for one business segment."""
    summary = (
        dataframe.dropna(subset=[segment_column])
        .groupby(segment_column, observed=True)
        .agg(
            ads=("src_ad_id", "count"),
            lead_rate=("has_any_lead", "mean"),
            avg_total_leads=("total_leads", "mean"),
            median_price=("price", "median"),
            median_photos=("photo_cnt", "median"),
        )
        .reset_index()
    )
    summary = summary.loc[summary["ads"] >= min_ads].copy()
    summary["share_of_ads"] = summary["ads"] / len(dataframe)
    return summary.sort_values("lead_rate", ascending=False)


def segment_benchmark_summary(dataframe, segment_column, min_ads=500):
    """Summarize one segment band with medians for the other benchmark dimensions."""
    median_columns = {
        "price_band": {
            "median_car_age": ("car_age", "median"),
            "median_mileage": ("kmstand", "median"),
        },
        "km_band": {
            "median_price": ("price", "median"),
            "median_car_age": ("car_age", "median"),
        },
        "car_age_band": {
            "median_price": ("price", "median"),
            "median_mileage": ("kmstand", "median"),
        },
    }
    aggregations = {
        "ads": ("src_ad_id", "count"),
        "lead_rate": ("has_any_lead", "mean"),
        "avg_total_leads": ("total_leads", "mean"),
        **median_columns.get(segment_column, {}),
    }
    summary = (
        dataframe.dropna(subset=[segment_column])
        .groupby(segment_column, observed=True)
        .agg(**aggregations)
        .reset_index()
    )
    summary = summary.loc[summary["ads"] >= min_ads].copy()
    summary["share_of_ads"] = summary["ads"] / len(dataframe)
    return summary.sort_values("lead_rate", ascending=False)


def time_scope_summary(dataframe):
    """Summarize date coverage and listing tenure in the q3 data."""
    return pd.DataFrame(
        {
            "metric": [
                "Earliest ad start",
                "Latest ad start",
                "Days live median",
                "Days live p90",
                "Days live max",
            ],
            "value": [
                dataframe["ad_start_dt"].min(),
                dataframe["ad_start_dt"].max(),
                dataframe["days_live"].median(),
                dataframe["days_live"].quantile(0.90),
                dataframe["days_live"].max(),
            ],
        }
    )


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


def lifecycle_summary(dataframe):
    """Summarize descriptive q3 lead outcomes by listing age band."""
    summary = (
        dataframe.dropna(subset=["days_live_band"])
        .groupby("days_live_band", observed=True)
        .agg(
            ads=("src_ad_id", "count"),
            lead_rate=("has_any_lead", "mean"),
            avg_total_leads=("total_leads", "mean"),
            median_total_leads=("total_leads", "median"),
            median_price=("price", "median"),
            median_photos=("photo_cnt", "median"),
        )
        .reset_index()
    )
    summary["share_of_ads"] = summary["ads"] / len(dataframe)
    return summary


def weekday_summary(dataframe):
    """Summarize lead outcomes by ad start weekday."""
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    summary = (
        dataframe.groupby("start_weekday")
        .agg(
            ads=("src_ad_id", "count"),
            lead_rate=("has_any_lead", "mean"),
            avg_total_leads=("total_leads", "mean"),
            median_days_live=("days_live", "median"),
            median_price=("price", "median"),
        )
        .reindex(weekday_order)
        .reset_index()
    )
    summary["share_of_ads"] = summary["ads"] / len(dataframe)
    return summary


def fresh_stale_summary(dataframe):
    """Summarize lead outcomes by broad listing lifecycle stage."""
    summary = (
        dataframe.groupby("listing_lifecycle_stage", observed=True)
        .agg(
            ads=("src_ad_id", "count"),
            lead_rate=("has_any_lead", "mean"),
            avg_total_leads=("total_leads", "mean"),
            median_total_leads=("total_leads", "median"),
            median_price=("price", "median"),
            median_photos=("photo_cnt", "median"),
            median_mileage=("kmstand", "median"),
        )
        .reset_index()
    )
    summary["share_of_ads"] = summary["ads"] / len(dataframe)
    return summary


def lead_profile_summary(dataframe, numeric_fields=None):
    """Compare median ad characteristics for ads with and without leads."""
    if numeric_fields is None:
        numeric_fields = ["price", "kmstand", "car_age", "photo_cnt", "days_live", "vermogen"]

    lead_profile = (
        dataframe.groupby("has_any_lead")[numeric_fields]
        .median()
        .T
        .rename(columns={False: "no_lead_median", True: "lead_median"})
        .reset_index()
        .rename(columns={"index": "dimension"})
    )
    lead_profile["difference_lead_minus_no_lead"] = lead_profile["lead_median"] - lead_profile["no_lead_median"]
    lead_profile["pct_difference_vs_no_lead"] = (
        lead_profile["difference_lead_minus_no_lead"] / lead_profile["no_lead_median"]
    )
    return lead_profile


def business_insight_table(ab_data):
    """Create a compact, text-friendly business insight table."""
    lift = lead_rate_lift(ab_data).set_index("metric")["value"]
    outcomes = lead_outcome_summary(ab_data).set_index("group")
    numeric_balance = numeric_balance_summary(ab_data)
    largest_numeric_gap = (
        numeric_balance.assign(abs_standardized_diff=numeric_balance["standardized_diff"].abs())
        .sort_values("abs_standardized_diff", ascending=False)
        .iloc[0]
    )
    largest_numeric_gap_label = NUMERIC_BALANCE_AXIS_LABELS.get(
        largest_numeric_gap["dimension"],
        format_table_header(largest_numeric_gap["dimension"]),
    )

    return pd.DataFrame(
        {
            "topic": [
                "Primary outcome",
                "Statistical inference",
                "Lead volume",
                "Group balance",
                "Interpretation",
            ],
            "insight": [
                f"B has a {format_percentage(lift['B minus A lead-rate difference'])} higher share of ads with any lead than A ({format_percentage(lift['Relative lift vs A'])} relative lift).",
                "At a 5% significance level, the B-A lead-rate gap is statistically significant (p < 0.001).",
                f"B also has higher average total leads per ad ({outcomes.loc['B', 'avg_total_leads']:.3f} vs {outcomes.loc['A', 'avg_total_leads']:.3f}).",
                f"The largest standardized numeric balance gap is {largest_numeric_gap_label} ({largest_numeric_gap['standardized_diff']:.2f} standardized difference, B vs A).",
                "Group B is directionally positive. I would frame it as causal only if we confirm which group received the feature and validate the assignment setup.",
            ],
        }
    )


def business_insight_lines(ab_data):
    """Return the insight table as bullet lines for notebook output."""
    insights = business_insight_table(ab_data)
    return [
        f"- {row['topic'].title()}: {row['insight']}"
        for _, row in insights.iterrows()
    ]


def print_business_insights(ab_data):
    """Print the business insight bullets."""
    print("\n".join(business_insight_lines(ab_data)))


def print_section(title):
    """Print a simple console section heading."""
    print(f"\n{'=' * len(title)}")
    print(title)
    print(f"{'=' * len(title)}")


def lead_channel_coverage(dataframe):
    """Compute the share of rows with activity in each lead channel."""
    metric_columns = existing_columns(dataframe, METRIC_COLUMNS)
    coverage = pd.DataFrame(
        {
            "channel": metric_columns,
            "share_with_event": [dataframe[column].gt(0).mean() for column in metric_columns],
        }
    )
    coverage = pd.concat(
        [
            coverage,
            pd.DataFrame(
                {
                    "channel": ["any_lead"],
                    "share_with_event": [dataframe[metric_columns].gt(0).any(axis=1).mean()],
                }
            ),
        ],
        ignore_index=True,
    )
    coverage["channel"] = coverage["channel"].map(DISPLAY_VALUE_ALIASES).fillna(coverage["channel"])
    return coverage.sort_values("share_with_event")


def lift_summary_table(ab_data):
    """Format the primary lift and inference outputs for notebook display."""
    lift = lead_rate_lift(ab_data).set_index("metric")["value"]
    inference = lead_rate_inference(ab_data).set_index("metric")["value"]

    absolute_lift = lift["B minus A lead-rate difference"]
    ci_lower = lift["Approx. 95% CI lower for difference"]
    ci_upper = lift["Approx. 95% CI upper for difference"]
    relative_lift = lift["Relative lift vs A"]
    p_value = inference["Two-sided p-value"]
    significance_level = inference["Significance level"]

    return pd.DataFrame(
        {
            "Metric": [
                "Absolute lead-rate lift",
                "95% CI for absolute lift",
                "Relative lift vs A",
                "p-value",
                "Significance level",
            ],
            "Value": [
                f"{absolute_lift * 100:.1f} pp",
                f"{ci_lower * 100:.1f} to {ci_upper * 100:.1f} pp",
                f"{relative_lift:.1%}",
                "<0.001" if p_value < 0.001 else f"{p_value:.3f}",
                f"{significance_level:.0%}",
            ],
        }
    )


def group_colors(groups):
    """Map A/B group labels to the shared notebook palette."""
    return [PLOT_COLORS.get(group, PLOT_COLORS["neutral"]) for group in groups]


def signed_difference_colors(values):
    """Color positive differences green and negative differences orange."""
    return [PLOT_COLORS["diff"] if value >= 0 else PLOT_COLORS["B"] for value in values]


def plot_labeled_vertical_bars(
    ax,
    labels,
    values,
    title,
    ylabel=None,
    colors=None,
    percent_y=False,
    decimals=1,
    percent_labels=False,
):
    """Draw a simple labeled vertical bar chart with shared styling."""
    ax.bar(labels, values, color=colors)
    finish_plot(ax, title, xlabel=None, ylabel=ylabel, percent_y=percent_y)
    add_bar_labels(ax, percent=percent_labels, decimals=decimals)
    simplify_fully_labeled_bar_axis(ax)
    return ax


def plot_labeled_horizontal_bars(
    ax,
    labels,
    values,
    title,
    xlabel=None,
    colors=None,
    percent_x=False,
    decimals=1,
    percent_labels=False,
    zero_line=False,
):
    """Draw a simple labeled horizontal bar chart with shared styling."""
    ax.barh(labels, values, color=colors)
    if zero_line:
        ax.axvline(0, color=PLOT_COLORS["text"], linewidth=1)
    finish_plot(ax, title, xlabel=xlabel, ylabel=None, percent_x=percent_x)
    add_bar_labels(ax, percent=percent_labels, decimals=decimals, axis="horizontal")
    simplify_fully_labeled_bar_axis(ax, axis="horizontal")
    return ax


def finish_plot(ax, title, xlabel=None, ylabel=None, percent_x=False, percent_y=False):
    """Apply the shared q2 chart title, axis, grid, and percent formatting."""
    ax.set_facecolor(PLOT_COLORS["background"])
    ax.figure.set_facecolor(PLOT_COLORS["background"])
    ax.set_title(title, loc="left", fontweight="bold", pad=12, color=PLOT_COLORS["text"])
    if xlabel is not None:
        ax.set_xlabel(xlabel, color=PLOT_COLORS["text"])
    if ylabel is not None:
        ax.set_ylabel(ylabel, color=PLOT_COLORS["text"])
    if percent_x:
        ax.xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    if percent_y:
        ax.yaxis.set_major_formatter(mtick.PercentFormatter(1.0, decimals=0))
    ax.spines[["top", "right"]].set_visible(False)
    for spine in ax.spines.values():
        spine.set_color(PLOT_COLORS["axis"])
    ax.tick_params(colors=PLOT_COLORS["text"])
    ax.grid(axis="y", color=PLOT_COLORS["grid"], alpha=0.75)
    ax.grid(axis="x", visible=False)
    return ax


def add_bar_labels(ax, percent=False, decimals=1, axis="vertical"):
    """Annotate bar charts so axes can stay visually lightweight."""
    for patch in ax.patches:
        if axis == "vertical":
            value = patch.get_height()
            x = patch.get_x() + patch.get_width() / 2
            y = value
            label = f"{value:.{decimals}%}" if percent else f"{value:,.{decimals}f}"
            ax.annotate(
                label,
                (x, y),
                ha="center",
                va="bottom",
                xytext=(0, 4),
                textcoords="offset points",
                fontsize=9,
                color=PLOT_COLORS["text"],
            )
        else:
            value = patch.get_width()
            y = patch.get_y() + patch.get_height() / 2
            label = f"{value:.{decimals}%}" if percent else f"{value:,.{decimals}f}"
            if value < -0.025:
                offset = 6
                ha = "left"
            else:
                offset = 4 if value >= 0 else -4
                ha = "left" if value >= 0 else "right"
            ax.annotate(
                label,
                (value, y),
                ha=ha,
                va="center",
                xytext=(offset, 0),
                textcoords="offset points",
                fontsize=9,
                color=PLOT_COLORS["text"],
            )


def simplify_fully_labeled_bar_axis(ax, axis="vertical"):
    """Hide axis furniture when all bar values are labeled directly."""
    ax.grid(False)
    if axis == "vertical":
        ax.set_ylabel(None)
        ax.set_yticks([])
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_visible(False)
    else:
        ax.set_xlabel(None)
        ax.set_xticks([])
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
        ax.spines["bottom"].set_visible(False)


def plot_row_coverage(raw_data, ab_data, excluded_data):
    """Plot raw rows by experiment assignment status."""
    row_coverage = pd.DataFrame(
        {
            "status": ["A", "B", "Unassigned"],
            "rows": [
                int((raw_data["group"] == "A").sum()),
                int((raw_data["group"] == "B").sum()),
                len(excluded_data),
            ],
        }
    )
    row_coverage["share"] = row_coverage["rows"] / len(raw_data)

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(
        row_coverage["status"],
        row_coverage["rows"],
        color=[PLOT_COLORS["A"], PLOT_COLORS["B"], PLOT_COLORS["neutral"]],
    )
    finish_plot(ax, "Rows by experiment assignment", xlabel=None, ylabel="Rows")
    max_rows = row_coverage["rows"].max()

    for patch, (_, row) in zip(ax.patches, row_coverage.iterrows()):
        is_tall_bar = row["rows"] > max_rows * 0.5
        y = patch.get_height() * 0.96 if is_tall_bar else patch.get_height()
        va = "top" if is_tall_bar else "bottom"
        offset = -4 if is_tall_bar else 4
        label_color = "white" if is_tall_bar else None
        ax.annotate(
            f"{row['rows']:,.0f}\n{row['share']:.1%}",
            (patch.get_x() + patch.get_width() / 2, y),
            ha="center",
            va=va,
            xytext=(0, offset),
            textcoords="offset points",
            fontsize=9,
            color=label_color,
        )

    simplify_fully_labeled_bar_axis(ax)
    return fig, ax


def plot_lead_channel_coverage(dataframe):
    """Plot event coverage by lead channel and combined lead KPI."""
    coverage = lead_channel_coverage(dataframe)
    fig, ax = plt.subplots(figsize=(7, 4))
    plot_labeled_horizontal_bars(
        ax,
        coverage["channel"],
        coverage["share_with_event"],
        "Rows with at least one lead event",
        xlabel="Share of raw rows",
        colors=[PLOT_COLORS["neutral"] if channel == "Any Lead" else PLOT_COLORS["B"] for channel in coverage["channel"]],
        percent_x=True,
        percent_labels=True,
    )
    return fig, ax


def plot_lead_channel_mix_by_segment(channel_share, title):
    """Plot stacked lead-channel share by segment."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bottom = 0
    colors = [PLOT_COLORS["A"], PLOT_COLORS["B"], PLOT_COLORS["diff"], PLOT_COLORS["neutral"]]

    for color, channel in zip(colors, channel_share.columns):
        ax.bar(
            channel_share.index.astype(str),
            channel_share[channel],
            bottom=bottom,
            label=channel,
            color=color,
        )
        bottom = bottom + channel_share[channel]

    finish_plot(ax, title, xlabel=None, ylabel="Share of lead events", percent_y=True)
    ax.legend(title=None, frameon=False, bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    return fig, ax


def plot_group_sizes(dataframe):
    """Plot row counts by assignment status."""
    group_sizes = group_size_summary(dataframe).copy()
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(group_sizes["group"], group_sizes["rows"], color=group_colors(group_sizes["group"]))
    finish_plot(ax, "Rows by experiment assignment", xlabel=None, ylabel="Records")
    max_rows = group_sizes["rows"].max()

    for patch, (_, row) in zip(ax.patches, group_sizes.iterrows()):
        is_tall_bar = row["rows"] > max_rows * 0.5
        y = patch.get_height() * 0.96 if is_tall_bar else patch.get_height()
        va = "top" if is_tall_bar else "bottom"
        offset = -4 if is_tall_bar else 4
        label_color = "white" if is_tall_bar else None
        ax.annotate(
            f"{row['rows']:,.0f}\n{row['share']:.1%}",
            (patch.get_x() + patch.get_width() / 2, y),
            ha="center",
            va=va,
            xytext=(0, offset),
            textcoords="offset points",
            fontsize=9,
            color=label_color,
        )

    simplify_fully_labeled_bar_axis(ax)
    ax.set_xlabel("Group")
    return fig, ax


def plot_numeric_balance(dataframe):
    """Plot percent differences in numeric dimensions between B and A."""
    numeric_balance = numeric_balance_summary(dataframe).dropna(subset=["pct_diff_vs_A"]).copy()
    numeric_balance = numeric_balance.sort_values("pct_diff_vs_A")
    y_labels = numeric_balance["dimension"].map(
        lambda dimension: NUMERIC_BALANCE_AXIS_LABELS.get(dimension, format_table_header(dimension))
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    plot_labeled_horizontal_bars(
        ax,
        y_labels,
        numeric_balance["pct_diff_vs_A"],
        "How B differs from A",
        xlabel="Percent difference",
        colors=signed_difference_colors(numeric_balance["pct_diff_vs_A"]),
        percent_x=True,
        percent_labels=True,
        zero_line=True,
    )
    return fig, ax


def plot_lead_rate(outcomes):
    """Plot the primary KPI, lead rate by group."""
    fig, ax = plt.subplots(figsize=(6, 4))
    plot_labeled_vertical_bars(
        ax,
        outcomes["group"],
        outcomes["lead_rate"],
        "Share of ads with at least one lead",
        ylabel="Lead rate",
        colors=group_colors(outcomes["group"]),
        percent_y=True,
        percent_labels=True,
    )
    ax.set_xlabel("Group")
    return fig, ax


def plot_average_leads_by_channel(outcomes):
    """Plot average leads per ad by channel and group."""
    channel_columns = ["avg_telclicks", "avg_bids", "avg_questions", "avg_webclicks", "avg_total_leads"]
    channel_labels = ["Tel clicks", "Bids", "Questions", "Web clicks", "Total leads"]
    channel_plot = outcomes.set_index("group")[channel_columns].T
    channel_plot.index = channel_labels

    fig, ax = plt.subplots(figsize=(9, 5))
    channel_plot.plot(kind="bar", ax=ax, color=[PLOT_COLORS["A"], PLOT_COLORS["B"]])
    finish_plot(ax, "Average leads per ad by channel", xlabel=None, ylabel="Average per ad")
    add_bar_labels(ax, decimals=2)
    simplify_fully_labeled_bar_axis(ax)
    ax.tick_params(axis="x", rotation=0)
    ax.legend(title="Group", frameon=False)
    return fig, ax


def plot_total_leads_distribution(dataframe):
    """Plot the clipped total-leads distribution."""
    clip_at = dataframe["total_leads"].quantile(0.99)
    bins = range(0, int(clip_at) + 2)
    lead_data = dataframe["total_leads"].clip(upper=clip_at)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.hist(lead_data, bins=bins, density=True, color=PLOT_COLORS["neutral"], edgecolor="white", linewidth=0.5)
    finish_plot(
        ax,
        "Total leads per ad distribution",
        xlabel="Total leads per ad (clipped at p99)",
        ylabel="Density",
    )
    ax.text(0.98, 0.82, f"Clipped mean: {lead_data.mean():.2f}", transform=ax.transAxes, ha="right", fontsize=10)
    plt.tight_layout()
    return fig, ax


def plot_cumulative_lead_share(ranked_leads, cutoff_summary, highlighted_ad_share=0.10):
    """Plot cumulative lead events by ads ranked from highest to lowest lead count."""
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.plot(ranked_leads["ad_share"], ranked_leads["lead_share"], color=PLOT_COLORS["A"], linewidth=2.5)
    ax.plot([0, 1], [0, 1], color=PLOT_COLORS["axis"], linestyle="--", linewidth=1)
    finish_plot(
        ax,
        "Cumulative lead events by ranked ads",
        xlabel="Share of ads",
        ylabel="Share of lead events",
        percent_x=True,
        percent_y=True,
    )

    highlight = cutoff_summary.loc[cutoff_summary["top_ad_share"].eq(highlighted_ad_share)]
    if not highlight.empty:
        lead_share = highlight["lead_event_share"].iloc[0]
        rank_index = int(len(ranked_leads) * highlighted_ad_share) - 1
        ax.annotate(
            f"Top {highlighted_ad_share:.0%} of ads: {lead_share:.1%} of leads",
            xy=(highlighted_ad_share, ranked_leads.loc[rank_index, "lead_share"]),
            xytext=(0.22, 0.58),
            arrowprops={"arrowstyle": "->", "color": PLOT_COLORS["text"], "linewidth": 1},
            fontsize=10,
        )

    plt.tight_layout()
    return fig, ax


def plot_photo_count_lead_rate(listing_quality):
    """Plot lead rate by photo-count band."""
    fig, ax = plt.subplots(figsize=(7, 4))
    plot_labeled_vertical_bars(
        ax,
        listing_quality["photo_count_band"].astype(str),
        listing_quality["lead_rate"],
        "Lead rate by photo count",
        ylabel="Lead rate",
        colors=PLOT_COLORS["A"],
        percent_y=True,
        percent_labels=True,
    )
    return fig, ax


def plot_lifecycle_lead_rate(lifecycle):
    """Plot lead rate by days-live band."""
    fig, ax = plt.subplots(figsize=(8, 4))
    plot_labeled_vertical_bars(
        ax,
        lifecycle["days_live_band"].astype(str),
        lifecycle["lead_rate"],
        "Lead rate by days live band",
        ylabel="Lead rate",
        colors=PLOT_COLORS["A"],
        percent_y=True,
        percent_labels=True,
    )
    return fig, ax


def plot_weekday_lead_rate(weekday):
    """Plot lead rate by ad start weekday."""
    fig, ax = plt.subplots(figsize=(8, 4))
    plot_labeled_vertical_bars(
        ax,
        weekday["start_weekday"],
        weekday["lead_rate"],
        "Lead rate by ad start weekday",
        ylabel="Lead rate",
        colors=PLOT_COLORS["B"],
        percent_y=True,
        percent_labels=True,
    )
    ax.tick_params(axis="x", rotation=30)
    return fig, ax


def plot_lead_profile_differences(lead_profile):
    """Plot median characteristic differences for ads with leads vs no leads."""
    plot_profile = lead_profile.dropna(subset=["pct_difference_vs_no_lead"]).sort_values("pct_difference_vs_no_lead")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    plot_labeled_horizontal_bars(
        ax,
        plot_profile["dimension"].map(DISPLAY_VALUE_ALIASES).fillna(plot_profile["dimension"]),
        plot_profile["pct_difference_vs_no_lead"],
        "Median difference for ads with leads vs no leads",
        xlabel="Percent difference",
        colors=signed_difference_colors(plot_profile["pct_difference_vs_no_lead"]),
        percent_x=True,
        percent_labels=True,
        zero_line=True,
    )
    return fig, ax


def plot_duplicate_id_sensitivity(dataframe):
    """Plot whether duplicate-ID removal changes the lead-rate result."""
    sensitivity = duplicated_ad_id_sensitivity(dataframe).set_index("metric").loc[["A lead rate", "B lead rate"]]
    sensitivity = sensitivity.rename(index={"A lead rate": "A", "B lead rate": "B"}).T
    sensitivity = sensitivity.rename(
        index={
            "with_duplicate_id_rows": "With duplicate rows",
            "excluding_duplicate_id_rows": "Excluding duplicate rows",
        }
    )
    fig, ax = plt.subplots(figsize=(8, 4))
    sensitivity.plot(kind="bar", ax=ax, color=[PLOT_COLORS["A"], PLOT_COLORS["B"]])
    finish_plot(ax, "Duplicate-ID sensitivity", xlabel=None, ylabel="Lead rate", percent_y=True)
    add_bar_labels(ax, percent=True, decimals=1)
    simplify_fully_labeled_bar_axis(ax)
    ax.tick_params(axis="x", rotation=0)
    ax.legend(title=None, frameon=False)
    return fig, ax


def plot_segment_lift(dataframe, segment_column, lead_rate_title, lift_title):
    """Plot A/B lead rates and B-minus-A lift for one segment dimension."""
    summary = segment_outcome_summary(dataframe, segment_column)
    labels = summary[segment_column].astype(str)
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))

    axes[0].plot(labels, summary["lead_rate_A"], marker="o", color=PLOT_COLORS["A"], label="A")
    axes[0].plot(labels, summary["lead_rate_B"], marker="o", color=PLOT_COLORS["B"], label="B")
    finish_plot(axes[0], lead_rate_title, xlabel=None, ylabel="Lead rate", percent_y=True)
    axes[0].legend(title="Group", frameon=False)

    plot_labeled_vertical_bars(
        axes[1],
        labels,
        summary["lead_rate_diff_B_minus_A"],
        lift_title,
        ylabel="Lead-rate difference",
        colors=signed_difference_colors(summary["lead_rate_diff_B_minus_A"]),
        percent_y=True,
        percent_labels=True,
    )
    axes[1].axhline(0, color=PLOT_COLORS["text"], linewidth=1)
    plt.tight_layout()
    return fig, axes


def plot_top_category_lift(dataframe, column, title):
    """Plot lift for the most frequent values in a categorical column."""
    summary = top_category_segment_summary(dataframe, column).sort_values("lead_rate_diff_B_minus_A")
    fig, ax = plt.subplots(figsize=(8, 5))
    plot_labeled_horizontal_bars(
        ax,
        summary[column],
        summary["lead_rate_diff_B_minus_A"],
        title,
        xlabel="Lead-rate difference",
        colors=signed_difference_colors(summary["lead_rate_diff_B_minus_A"]),
        percent_x=True,
        percent_labels=True,
        zero_line=True,
    )
    return fig, ax


def plot_final_summary(outcomes):
    """Plot the two headline business metrics side by side."""
    summary_metrics = outcomes.set_index("group")[["lead_rate", "avg_total_leads"]].rename(
        columns={"lead_rate": "Lead rate", "avg_total_leads": "Avg total leads"}
    )
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    plot_labeled_vertical_bars(
        axes[0],
        summary_metrics.index,
        summary_metrics["Lead rate"],
        "Share of ads with at least one lead",
        ylabel="Lead rate",
        colors=group_colors(summary_metrics.index),
        percent_y=True,
        percent_labels=True,
    )

    plot_labeled_vertical_bars(
        axes[1],
        summary_metrics.index,
        summary_metrics["Avg total leads"],
        "Average total leads per ad",
        ylabel="Average total leads",
        colors=group_colors(summary_metrics.index),
        decimals=2,
    )

    for ax in axes:
        ax.tick_params(axis="x", rotation=0)

    plt.tight_layout()
    return fig, axes


# ---------------------------------------------------------------------------
# Display formatting
# ---------------------------------------------------------------------------


DECIMAL_FORMAT_COLUMN_KEYWORDS = [
    "avg",
    "diff",
    "lift",
    "mean",
    "median",
    "p-value",
    "pct",
    "rate",
    "share",
    "std",
]
TABLE_DECIMALS = 3
NO_THOUSANDS_SEPARATOR_COLUMN_KEYWORDS = ["jaar", "year"]
HEADER_WORD_REPLACEMENTS = {
    "a": "A",
    "ab": "A/B",
    "ads": "Ads",
    "avg": "Average",
    "b": "B",
    "ci": "CI",
    "diff": "Difference",
    "id": "ID",
    "kpi": "KPI",
    "of": "of",
    "pct": "Percent",
    "vs": "vs",
}
DISPLAY_HEADER_ALIASES = {
    "ad_start_dt": "Start Date",
    "ads_a": "Ad Count A",
    "ads_b": "Ad Count B",
    "ads_with_any_lead": "Ads With Leads",
    "aantaldeuren": "Doors",
    "aantalstoelen": "Seats",
    "avg_total_leads": "Avg Leads/Ad",
    "avg_total_leads_a": "Avg Leads/Ad A",
    "avg_total_leads_b": "Avg Leads/Ad B",
    "avg_bids": "Avg Bids",
    "avg_questions": "Avg Questions",
    "avg_telclicks": "Avg Tel Clicks",
    "avg_webclicks": "Avg Web Clicks",
    "bouwjaar": "Build Year",
    "carrosserie": "Body Type",
    "diff_b_minus_a": "Diff B-A",
    "difference_lead_minus_no_lead": "Lead vs No-Lead Difference",
    "emissie": "Emissions",
    "energielabel": "Energy Label",
    "excluding_missing_metric_rows": "Excl Missing Metric Rows",
    "excluding_duplicate_id_rows": "Excl Dup IDs",
    "expected_a_share": "Expected A Share",
    "largest_category_gap": "Largest Category Gap",
    "lead_rate_diff_b_minus_a": "Abs Lift",
    "group": "Test Group",
    "car_age_band": "Car Age Band",
    "channel": "Lead Type",
    "km_band": "Mileage Band",
    "listing_lifecycle_stage": "Lifecycle Stage",
    "lead_rate": "Lead Rate",
    "lead_rate_a": "Lead Rate A",
    "lead_rate_b": "Lead Rate B",
    "lead_median": "Lead Median",
    "median_total_leads": "Median Leads/Ad",
    "median_car_age": "Median Car Age",
    "median_days_live": "Median Days Live",
    "median_mileage": "Median Mileage",
    "median_photos": "Median Photos",
    "median_price": "Median Price",
    "missing_pct": "Missing %",
    "missing_source_rows": "Missing Source",
    "n_asq": "Questions",
    "out_of_band_rows": "Out of Band",
    "pct_rows_dropped": "% Rows Dropped",
    "pct_diff_vs_a": "% Diff",
    "pct_difference_vs_no_lead": "% Difference vs No Lead",
    "photo_count_band": "Photo Count Band",
    "photo_cnt": "Photos",
    "price_band": "Price Band",
    "relative_lift_vs_a": "Rel Lift",
    "rows_dropped": "Rows Dropped",
    "rows_used": "Rows Used",
    "share": "Row Share",
    "share_a": "Share A",
    "share_b": "Share B",
    "share_diff_b_minus_a": "Share Diff",
    "share_of_ads": "Ad Share",
    "share_of_ads_with_event": "Ads With Event Share",
    "share_of_all_lead_events": "Lead Event Share",
    "share_of_raw_rows": "Row Share",
    "small_segment_flag": "Small Segment",
    "source_column": "Source Column",
    "src_ad_id": "Ad ID",
    "standardized_diff": "Std Diff",
    "start_weekday": "Start Weekday",
    "telclicks": "Tel Clicks",
    "total_leads": "Total Leads",
    "unique_values": "Unique",
    "vermogen": "Power",
    "webclicks": "Web Clicks",
    "average_events_per_ad": "Avg Events/Ad",
    "missing_as_zero": "Missing as Zero",
    "no_lead_median": "No-Lead Median",
    "rows_with_event": "Rows With Event",
    "with_duplicate_id_rows": "With Dup IDs",
}
DISPLAY_VALUE_ALIASES = {
    "A lead rate": "A Lead Rate",
    "any_lead": "Any Lead",
    "A rows": "A Rows",
    "A share of assigned rows": "A Share of Assigned Rows",
    "A ads": "A Ads",
    "A ads with leads": "A Ads With Leads",
    "Ads with at least one lead": "Ads With At Least One Lead",
    "B lead rate": "B Lead Rate",
    "B rows": "B Rows",
    "B share of assigned rows": "B Share of Assigned Rows",
    "B ads": "B Ads",
    "B ads with leads": "B Ads With Leads",
    "B minus A lead-rate difference": "Abs Lead-Rate Lift",
    "expected_A_share": "Expected A Share",
    "Significance level": "Significance Level",
    "Sample-ratio p-value": "Sample-Ratio p-Value",
    "Approx. 95% CI lower for difference": "Approx 95% CI Lower",
    "Approx. 95% CI upper for difference": "Approx 95% CI Upper",
    "z statistic": "z Statistic",
    "Two-sided p-value": "Two-Sided p-Value",
    "ad_start_dt": "Start Date",
    "avg_total_leads": "Avg Leads/Ad",
    "aantaldeuren": "Doors",
    "aantalstoelen": "Seats",
    "bids": "Bids",
    "bouwjaar": "Build Year",
    "brand": "Brand",
    "car_age": "Car Age",
    "car_age_band": "Car Age Band",
    "carrosserie": "Body Type",
    "columns": "Columns",
    "count": "Count",
    "days_live": "Days Live",
    "Days live max": "Days Live Max",
    "Days live median": "Days Live Median",
    "Days live p90": "Days Live P90",
    "diff_b_minus_a": "Diff B-A",
    "Earliest ad start": "Earliest Ad Start",
    "emissie": "Emissions",
    "energielabel": "Energy Label",
    "excluded_missing_group_rows": "Missing-Group Rows",
    "fully_duplicated_rows": "Fully Duplicated Rows",
    "km_band": "Mileage Band",
    "kmstand": "Mileage",
    "kleur": "Color",
    "l2": "L2",
    "Latest ad start": "Latest Ad Start",
    "Lead events from top-decile ads": "Lead Events From Top-Decile Ads",
    "max": "Max",
    "mean": "Mean",
    "Median total leads": "Median Total Leads",
    "median_total_leads": "Median Leads/Ad",
    "min": "Min",
    "model": "Model",
    "n_asq": "Questions",
    "pct_rows_dropped": "% Rows Dropped",
    "photo_count_band": "Photo Count Band",
    "photo_cnt": "Photos",
    "P90 total leads": "P90 Total Leads",
    "P99 total leads": "P99 Total Leads",
    "price": "Price",
    "price_band": "Price Band",
    "raw_rows": "Raw Rows",
    "Relative lift vs A": "Relative Lift vs A",
    "relative_lift_vs_a": "Relative Lift vs A",
    "rows": "Rows",
    "Rows assigned to A/B groups in q2": "Rows Assigned to A/B Groups in q2",
    "Rows available for q3 insights": "Rows Available for q3 Insights",
    "Rows not assigned to an A/B group": "Rows Not Assigned to an A/B Group",
    "rows_dropped": "Rows Dropped",
    "rows_with_duplicated_ad_id": "Rows With Duplicated Ad ID",
    "std": "Std",
    "src_ad_id": "Ad ID",
    "telclicks": "Tel Clicks",
    "group": "Test Group",
    "unique_ad_ids": "Unique Ad IDs",
    "valid_ab_rows": "Valid A/B Rows",
    "vermogen": "Power",
    "webclicks": "Web Clicks",
}


def format_table_header(column):
    """Convert snake_case/raw field names into notebook-friendly headers."""
    normalized_column = str(column).lower()
    if normalized_column in DISPLAY_HEADER_ALIASES:
        return DISPLAY_HEADER_ALIASES[normalized_column]

    words = str(column).replace("_", " ").split()
    return " ".join(
        HEADER_WORD_REPLACEMENTS.get(word.lower(), word.title())
        for word in words
    )


def format_table_value(value, column, row=None):
    """Format table values using column and row context."""
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")

    if pd.isna(value):
        return "NaN"

    if isinstance(value, bool):
        return str(value)

    if isinstance(value, Number):
        column_name = str(column).lower()
        row_context = ""
        if row is not None:
            row_context = " ".join(
                str(row[label]).lower()
                for label in ["dimension", "metric"]
                if label in row.index
            )
        # Row context lets metric/value tables format p-values, power, and
        # year-like fields correctly even when the column name is generic.
        if column_name in {"share_of_ads", "ad share"}:
            return f"{value:.1%}"

        if column_name in {"lead_rate", "lead rate", "lead_rate_a", "lead rate a", "lead_rate_b", "lead rate b"}:
            return f"{value:.1%}"

        if column_name in {"median_price", "median price"}:
            return f"€{value:,.0f}"

        if column_name in {"median_car_age", "median car age", "median_mileage", "median mileage"}:
            return f"{value:,.0f}"

        uses_decimal_format = any(keyword in column_name for keyword in DECIMAL_FORMAT_COLUMN_KEYWORDS)
        uses_thousands_separator = not any(
            keyword in f"{column_name} {row_context}" for keyword in NO_THOUSANDS_SEPARATOR_COLUMN_KEYWORDS
        )
        separator = "," if uses_thousands_separator else ""

        if not uses_decimal_format and float(value).is_integer():
            return f"{value:{separator}.0f}"

        if "p-value" in row_context and abs(value) < 0.001:
            return "<0.001"

        if "power" in row_context and value > 0.999:
            return ">0.999"

        return f"{value:{separator}.{TABLE_DECIMALS}f}"

    string_value = str(value)
    return DISPLAY_VALUE_ALIASES.get(string_value, string_value)


def format_table_for_display(table, max_rows=None):
    """Return a copy of a dataframe with readable headers and values."""
    visible_table = table.head(max_rows) if max_rows is not None else table
    display_table = visible_table.copy()

    for column in display_table.columns:
        display_table[column] = [
            format_table_value(value, column, visible_table.loc[index])
            for index, value in visible_table[column].items()
        ]

    display_table = display_table.rename(columns=format_table_header)
    return display_table


def style_table(table, max_rows=None):
    """Return a styled dataframe for display in notebooks."""
    return format_table_for_display(table, max_rows=max_rows).style


def style_segment_insight_table(table, max_rows=None):
    """Style q3 segment tables with separate heat maps for lead-rate columns."""
    visible_table = table.head(max_rows) if max_rows is not None else table
    display_table = visible_table.copy().rename(columns=format_table_header)
    lead_rate_column = format_table_header("lead_rate")
    avg_leads_column = format_table_header("avg_total_leads")
    heatmap_cmap = LinearSegmentedColormap.from_list(
        "segment_blue_green",
        ["#EAF0F7", PLOT_COLORS["diff"]],
    )

    formatters = {
        column: (lambda value, column=column: format_table_value(value, column))
        for column in display_table.columns
    }
    styled_table = display_table.style.format(formatters)

    if lead_rate_column in display_table.columns:
        styled_table = styled_table.background_gradient(cmap=heatmap_cmap, subset=[lead_rate_column])
    if avg_leads_column in display_table.columns:
        styled_table = styled_table.background_gradient(cmap=heatmap_cmap, subset=[avg_leads_column])

    return styled_table


def print_table(title, table, max_rows=30):
    """Print a formatted dataframe for script/terminal output."""
    print(f"\n{title}")
    display_table = format_table_for_display(table, max_rows=max_rows)
    print(display_table.to_string(index=False))

"""Shared constants and formatting utilities for the cars analysis."""

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


ASSIGNMENT_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ASSIGNMENT_DIR.parents[1]
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

# ---------------------------------------------------------------------------
# General utilities
# ---------------------------------------------------------------------------


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

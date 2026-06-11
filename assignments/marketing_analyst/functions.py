"""Shared helpers for the marketing analyst notebooks.

The notebooks should read like a presentation-ready analysis story. This
module holds the repeatable mechanics: file paths, data loading, aggregation,
metric formatting, and chart setup.
"""

from pathlib import Path
import os
import tempfile

# Matplotlib can try to write config files under the user's home directory.
# Point it at /tmp so notebook execution works in restricted environments too.
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "marketplaats-matplotlib"))

import pandas as pd

try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    plt = None


ASSIGNMENT_DIR = Path(__file__).resolve().parent
DATA_DIR = ASSIGNMENT_DIR / "data"
DOCS_DIR = ASSIGNMENT_DIR / "docs"

SOURCE_WORKBOOK_PATH = DATA_DIR / "Marktplaats2dehands Business Analytics SMB Dataset.xlsx"
Q2_CSV_PATH = DATA_DIR / "question_2_outreach_prioritization.csv"
Q3_CSV_PATH = DATA_DIR / "question_3_bundle_registrations.csv"

Q2_DATE_COLUMN = "FTR_MONTH"
Q2_USER_COLUMN = "USER_ID"
Q2_CATEGORY_COLUMN = "CATEGORY_NAME"
Q3_USER_COLUMN = "User ID"

AD_COUNT_COLUMNS = [
    "N_FREE_AD_INSERTIONS",
    "N_PAID_AD_INSERTIONS",
]
FEATURE_COUNT_COLUMNS = [
    "N_AD_RENEWALS",
    "N_DAGTOPPERS",
    "N_HOMEPAGE",
    "N_PAID_URL",
    "N_AD_UPCALLS",
    "N_URGENCY",
]
FEE_COLUMNS = [
    "FEE_PAID_AD_INSERTIONS",
    "FEE_AD_RENEWALS",
    "FEE_DAGTOPPERS",
    "FEE_HOMEPAGE",
    "FEE_PAID_URL",
    "FEE_AD_UPCALLS",
    "FEE_URGENCY",
]
Q2_NUMERIC_COLUMNS = AD_COUNT_COLUMNS + FEATURE_COUNT_COLUMNS + FEE_COLUMNS

BUNDLE_PRICES_PER_4_WEEKS = {
    "Basis": 19.99,
    "Basic": 19.99,
    "Plus": 49.99,
}
FREE_TRIAL_DAYS = 28
ACTIVE_SUBSCRIPTION_END_DATE = pd.Timestamp("2099-12-31")

PLOT_COLORS = {
    "primary": "#4C78A8",
    "secondary": "#F58518",
    "success": "#54A24B",
    "warning": "#ECA82C",
    "neutral": "#8A8F98",
}


# ---------------------------------------------------------------------------
# General utilities
# ---------------------------------------------------------------------------


def pct(value):
    """Format a share as a readable percentage."""
    if pd.isna(value):
        return pd.NA
    return f"{value:.1%}"


def eur(value):
    """Format a numeric value as EUR for presentation output."""
    if pd.isna(value):
        return pd.NA
    return f"EUR {value:,.0f}"


def existing_columns(dataframe, requested_columns):
    """Return requested columns that are present in the dataframe."""
    return [column for column in requested_columns if column in dataframe.columns]


def set_plot_style():
    """Apply a consistent plotting style for all marketing notebooks."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update(
        {
            "figure.figsize": (9, 5),
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titleweight": "bold",
            "axes.titlesize": 13,
            "axes.labelsize": 10,
            "font.size": 10,
        }
    )


def add_bar_labels(ax, fmt="{:,.0f}", padding=3):
    """Add value labels above vertical bars."""
    for patch in ax.patches:
        height = patch.get_height()
        if pd.isna(height):
            continue
        ax.annotate(
            fmt.format(height),
            (patch.get_x() + patch.get_width() / 2, height),
            ha="center",
            va="bottom",
            xytext=(0, padding),
            textcoords="offset points",
            fontsize=9,
        )
    return ax


# ---------------------------------------------------------------------------
# Question 2: outreach prioritization
# ---------------------------------------------------------------------------


def read_q2_data(data_path=Q2_CSV_PATH):
    """Read the Q2 outreach dataset and coerce dates/numeric metrics."""
    dataframe = pd.read_csv(data_path)
    dataframe[Q2_DATE_COLUMN] = pd.to_datetime(dataframe[Q2_DATE_COLUMN], errors="coerce")

    for column in existing_columns(dataframe, Q2_NUMERIC_COLUMNS):
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce").fillna(0)

    return dataframe


def add_q2_row_metrics(dataframe):
    """Add row-level ad, feature, and fee totals to the Q2 dataset."""
    data = dataframe.copy()
    data["total_ad_insertions"] = data[existing_columns(data, AD_COUNT_COLUMNS)].sum(axis=1)
    data["paid_ad_insertions"] = data.get("N_PAID_AD_INSERTIONS", 0)
    data["total_feature_uses"] = data[existing_columns(data, FEATURE_COUNT_COLUMNS)].sum(axis=1)
    data["total_fees"] = data[existing_columns(data, FEE_COLUMNS)].sum(axis=1)
    data["paid_visibility_uses"] = data[
        existing_columns(
            data,
            [
                "N_DAGTOPPERS",
                "N_HOMEPAGE",
                "N_PAID_URL",
                "N_AD_UPCALLS",
                "N_URGENCY",
            ],
        )
    ].sum(axis=1)
    return data


def seller_level_q2_summary(dataframe):
    """Aggregate Q2 rows to one row per seller for prioritization analysis."""
    data = add_q2_row_metrics(dataframe)
    summary = (
        data.groupby(Q2_USER_COLUMN, as_index=False)
        .agg(
            active_months=(Q2_DATE_COLUMN, "nunique"),
            first_month=(Q2_DATE_COLUMN, "min"),
            last_month=(Q2_DATE_COLUMN, "max"),
            categories=(Q2_CATEGORY_COLUMN, "nunique"),
            total_ad_insertions=("total_ad_insertions", "sum"),
            free_ad_insertions=("N_FREE_AD_INSERTIONS", "sum"),
            paid_ad_insertions=("paid_ad_insertions", "sum"),
            total_feature_uses=("total_feature_uses", "sum"),
            paid_visibility_uses=("paid_visibility_uses", "sum"),
            total_fees=("total_fees", "sum"),
        )
        .sort_values("total_fees", ascending=False)
        .reset_index(drop=True)
    )
    summary["avg_ads_per_active_month"] = summary["total_ad_insertions"] / summary["active_months"].clip(lower=1)
    summary["avg_fees_per_active_month"] = summary["total_fees"] / summary["active_months"].clip(lower=1)
    summary["has_paid_visibility"] = summary["paid_visibility_uses"] > 0
    summary["has_paid_ads"] = summary["paid_ad_insertions"] > 0
    return summary


def add_percentile_score(dataframe, columns, score_column="priority_score"):
    """Create a simple average percentile score from selected numeric columns."""
    scored = dataframe.copy()
    columns = existing_columns(scored, columns)
    percentile_columns = []

    for column in columns:
        percentile_column = f"{column}_pct_rank"
        scored[percentile_column] = scored[column].rank(pct=True, method="average")
        percentile_columns.append(percentile_column)

    scored[score_column] = scored[percentile_columns].mean(axis=1)
    return scored.sort_values(score_column, ascending=False).reset_index(drop=True)


def segment_by_quantiles(dataframe, column, labels=("Low", "Medium", "High")):
    """Add a simple quantile segment for a numeric column."""
    data = dataframe.copy()
    segment_column = f"{column}_segment"
    data[segment_column] = pd.qcut(data[column].rank(method="first"), q=len(labels), labels=labels)
    return data


def top_categories(dataframe, value_column="total_fees", top_n=10):
    """Summarize Q2 activity by category for compact exploratory charts."""
    data = add_q2_row_metrics(dataframe)
    return (
        data.groupby(Q2_CATEGORY_COLUMN, as_index=False)
        .agg(
            sellers=(Q2_USER_COLUMN, "nunique"),
            total_ad_insertions=("total_ad_insertions", "sum"),
            total_feature_uses=("total_feature_uses", "sum"),
            total_fees=("total_fees", "sum"),
        )
        .sort_values(value_column, ascending=False)
        .head(top_n)
        .reset_index(drop=True)
    )


# ---------------------------------------------------------------------------
# Question 3: sales monitoring
# ---------------------------------------------------------------------------


def read_q3_data(data_path=Q3_CSV_PATH):
    """Read the Q3 bundle registration dataset and coerce date fields."""
    dataframe = pd.read_csv(data_path)
    dataframe["Start"] = pd.to_datetime(dataframe["Start"], errors="coerce")
    dataframe["End"] = pd.to_datetime(dataframe["End"], errors="coerce")
    return dataframe


def add_subscription_metrics(dataframe, as_of_date=None):
    """Add reusable subscription flags and estimated first-payment metrics."""
    data = dataframe.copy()
    if as_of_date is None:
        as_of_date = data["Start"].max()
    as_of_date = pd.Timestamp(as_of_date)

    data["is_active"] = data["End"].ge(as_of_date) | data["End"].eq(ACTIVE_SUBSCRIPTION_END_DATE)
    data["trial_end"] = data["Start"] + pd.Timedelta(days=FREE_TRIAL_DAYS)
    data["is_past_trial"] = data["trial_end"].le(as_of_date)
    data["bundle_price_per_4_weeks"] = data["Bundle"].map(BUNDLE_PRICES_PER_4_WEEKS)
    data["eligible_first_payment"] = data["is_past_trial"] & data["bundle_price_per_4_weeks"].notna()
    data["estimated_first_payment_revenue"] = data["bundle_price_per_4_weeks"].where(
        data["eligible_first_payment"],
        0,
    )
    return data


def subscription_kpi_summary(dataframe, as_of_date=None):
    """Return a compact KPI table for the Q3 sales dashboard."""
    data = add_subscription_metrics(dataframe, as_of_date=as_of_date)
    rows = [
        ("registrations", len(data)),
        ("unique_sellers", data[Q3_USER_COLUMN].nunique()),
        ("active_subscriptions", int(data["is_active"].sum())),
        ("past_trial_registrations", int(data["is_past_trial"].sum())),
        ("estimated_first_payment_revenue", data["estimated_first_payment_revenue"].sum()),
    ]
    return pd.DataFrame(rows, columns=["metric", "value"])


def monthly_registrations(dataframe):
    """Count new bundle registrations by month and bundle."""
    data = dataframe.copy()
    data["start_month"] = data["Start"].dt.to_period("M").dt.to_timestamp()
    return (
        data.groupby(["start_month", "Bundle"], as_index=False)
        .size()
        .rename(columns={"size": "registrations"})
        .sort_values(["start_month", "Bundle"])
        .reset_index(drop=True)
    )


def bundle_mix(dataframe, group_column="Bundle"):
    """Return count and share by bundle or customer type."""
    summary = dataframe[group_column].value_counts(dropna=False).rename_axis(group_column).reset_index(name="registrations")
    summary["share"] = summary["registrations"] / summary["registrations"].sum()
    return summary

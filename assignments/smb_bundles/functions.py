"""Shared helpers for the SMB Bundles notebooks.

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
import numpy as np

try:
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    from matplotlib.lines import Line2D
    from matplotlib.patches import Circle
    from matplotlib.ticker import FuncFormatter
except ModuleNotFoundError:
    plt = None
    LinearSegmentedColormap = None
    Line2D = None
    Circle = None
    FuncFormatter = None


ASSIGNMENT_DIR = Path(__file__).resolve().parent
DATA_DIR = ASSIGNMENT_DIR / "data"
DOCS_DIR = ASSIGNMENT_DIR / "docs"
DELIVERABLES_DIR = ASSIGNMENT_DIR.parents[1] / "deliverables" / "smb_bundles"

SOURCE_WORKBOOK_PATH = DATA_DIR / "Marktplaats2dehands Business Analytics SMB Dataset.xlsx"
Q2_CSV_PATH = DATA_DIR / "q2_prioritize.csv"
Q3_CSV_PATH = DATA_DIR / "q3_monitor.csv"
Q2_SCORED_SELLERS_CSV_PATH = DELIVERABLES_DIR / "q2_scored_sellers.csv"

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
Q3_COHORT_MATURITY_DAYS = (28, 56, 84, 112, 140, 168)
ACTIVE_SUBSCRIPTION_END_DATE = pd.Timestamp("2099-12-31")

PLOT_COLORS = {
    "background": "#050505",
    "panel": "#050505",
    "grid": "#3A3A3A",
    "text": "#F7F7F2",
    "muted_text": "#A5A5A5",
    "q1": "#F4C430",
    "q2": "#4FB3FF",
    "q3": "#3DDC97",
    "q4": "#FF7A59",
    "primary": "#4FB3FF",
    "secondary": "#9AA4B2",
    "success": "#3DDC97",
    "warning": "#F4C430",
    "danger": "#FF7A59",
    "accent": "#4FB3FF",
    "neutral": "#9AA4B2",
    "highlight": "#3A3321",
}

Q3_HEATMAP_CMAP = (
    LinearSegmentedColormap.from_list(
        "q3_black_to_green",
        [PLOT_COLORS["background"], PLOT_COLORS["q3"]],
    )
    if LinearSegmentedColormap is not None
    else None
)

CATEGORY_TRANSLATIONS = {
    "Antiek en Kunst": "Antiques and Art",
    "Audio, Tv en Foto": "Audio, TV and Photo",
    "Auto diversen": "Miscellaneous Auto",
    "Auto-onderdelen": "Auto Parts",
    "Boeken": "Books",
    "Cd's en Dvd's": "CDs and DVDs",
    "Computers en Software": "Computers and Software",
    "Contacten en Berichten": "Contacts and Messages",
    "Diensten en Vakmensen": "Services and Tradespeople",
    "Dieren en Toebehoren": "Pets and Accessories",
    "Diversen": "Miscellaneous",
    "Doe-het-zelf en Verbouw": "DIY and Renovation",
    "Fietsen en Brommers": "Bicycles and Mopeds",
    "Hobby en Vrije tijd": "Hobbies and Leisure",
    "Huis en Inrichting": "Home and Interior",
    "Huizen en Kamers": "Houses and Rooms",
    "Kinderen en Baby's": "Children and Babies",
    "Kleding | Dames": "Women's Clothing",
    "Kleding | Heren": "Men's Clothing",
    "Muziek en Instrumenten": "Music and Instruments",
    "Postzegels en Munten": "Stamps and Coins",
    "Sieraden, Tassen en Uiterlijk": "Jewelry, Bags and Beauty",
    "Spelcomputers en Games": "Game Consoles and Games",
    "Sport en Fitness": "Sports and Fitness",
    "Telecommunicatie": "Telecommunications",
    "Tickets en Kaartjes": "Tickets",
    "Tuin en Terras": "Garden and Terrace",
    "Vakantie": "Holiday",
    "Verzamelen": "Collectibles",
    "Watersport en Boten": "Water Sports and Boats",
    "Witgoed en Apparatuur": "White Goods and Appliances",
    "Zakelijke goederen": "Business Goods",
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
    """Format a numeric value as euros for presentation output."""
    if pd.isna(value):
        return pd.NA
    return f"€{value:,.0f}"


def format_display_table(dataframe, euro_columns=None, decimal_columns=None, integer_columns=None):
    """Return a copy with selected columns formatted for notebook display."""
    display = dataframe.copy()
    euro_columns = euro_columns or []
    decimal_columns = decimal_columns or []
    integer_columns = integer_columns or []

    for column in existing_columns(display, euro_columns):
        display[column] = display[column].map(lambda value: eur(value))
    for column in existing_columns(display, decimal_columns):
        display[column] = display[column].map(lambda value: f"{value:,.1f}")
    for column in existing_columns(display, integer_columns):
        display[column] = display[column].map(lambda value: f"{value:,.0f}")

    return display


def existing_columns(dataframe, requested_columns):
    """Return requested columns that are present in the dataframe."""
    return [column for column in requested_columns if column in dataframe.columns]


def set_plot_style():
    """Apply a consistent plotting style for all marketing notebooks."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    plt.style.use("dark_background")
    plt.rcParams.update(
        {
            "figure.figsize": (9, 5),
            "figure.facecolor": PLOT_COLORS["background"],
            "figure.edgecolor": PLOT_COLORS["background"],
            "savefig.facecolor": PLOT_COLORS["background"],
            "savefig.edgecolor": PLOT_COLORS["background"],
            "axes.facecolor": PLOT_COLORS["panel"],
            "axes.edgecolor": PLOT_COLORS["grid"],
            "axes.labelcolor": PLOT_COLORS["muted_text"],
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titleweight": "bold",
            "axes.titlesize": 13,
            "axes.titlecolor": PLOT_COLORS["text"],
            "axes.labelsize": 10,
            "axes.prop_cycle": plt.cycler(
                color=[
                    PLOT_COLORS["q2"],
                    PLOT_COLORS["q1"],
                    PLOT_COLORS["q3"],
                    PLOT_COLORS["q4"],
                    PLOT_COLORS["neutral"],
                ]
            ),
            "font.size": 10,
            "text.color": PLOT_COLORS["text"],
            "xtick.color": PLOT_COLORS["muted_text"],
            "ytick.color": PLOT_COLORS["muted_text"],
            "grid.color": PLOT_COLORS["grid"],
            "grid.alpha": 0.45,
            "legend.facecolor": PLOT_COLORS["panel"],
            "legend.edgecolor": PLOT_COLORS["grid"],
            "legend.labelcolor": PLOT_COLORS["text"],
        }
    )


def readable_metric_label(column_name):
    """Convert dataset-style column names to readable chart labels."""
    label_overrides = {
        "FEE_PAID_AD_INSERTIONS": "Paid Ad Insertions",
        "FEE_AD_RENEWALS": "Ad Renewals",
        "FEE_DAGTOPPERS": "Dagtoppers",
        "FEE_HOMEPAGE": "Homepage",
        "FEE_PAID_URL": "Paid URL",
        "FEE_AD_UPCALLS": "Ad Upcalls",
        "FEE_URGENCY": "Urgency",
        "N_FREE_AD_INSERTIONS": "Free Ad Insertions",
        "N_PAID_AD_INSERTIONS": "Paid Ad Insertions",
        "N_AD_RENEWALS": "Ad Renewals",
        "N_DAGTOPPERS": "Dagtoppers",
        "N_HOMEPAGE": "Homepage",
        "N_PAID_URL": "Paid URL",
        "N_AD_UPCALLS": "Ad Upcalls",
        "N_URGENCY": "Urgency",
        "USER_ID": "Seller ID",
        "FTR_MONTH": "Month",
        "CATEGORY_NAME": "Category",
        "total_ad_insertions": "Total Ad Insertions",
        "paid_ad_insertions": "Paid Ad Insertions",
        "free_ad_insertions": "Free Ad Insertions",
        "total_feature_uses": "Total Feature Uses",
        "commercial_uses": "Commercial Uses",
        "paid_marketplace_actions": "Paid Marketplace Actions",
        "recent_paid_usage": "Recent Paid Usage",
        "paid_visibility_uses": "Paid Visibility Uses",
        "total_fees": "Total Fees",
        "active_months": "Active Months",
        "first_month": "First Active Month",
        "last_month": "Last Active Month",
        "categories": "Categories",
        "rows": "Rows",
        "avg_ads_per_active_month": "Average Ads per Active Month",
        "avg_fees_per_active_month": "Average Fees per Active Month",
        "has_paid_visibility": "Has Paid Visibility",
        "has_paid_ads": "Has Paid Ads",
    }
    if column_name in label_overrides:
        return label_overrides[column_name]

    label = column_name
    for prefix in ("FEE_", "N_"):
        if label.startswith(prefix):
            label = label[len(prefix) :]
    label = label.replace("_", " ").title()
    return label.replace("Url", "URL")


def readable_category_label(category_name):
    """Keep the Dutch category name and add an English translation."""
    translation = CATEGORY_TRANSLATIONS.get(category_name)
    if not translation:
        return category_name
    return f"{category_name} ({translation})"


def format_number_axis(ax, axis="x"):
    """Use thousands separators on a numeric chart axis."""
    if FuncFormatter is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    formatter = FuncFormatter(lambda value, _: f"{value:,.0f}")
    if axis in ("x", "both"):
        ax.xaxis.set_major_formatter(formatter)
    if axis in ("y", "both"):
        ax.yaxis.set_major_formatter(formatter)
    return ax


def format_eur_axis(ax, axis="x"):
    """Format a numeric chart axis as whole euros."""
    if FuncFormatter is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    formatter = FuncFormatter(lambda value, _: f"€{value:,.0f}")
    if axis in ("x", "both"):
        ax.xaxis.set_major_formatter(formatter)
    if axis in ("y", "both"):
        ax.yaxis.set_major_formatter(formatter)
    return ax


def format_percent_axis(ax, axis="y"):
    """Format a 0-100 axis as whole percentages."""
    if FuncFormatter is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    formatter = FuncFormatter(lambda value, _: f"{value:.0f}%")
    if axis in ("x", "both"):
        ax.xaxis.set_major_formatter(formatter)
    if axis in ("y", "both"):
        ax.yaxis.set_major_formatter(formatter)
    return ax


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


def add_horizontal_bar_labels(ax, fmt="{:,.0f}", padding=4):
    """Add value labels to the right of horizontal bars."""
    for patch in ax.patches:
        width = patch.get_width()
        if pd.isna(width):
            continue
        ax.annotate(
            fmt.format(width),
            (width, patch.get_y() + patch.get_height() / 2),
            ha="left",
            va="center",
            xytext=(padding, 0),
            textcoords="offset points",
            fontsize=9,
        )
    return ax


def add_horizontal_bar_text_labels(ax, labels, padding=4):
    """Add custom text labels to the right of horizontal bars."""
    for patch, label in zip(ax.patches, labels):
        width = patch.get_width()
        if pd.isna(width):
            continue
        ax.annotate(
            label,
            (width, patch.get_y() + patch.get_height() / 2),
            ha="left",
            va="center",
            xytext=(padding, 0),
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
    data["paid_marketplace_actions"] = data["paid_ad_insertions"] + data["total_feature_uses"]
    return data


def q2_overview(dataframe):
    """Return high-level Q2 dataset dimensions."""
    return {
        "rows": len(dataframe),
        "columns": dataframe.shape[1],
        "unique_sellers": dataframe[Q2_USER_COLUMN].nunique(),
        "unique_months": dataframe[Q2_DATE_COLUMN].nunique(),
        "first_month": dataframe[Q2_DATE_COLUMN].min(),
        "last_month": dataframe[Q2_DATE_COLUMN].max(),
        "unique_categories": dataframe[Q2_CATEGORY_COLUMN].nunique(),
    }


def q2_data_quality_message(dataframe):
    """Summarize basic Q2 quality checks at the expected row grain."""
    dimension_columns = [Q2_USER_COLUMN, Q2_DATE_COLUMN, Q2_CATEGORY_COLUMN]
    metric_columns = existing_columns(dataframe, Q2_NUMERIC_COLUMNS)
    missing_values = dataframe.isna().sum().sum()
    duplicate_grain_rows = dataframe.duplicated(dimension_columns).sum()
    negative_metric_values = (dataframe[metric_columns] < 0).sum().sum()

    if missing_values == duplicate_grain_rows == negative_metric_values == 0:
        return (
            "Data quality check: no missing values, no duplicate seller-month-category rows, "
            "and no negative metric values."
        )

    return (
        f"Data quality check: {missing_values} missing values, "
        f"{duplicate_grain_rows} duplicate seller-month-category rows, "
        f"and {negative_metric_values} negative metric values."
    )


def q2_metric_summary(dataframe):
    """Summarize raw Q2 numeric columns for quick data understanding."""
    metric_columns = existing_columns(dataframe, Q2_NUMERIC_COLUMNS)
    summary = (
        pd.DataFrame(
            {
                "Column": metric_columns,
                "Metric": [readable_metric_label(column) for column in metric_columns],
                "Total": dataframe[metric_columns].sum().values,
                "Non-zero Rows": (dataframe[metric_columns] > 0).sum().values,
                "Non-zero Row %": ((dataframe[metric_columns] > 0).mean() * 100).round(1).values,
            }
        )
        .sort_values("Total", ascending=False)
        .reset_index(drop=True)
    )
    summary["Total"] = summary.apply(
        lambda row: eur(row["Total"]) if row["Column"] in FEE_COLUMNS else f"{row['Total']:,.0f}",
        axis=1,
    )
    return summary


def q2_row_metric_summary(dataframe):
    """Describe row-level volume, commercial usage, and fees."""
    data = add_q2_row_metrics(dataframe)
    data["commercial_uses"] = data["paid_marketplace_actions"]
    summary = data[["total_ad_insertions", "commercial_uses", "total_fees"]].describe().round(2)
    summary = summary.rename(columns=readable_metric_label)
    summary["Total Fees"] = [
        f"{value:,.0f}" if index == "count" else f"€{value:,.2f}"
        for index, value in summary["Total Fees"].items()
    ]
    return summary


def q2_monthly_summary(dataframe):
    """Aggregate Q2 activity by month."""
    data = add_q2_row_metrics(dataframe)
    data["commercial_uses"] = data["paid_marketplace_actions"]
    return (
        data.groupby(Q2_DATE_COLUMN, as_index=False)
        .agg(
            sellers=(Q2_USER_COLUMN, "nunique"),
            rows=(Q2_USER_COLUMN, "size"),
            categories=(Q2_CATEGORY_COLUMN, "nunique"),
            total_ad_insertions=("total_ad_insertions", "sum"),
            commercial_uses=("commercial_uses", "sum"),
            total_fees=("total_fees", "sum"),
        )
    )


def seller_level_q2_summary(dataframe):
    """Aggregate Q2 rows to one row per seller for prioritization analysis."""
    data = add_q2_row_metrics(dataframe)
    data["_has_activity"] = data["total_ad_insertions"].add(data["paid_marketplace_actions"]).gt(0)
    active_months = (
        data[data["_has_activity"]]
        .groupby(Q2_USER_COLUMN)[Q2_DATE_COLUMN]
        .nunique()
        .rename("active_months")
        .reset_index()
    )
    summary = (
        data.groupby(Q2_USER_COLUMN, as_index=False)
        .agg(
            first_month=(Q2_DATE_COLUMN, "min"),
            last_month=(Q2_DATE_COLUMN, "max"),
            categories=(Q2_CATEGORY_COLUMN, "nunique"),
            total_ad_insertions=("total_ad_insertions", "sum"),
            free_ad_insertions=("N_FREE_AD_INSERTIONS", "sum"),
            paid_ad_insertions=("paid_ad_insertions", "sum"),
            total_feature_uses=("total_feature_uses", "sum"),
            paid_marketplace_actions=("paid_marketplace_actions", "sum"),
            paid_visibility_uses=("paid_visibility_uses", "sum"),
            total_fees=("total_fees", "sum"),
        )
        .merge(active_months, on=Q2_USER_COLUMN, how="left")
        .sort_values("total_fees", ascending=False)
        .reset_index(drop=True)
    )
    summary["active_months"] = summary["active_months"].fillna(0)
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


def q2_seller_summary_describe(seller_summary):
    """Return a formatted seller-level distribution table."""
    display = seller_summary.drop(
        columns=existing_columns(
            seller_summary,
            [Q2_USER_COLUMN, "first_month", "last_month", "has_paid_visibility", "has_paid_ads"],
        )
    ).rename(columns=readable_metric_label)
    summary = display.describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.95, 0.99]).round(2)
    for column in existing_columns(summary, ["Total Fees", "Average Fees per Active Month"]):
        summary[column] = [
            f"{value:,.0f}" if index == "count" else f"€{value:,.2f}"
            for index, value in summary[column].items()
        ]
    return summary


def q2_anomaly_detail(
    dataframe,
    monthly_summary,
    anomaly_seller_id=65950787,
    anomaly_month="2023-11-01",
    anomaly_category="Auto-onderdelen",
):
    """Return the row explaining the visible November 2023 spike."""
    data = add_q2_row_metrics(dataframe)
    anomaly_month = pd.Timestamp(anomaly_month)
    anomaly_row = data[
        data[Q2_USER_COLUMN].eq(anomaly_seller_id)
        & data[Q2_DATE_COLUMN].eq(anomaly_month)
        & data[Q2_CATEGORY_COLUMN].eq(anomaly_category)
    ].iloc[0]
    month_totals = monthly_summary.loc[monthly_summary[Q2_DATE_COLUMN].eq(anomaly_month)].iloc[0]

    detail = pd.DataFrame(
        [
            {
                "Seller ID": anomaly_seller_id,
                "Month": anomaly_month.strftime("%Y-%m"),
                "Category": readable_category_label(anomaly_category),
                "Paid Ad Insertions": anomaly_row["N_PAID_AD_INSERTIONS"],
                "Paid URL Features": anomaly_row["N_PAID_URL"],
                "Paid URL Fees": anomaly_row["FEE_PAID_URL"],
                "Total Fees": anomaly_row["total_fees"],
                "Share of Monthly Ads": anomaly_row["total_ad_insertions"] / month_totals["total_ad_insertions"],
                "Share of Monthly Fees": anomaly_row["total_fees"] / month_totals["total_fees"],
            }
        ]
    )
    return detail.style.format(
        {
            "Paid Ad Insertions": "{:,.0f}",
            "Paid URL Features": "{:,.0f}",
            "Paid URL Fees": "€{:,.0f}",
            "Total Fees": "€{:,.0f}",
            "Share of Monthly Ads": "{:.1%}",
            "Share of Monthly Fees": "{:.1%}",
        }
    )


def q2_spike_comparison(
    dataframe,
    monthly_summary,
    anomaly_seller_id=65950787,
    start_month="2023-09-01",
    end_month="2024-01-01",
):
    """Compare monthly totals with and without the anomaly seller."""
    data = add_q2_row_metrics(dataframe)
    monthly_without_seller = (
        data[data[Q2_USER_COLUMN].ne(anomaly_seller_id)]
        .groupby(Q2_DATE_COLUMN, as_index=False)
        .agg(
            sellers=(Q2_USER_COLUMN, "nunique"),
            total_ad_insertions=("total_ad_insertions", "sum"),
            total_fees=("total_fees", "sum"),
        )
    )
    comparison = monthly_summary[[Q2_DATE_COLUMN, "total_ad_insertions", "total_fees"]].merge(
        monthly_without_seller[[Q2_DATE_COLUMN, "total_ad_insertions", "total_fees"]],
        on=Q2_DATE_COLUMN,
        suffixes=("_all", "_excluding_seller"),
    )
    comparison["Ads Explained by Seller"] = (
        comparison["total_ad_insertions_all"] - comparison["total_ad_insertions_excluding_seller"]
    )
    comparison["Fees Explained by Seller"] = (
        comparison["total_fees_all"] - comparison["total_fees_excluding_seller"]
    )
    comparison["Ads Explained %"] = comparison["Ads Explained by Seller"] / comparison["total_ad_insertions_all"]
    comparison["Fees Explained %"] = comparison["Fees Explained by Seller"] / comparison["total_fees_all"]

    display = comparison[
        comparison[Q2_DATE_COLUMN].between(pd.Timestamp(start_month), pd.Timestamp(end_month))
    ].copy()
    display["Month"] = display[Q2_DATE_COLUMN].dt.strftime("%Y-%m")
    display = display.rename(
        columns={
            "total_ad_insertions_all": "Ads: All Sellers",
            "total_ad_insertions_excluding_seller": f"Ads: Excluding Seller {anomaly_seller_id}",
            "total_fees_all": "Fees: All Sellers",
            "total_fees_excluding_seller": f"Fees: Excluding Seller {anomaly_seller_id}",
        }
    )[
        [
            "Month",
            "Ads: All Sellers",
            f"Ads: Excluding Seller {anomaly_seller_id}",
            "Ads Explained by Seller",
            "Ads Explained %",
            "Fees: All Sellers",
            f"Fees: Excluding Seller {anomaly_seller_id}",
            "Fees Explained by Seller",
            "Fees Explained %",
        ]
    ]

    def highlight_anomaly_month(row):
        return [f"background-color: {PLOT_COLORS['highlight']}" if row["Month"] == "2023-11" else "" for _ in row]

    return display.style.apply(highlight_anomaly_month, axis=1).format(
        {
            "Ads: All Sellers": "{:,.0f}",
            f"Ads: Excluding Seller {anomaly_seller_id}": "{:,.0f}",
            "Ads Explained by Seller": "{:,.0f}",
            "Ads Explained %": "{:.1%}",
            "Fees: All Sellers": "€{:,.0f}",
            f"Fees: Excluding Seller {anomaly_seller_id}": "€{:,.0f}",
            "Fees Explained by Seller": "€{:,.0f}",
            "Fees Explained %": "{:.1%}",
        }
    ), monthly_without_seller


def style_minimal_horizontal_bar(ax):
    """Remove redundant axes from labeled horizontal bar charts."""
    ax.grid(False)
    ax.margins(x=0.15)
    ax.set_xlabel("")
    ax.tick_params(axis="x", bottom=False, labelbottom=False)
    ax.tick_params(axis="y", left=False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    return ax


def plot_q2_monthly_overview(monthly_summary, anomaly_month="2023-11-01"):
    """Plot monthly sellers, ad insertions, and fees."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    anomaly_month = pd.Timestamp(anomaly_month)
    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    axes[0].bar(monthly_summary[Q2_DATE_COLUMN], monthly_summary["sellers"], width=20, color=PLOT_COLORS["primary"])
    axes[0].set_title("Monthly Active Sellers")
    axes[0].set_ylabel("Sellers")

    axes[1].bar(monthly_summary[Q2_DATE_COLUMN], monthly_summary["total_ad_insertions"], width=20, color=PLOT_COLORS["q2"])
    axes[1].set_title("Monthly Ad Insertions")
    axes[1].set_ylabel("Ads")

    axes[2].bar(monthly_summary[Q2_DATE_COLUMN], monthly_summary["total_fees"], width=20, color=PLOT_COLORS["q2"])
    axes[2].set_title("Monthly Fees")
    axes[2].set_ylabel("Fees")
    axes[2].set_xlabel("Month")

    for ax in axes:
        format_number_axis(ax, axis="y")
        ax.grid(axis="y", alpha=0.3)
    format_eur_axis(axes[2], axis="y")

    anomaly_ads = monthly_summary.loc[monthly_summary[Q2_DATE_COLUMN].eq(anomaly_month), "total_ad_insertions"].iloc[0]
    anomaly_fees = monthly_summary.loc[monthly_summary[Q2_DATE_COLUMN].eq(anomaly_month), "total_fees"].iloc[0]
    label_month = anomaly_month + pd.DateOffset(days=28)
    axes[1].annotate(
        "Anomaly",
        xy=(anomaly_month, anomaly_ads),
        xytext=(label_month, anomaly_ads * 0.78),
        arrowprops={"arrowstyle": "->", "color": PLOT_COLORS["neutral"]},
    )
    axes[2].annotate(
        "Anomaly",
        xy=(anomaly_month, anomaly_fees),
        xytext=(label_month, anomaly_fees * 0.68),
        arrowprops={"arrowstyle": "->", "color": PLOT_COLORS["neutral"]},
    )

    fig.tight_layout()
    return fig, axes


def plot_q2_anomaly_comparison(monthly_summary, monthly_without_seller, anomaly_seller_id=65950787, anomaly_month="2023-11-01"):
    """Plot monthly ads and fees with and without the anomaly seller."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    anomaly_month = pd.Timestamp(anomaly_month)
    fig, axes = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    axes[0].plot(monthly_summary[Q2_DATE_COLUMN], monthly_summary["total_ad_insertions"], label="All Sellers", color=PLOT_COLORS["q2"])
    axes[0].plot(
        monthly_without_seller[Q2_DATE_COLUMN],
        monthly_without_seller["total_ad_insertions"],
        linestyle="--",
        label=f"Excluding Seller {anomaly_seller_id}",
        color=PLOT_COLORS["neutral"],
    )
    axes[0].set_title("Monthly Ad Insertions: With and Without Anomaly Seller")
    axes[0].set_ylabel("Ads")

    axes[1].plot(monthly_summary[Q2_DATE_COLUMN], monthly_summary["total_fees"], label="All Sellers", color=PLOT_COLORS["q2"])
    axes[1].plot(
        monthly_without_seller[Q2_DATE_COLUMN],
        monthly_without_seller["total_fees"],
        linestyle="--",
        label=f"Excluding Seller {anomaly_seller_id}",
        color=PLOT_COLORS["neutral"],
    )
    axes[1].set_title("Monthly Fees: With and Without Anomaly Seller")
    axes[1].set_ylabel("Fees")
    axes[1].set_xlabel("Month")

    for ax in axes:
        format_number_axis(ax, axis="y")
        ax.grid(axis="y", alpha=0.3)
        ax.legend()
    format_eur_axis(axes[1], axis="y")

    fig.tight_layout()
    return fig, axes


def plot_q2_combined_anomaly_overview(monthly_summary, monthly_without_seller, anomaly_seller_id=65950787):
    """Combine active sellers with the anomaly comparison into one compact visual."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

    axes[0].plot(monthly_summary[Q2_DATE_COLUMN], monthly_summary["sellers"], color=PLOT_COLORS["q2"])
    axes[0].set_title("Monthly Active Sellers")
    axes[0].set_ylabel("Sellers")

    axes[1].plot(monthly_summary[Q2_DATE_COLUMN], monthly_summary["total_ad_insertions"], label="All Sellers", color=PLOT_COLORS["q2"])
    axes[1].plot(
        monthly_without_seller[Q2_DATE_COLUMN],
        monthly_without_seller["total_ad_insertions"],
        linestyle="--",
        label=f"Excluding Seller {anomaly_seller_id}",
        color=PLOT_COLORS["neutral"],
    )
    axes[1].set_title("Monthly Ad Insertions")
    axes[1].set_ylabel("Ads")

    axes[2].plot(monthly_summary[Q2_DATE_COLUMN], monthly_summary["total_fees"], label="All Sellers", color=PLOT_COLORS["q2"])
    axes[2].plot(
        monthly_without_seller[Q2_DATE_COLUMN],
        monthly_without_seller["total_fees"],
        linestyle="--",
        label=f"Excluding Seller {anomaly_seller_id}",
        color=PLOT_COLORS["neutral"],
    )
    axes[2].set_title("Monthly Fees")
    axes[2].set_ylabel("Fees")
    axes[2].set_xlabel("Month")

    for ax in axes:
        format_number_axis(ax, axis="y")
        ax.grid(axis="y", alpha=0.3)
    for ax in axes[1:]:
        ax.legend()
    format_eur_axis(axes[2], axis="y")

    fig.tight_layout()
    return fig, axes


def plot_q2_top_categories_by_fees(category_summary):
    """Plot the top 10 fee categories as a labeled horizontal bar chart."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    top_category_fees = category_summary.head(10).sort_values("total_fees")
    top_category_labels = top_category_fees[Q2_CATEGORY_COLUMN].map(readable_category_label)
    total_fees = category_summary["total_fees"].sum()
    bar_labels = [
        f"€{value:,.0f} ({value / total_fees:.1%})"
        for value in top_category_fees["total_fees"]
    ]
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.barh(top_category_labels, top_category_fees["total_fees"], color=PLOT_COLORS["primary"])
    ax.set_title("Top Categories by Fees")
    add_horizontal_bar_text_labels(ax, bar_labels)
    style_minimal_horizontal_bar(ax)
    fig.tight_layout()
    fig.subplots_adjust(left=0.33)
    return fig, ax


def plot_q2_fee_mix(dataframe):
    """Plot total fees by paid product."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    fee_mix = dataframe[existing_columns(dataframe, FEE_COLUMNS)].sum().sort_values()
    total_fees = fee_mix.sum()
    bar_labels = [f"€{value:,.0f} ({value / total_fees:.1%})" for value in fee_mix.values]
    fee_mix.index = [readable_metric_label(column) for column in fee_mix.index]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.barh(fee_mix.index, fee_mix.values, color=PLOT_COLORS["q2"])
    ax.set_title("Fee Mix by Paid Product")
    add_horizontal_bar_text_labels(ax, bar_labels)
    style_minimal_horizontal_bar(ax)
    fig.tight_layout()
    return fig, ax


def plot_q2_fee_concentration(seller_summary):
    """Plot cumulative fee concentration by seller rank."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    seller_fee_rank = seller_summary.sort_values("total_fees", ascending=False).reset_index(drop=True)
    seller_fee_rank["seller_rank_pct"] = (seller_fee_rank.index + 1) / len(seller_fee_rank) * 100
    seller_fee_rank["cumulative_fee_pct"] = seller_fee_rank["total_fees"].cumsum() / seller_fee_rank["total_fees"].sum() * 100
    top_25_fee_share = seller_fee_rank.loc[seller_fee_rank["seller_rank_pct"].ge(25), "cumulative_fee_pct"].iloc[0]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(seller_fee_rank["seller_rank_pct"], seller_fee_rank["cumulative_fee_pct"], color=PLOT_COLORS["q2"])
    ax.axvline(25, color=PLOT_COLORS["neutral"], linestyle="--", linewidth=1)
    ax.axhline(top_25_fee_share, color=PLOT_COLORS["neutral"], linestyle="--", linewidth=1)
    ax.annotate(
        f"Top 25% = {top_25_fee_share:.0f}% of fees",
        xy=(25, top_25_fee_share),
        xytext=(30, top_25_fee_share - 10),
        arrowprops={"arrowstyle": "->", "color": PLOT_COLORS["neutral"]},
    )
    ax.set_title("Seller Fee Concentration")
    ax.set_xlabel("Top Sellers Ranked by Fees (%)")
    ax.set_ylabel("Cumulative Fees (%)")
    format_percent_axis(ax, axis="both")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    return fig, ax


def percentile(series):
    """Rank a numeric signal as a 0-1 percentile."""
    return series.rank(pct=True, method="average")


def q2_window_summary(dataframe, prefix):
    """Aggregate Q2 seller activity for a named time window."""
    return (
        dataframe.groupby(Q2_USER_COLUMN, as_index=False)
        .agg(
            **{
                f"{prefix}_active_months": (Q2_DATE_COLUMN, "nunique"),
                f"{prefix}_total_ad_insertions": ("total_ad_insertions", "sum"),
                f"{prefix}_paid_usage": ("paid_marketplace_actions", "sum"),
                f"{prefix}_paid_visibility_uses": ("paid_visibility_uses", "sum"),
                f"{prefix}_total_fees": ("total_fees", "sum"),
            }
        )
    )


def q2_paid_product_breadth(dataframe):
    """Count how many paid product types each seller has used."""
    paid_product_columns = existing_columns(dataframe, ["N_PAID_AD_INSERTIONS"] + FEATURE_COUNT_COLUMNS)
    return (
        dataframe.assign(**{column: dataframe[column].gt(0) for column in paid_product_columns})
        .groupby(Q2_USER_COLUMN)[paid_product_columns]
        .max()
        .sum(axis=1)
        .rename("paid_product_breadth")
        .reset_index()
    )


def score_q2_outreach_readiness(dataframe, seller_summary=None, top_share=0.25):
    """Score sellers for outreach readiness using recency, adoption, consistency, growth, and fees."""
    data = add_q2_row_metrics(dataframe)

    if seller_summary is None:
        seller_summary = seller_level_q2_summary(data)

    last_month = data[Q2_DATE_COLUMN].max()
    recent_start = last_month - pd.DateOffset(months=5)
    previous_start = recent_start - pd.DateOffset(months=6)
    previous_end = recent_start - pd.DateOffset(days=1)

    scored = (
        seller_summary.merge(
            q2_window_summary(data[data[Q2_DATE_COLUMN].between(recent_start, last_month)], "recent"),
            on=Q2_USER_COLUMN,
            how="left",
        )
        .merge(
            q2_window_summary(data[data[Q2_DATE_COLUMN].between(previous_start, previous_end)], "previous"),
            on=Q2_USER_COLUMN,
            how="left",
        )
        .merge(q2_paid_product_breadth(data), on=Q2_USER_COLUMN, how="left")
    )

    fill_columns = [
        "recent_active_months",
        "recent_total_ad_insertions",
        "recent_paid_usage",
        "recent_paid_visibility_uses",
        "recent_total_fees",
        "previous_active_months",
        "previous_total_ad_insertions",
        "previous_paid_usage",
        "previous_paid_visibility_uses",
        "previous_total_fees",
        "paid_product_breadth",
    ]
    scored[fill_columns] = scored[fill_columns].fillna(0)

    scored["paid_usage_growth_ratio"] = (
        (scored["recent_paid_usage"] + 1) / (scored["previous_paid_usage"] + 1)
    )
    scored["commercial_growth_ratio"] = scored["paid_usage_growth_ratio"]
    scored["recent_paid_usage_share"] = (
        scored["recent_paid_usage"] / scored["paid_marketplace_actions"].clip(lower=1)
    )

    scored["recent_paid_usage_score"] = percentile(scored["recent_paid_usage"])
    scored["paid_product_breadth_score"] = percentile(scored["paid_product_breadth"])
    scored["consistency_score"] = percentile(scored["active_months"])
    scored["category_breadth_score"] = percentile(scored["categories"])
    scored["growth_score"] = percentile(scored["paid_usage_growth_ratio"])
    scored["fee_score"] = percentile(scored["total_fees"])
    outreach_score_columns = [
        "recent_paid_usage_score",
        "paid_product_breadth_score",
        "consistency_score",
        "category_breadth_score",
        "growth_score",
        "fee_score",
    ]
    scored["outreach_readiness_score"] = scored[outreach_score_columns].mean(axis=1)

    cohort_size = int(np.ceil(len(scored) * top_share))
    outreach_ready_ids = set(scored.nlargest(cohort_size, "outreach_readiness_score")[Q2_USER_COLUMN])
    fee_top_ids = set(scored.nlargest(cohort_size, "total_fees")[Q2_USER_COLUMN])

    scored["is_outreach_ready_group"] = scored[Q2_USER_COLUMN].isin(outreach_ready_ids)
    scored["is_total_fee_group"] = scored[Q2_USER_COLUMN].isin(fee_top_ids)
    scored["selection_group"] = np.select(
        [
            scored["is_outreach_ready_group"] & scored["is_total_fee_group"],
            scored["is_outreach_ready_group"],
            scored["is_total_fee_group"],
        ],
        ["Both groups", "Outreach ready group only", "Total-fee group only"],
        default="Neither",
    )

    scored["paid_visibility_score"] = percentile(scored["paid_visibility_uses"])
    scored["listing_volume_score"] = percentile(scored["total_ad_insertions"])
    bundle_fit_columns = [
        scored["paid_visibility_score"],
        scored["paid_product_breadth_score"],
        scored["listing_volume_score"],
    ]
    scored["bundle_fit_score"] = pd.concat(bundle_fit_columns, axis=1).mean(axis=1)
    bundle_fit_cutoff = scored.loc[scored["is_outreach_ready_group"], "bundle_fit_score"].quantile(0.60)
    scored["is_targeted_for_plus"] = (
        scored["is_outreach_ready_group"] & scored["bundle_fit_score"].ge(bundle_fit_cutoff)
    )
    scored["bundle_target_group"] = np.where(
        scored["is_targeted_for_plus"], "Targeted for Plus group", "Targeted for Basic group"
    )

    return scored.sort_values("outreach_readiness_score", ascending=False).reset_index(drop=True)


def q2_method_comparison(scored_sellers):
    """Compare the outreach-ready top quartile against a fee-only top quartile."""
    method_flags = {
        "Outreach ready group": "is_outreach_ready_group",
        "Total-fee group": "is_total_fee_group",
    }
    signal_score_columns = {
        "Avg total fees score": "fee_score",
        "Avg recent paid usage score": "recent_paid_usage_score",
        "Avg consistency score": "consistency_score",
        "Avg category breadth score": "category_breadth_score",
        "Avg recent growth score": "growth_score",
        "Avg paid product breadth score": "paid_product_breadth_score",
    }
    rows = []

    for method, flag in method_flags.items():
        selected = scored_sellers[scored_sellers[flag]]
        row = {
            "Method": method,
            "Selected Sellers": len(selected),
            "Avg fees per seller": selected["total_fees"].mean(),
        }
        row.update(
            {
                signal: selected[score_column].mean() * 100
                for signal, score_column in signal_score_columns.items()
            }
        )
        row["Avg outreach readiness score"] = selected["outreach_readiness_score"].mean() * 100
        rows.append(row)

    return pd.DataFrame(rows)


def q2_method_comparison_display(scored_sellers):
    """Return a formatted method comparison table for presentation."""
    return format_display_table(
        q2_method_comparison(scored_sellers),
        euro_columns=["Avg fees per seller"],
        decimal_columns=[
            "Avg total fees score",
            "Avg recent paid usage score",
            "Avg consistency score",
            "Avg category breadth score",
            "Avg recent growth score",
            "Avg paid product breadth score",
            "Avg outreach readiness score",
        ],
    )


def clean_q2_score_profile_axis(ax):
    """Remove visual axis scaffolding while keeping category and axis labels."""
    ax.grid(False)
    ax.tick_params(axis="x", which="both", bottom=False, top=False, labelbottom=False)
    ax.tick_params(axis="y", which="both", left=False, right=False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    return ax


def plot_q2_method_score_profile(scored_sellers):
    """Plot average signal scores for outreach-ready vs total-fee selection."""
    if plt is None:
        raise ImportError("matplotlib is required for plotting")

    comparison = q2_method_comparison(scored_sellers).set_index("Method")
    score_columns = [
        "Avg total fees score",
        "Avg recent paid usage score",
        "Avg consistency score",
        "Avg category breadth score",
        "Avg recent growth score",
        "Avg paid product breadth score",
        "Avg outreach readiness score",
    ]
    labels = [
        "Total fees",
        "Recent paid usage",
        "Consistency",
        "Category breadth",
        "Recent growth",
        "Paid product breadth",
        "Outreach readiness",
    ]
    y = np.arange(len(labels))
    bar_height = 0.36

    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    ax.barh(
        y - bar_height / 2,
        comparison.loc["Outreach ready group", score_columns],
        height=bar_height,
        color=PLOT_COLORS["q2"],
        label="Outreach ready group",
    )
    ax.barh(
        y + bar_height / 2,
        comparison.loc["Total-fee group", score_columns],
        height=bar_height,
        color=PLOT_COLORS["neutral"],
        label="Total-fee group",
    )

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 105)
    ax.set_xlabel("Average percentile score")
    ax.set_title("Signal Comparison by Seller Group")
    ax.legend(loc="lower right")
    clean_q2_score_profile_axis(ax)

    for patch in ax.patches:
        width = patch.get_width()
        ax.annotate(
            f"{width:.1f}",
            (width, patch.get_y() + patch.get_height() / 2),
            ha="left",
            va="center",
            xytext=(4, 0),
            textcoords="offset points",
            fontsize=8,
        )
    return fig, ax


def q2_method_overlap_summary(scored_sellers):
    """Summarize overlap between the outreach-ready and total-fee top quartiles."""
    outreach_ready = scored_sellers["is_outreach_ready_group"]
    fee = scored_sellers["is_total_fee_group"]
    return pd.DataFrame(
        [
            {"Comparison": "Selected by both groups", "Sellers": int((outreach_ready & fee).sum())},
            {"Comparison": "Outreach ready group only", "Sellers": int((outreach_ready & ~fee).sum())},
            {"Comparison": "Total-fee group only", "Sellers": int((~outreach_ready & fee).sum())},
        ]
    )


def plot_q2_method_overlap_venn(scored_sellers):
    """Plot a two-set Venn diagram for outreach-ready vs total-fee selection."""
    if plt is None or Circle is None:
        raise ImportError("matplotlib is required for plotting")

    outreach_ready = scored_sellers["is_outreach_ready_group"]
    fee = scored_sellers["is_total_fee_group"]
    both = int((outreach_ready & fee).sum())
    outreach_ready_only = int((outreach_ready & ~fee).sum())
    fee_only = int((~outreach_ready & fee).sum())

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    left = Circle((0.0, 0.0), 1.35, color=PLOT_COLORS["q2"], alpha=0.50)
    right = Circle((1.25, 0.0), 1.35, color=PLOT_COLORS["neutral"], alpha=0.45)
    ax.add_patch(left)
    ax.add_patch(right)

    ax.text(-0.65, 0.1, f"{outreach_ready_only:,}", ha="center", va="center", fontsize=20, fontweight="bold")
    ax.text(0.62, 0.1, f"{both:,}", ha="center", va="center", fontsize=20, fontweight="bold")
    ax.text(1.9, 0.1, f"{fee_only:,}", ha="center", va="center", fontsize=20, fontweight="bold")

    ax.text(-0.65, -0.2, "Outreach ready only", ha="center", va="center", fontsize=10)
    ax.text(0.62, -0.2, "Both groups", ha="center", va="center", fontsize=10)
    ax.text(1.9, -0.2, "Total-fee only", ha="center", va="center", fontsize=10)

    ax.set_title("Seller Overlap Between Targeting Groups", pad=16)
    ax.set_xlim(-1.65, 2.9)
    ax.set_ylim(-1.45, 1.85)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def q2_selection_summary(scored_sellers):
    """Summarize sellers selected by both, one, or neither prioritization group."""
    return (
        scored_sellers.groupby("selection_group", as_index=False)
        .agg(
            sellers=(Q2_USER_COLUMN, "nunique"),
            avg_total_fees=("total_fees", "mean"),
            avg_recent_total_fees=("recent_total_fees", "mean"),
            avg_active_months=("active_months", "mean"),
            avg_recent_paid_usage=("recent_paid_usage", "mean"),
            avg_categories=("categories", "mean"),
            avg_paid_product_breadth=("paid_product_breadth", "mean"),
            median_growth_ratio=("paid_usage_growth_ratio", "median"),
        )
        .sort_values("sellers", ascending=False)
        .reset_index(drop=True)
    )


def q2_selection_summary_display(scored_sellers):
    """Return a formatted seller-selection comparison table."""
    selection_summary = q2_selection_summary(scored_sellers).rename(
        columns={
            "selection_group": "Selection Group",
            "sellers": "Sellers",
            "avg_total_fees": "Avg Fees per Seller",
            "avg_recent_total_fees": "Avg 6mo Fees per Seller",
            "avg_active_months": "Avg Active Months",
            "avg_recent_paid_usage": "Avg Recent Paid Usage",
            "avg_categories": "Avg Categories",
            "avg_paid_product_breadth": "Avg Paid Product Breadth",
            "median_growth_ratio": "Median 6mo Paid Action Growth Rate",
        }
    )
    selection_summary["Median 6mo Paid Action Growth Rate"] = selection_summary[
        "Median 6mo Paid Action Growth Rate"
    ].map(lambda value: f"{value - 1:+.0%}")
    return format_display_table(
        selection_summary,
        euro_columns=["Avg Fees per Seller", "Avg 6mo Fees per Seller"],
        decimal_columns=[
            "Avg Active Months",
            "Avg Recent Paid Usage",
            "Avg Categories",
            "Avg Paid Product Breadth",
        ],
    )


def q2_bundle_targeting_summary(scored_sellers):
    """Summarize Basic vs Plus targeting inside the outreach-ready group."""
    priority_cohort = scored_sellers[scored_sellers["is_outreach_ready_group"]]
    summary = (
        priority_cohort.groupby("bundle_target_group", as_index=False)
        .agg(
            sellers=(Q2_USER_COLUMN, "nunique"),
            avg_fees_per_seller=("total_fees", "mean"),
            avg_paid_visibility_score=("paid_visibility_score", "mean"),
            avg_paid_product_breadth_score=("paid_product_breadth_score", "mean"),
            avg_listing_volume_score=("listing_volume_score", "mean"),
            avg_bundle_fit_score=("bundle_fit_score", "mean"),
            avg_outreach_readiness_score=("outreach_readiness_score", "mean"),
        )
        .sort_values("bundle_target_group", ascending=False)
        .reset_index(drop=True)
    )
    score_columns = [
        "avg_paid_visibility_score",
        "avg_paid_product_breadth_score",
        "avg_listing_volume_score",
        "avg_bundle_fit_score",
        "avg_outreach_readiness_score",
    ]
    summary[score_columns] *= 100
    return summary


def q2_bundle_targeting_display(scored_sellers):
    """Return a formatted Basic vs Plus targeting table."""
    bundle_targeting = q2_bundle_targeting_summary(scored_sellers).rename(
        columns={
            "bundle_target_group": "Target Group",
            "sellers": "Selected Sellers",
            "avg_fees_per_seller": "Avg fees per seller",
            "avg_paid_visibility_score": "Avg paid visibility score",
            "avg_paid_product_breadth_score": "Avg paid product breadth score",
            "avg_listing_volume_score": "Avg listing volume score",
            "avg_bundle_fit_score": "Avg bundle fit score",
            "avg_outreach_readiness_score": "Avg outreach readiness score",
        }
    )
    return format_display_table(
        bundle_targeting,
        euro_columns=["Avg fees per seller"],
        decimal_columns=[
            "Avg paid visibility score",
            "Avg paid product breadth score",
            "Avg listing volume score",
            "Avg bundle fit score",
            "Avg outreach readiness score",
        ],
    )


def plot_q2_bundle_score_profile(scored_sellers):
    """Plot average bundle-fit scores for Plus vs Basic targeting groups."""
    if plt is None:
        raise ImportError("matplotlib is required for plotting")

    comparison = q2_bundle_targeting_summary(scored_sellers).set_index("bundle_target_group")
    score_columns = [
        "avg_paid_visibility_score",
        "avg_paid_product_breadth_score",
        "avg_listing_volume_score",
        "avg_bundle_fit_score",
        "avg_outreach_readiness_score",
    ]
    labels = [
        "Paid visibility",
        "Paid product breadth",
        "Listing volume",
        "Bundle fit",
        "Outreach readiness",
    ]
    y = np.arange(len(labels))
    bar_height = 0.36

    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.barh(
        y - bar_height / 2,
        comparison.loc["Targeted for Plus group", score_columns],
        height=bar_height,
        color=PLOT_COLORS["q2"],
        label="Plus Group",
    )
    ax.barh(
        y + bar_height / 2,
        comparison.loc["Targeted for Basic group", score_columns],
        height=bar_height,
        color=PLOT_COLORS["neutral"],
        label="Basic Group",
    )

    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlim(0, 105)
    ax.set_xlabel("Average percentile score")
    ax.set_title("Signal Comparison by Seller Group")
    ax.legend(loc="lower right")
    clean_q2_score_profile_axis(ax)

    for patch in ax.patches:
        width = patch.get_width()
        ax.annotate(
            f"{width:.1f}",
            (width, patch.get_y() + patch.get_height() / 2),
            ha="left",
            va="center",
            xytext=(4, 0),
            textcoords="offset points",
            fontsize=8,
        )
    return fig, ax


def q2_scored_sellers_export(scored_sellers):
    """Return a seller-level scoring table for preview and CSV export."""
    export = scored_sellers.rename(
        columns={
            "fee_score": "total_fees_score",
            "growth_score": "recent_growth_score",
        }
    ).copy()

    score_columns = [
        "recent_paid_usage_score",
        "consistency_score",
        "category_breadth_score",
        "recent_growth_score",
        "total_fees_score",
        "paid_visibility_score",
        "paid_product_breadth_score",
        "listing_volume_score",
        "outreach_readiness_score",
        "bundle_fit_score",
    ]
    export[score_columns] = export[score_columns] * 100

    column_order = [
        Q2_USER_COLUMN,
        "outreach_readiness_score",
        "recent_paid_usage_score",
        "consistency_score",
        "category_breadth_score",
        "recent_growth_score",
        "total_fees_score",
        "paid_visibility_score",
        "paid_product_breadth_score",
        "listing_volume_score",
        "recent_paid_usage",
        "active_months",
        "categories",
        "total_ad_insertions",
        "paid_usage_growth_ratio",
        "total_fees",
        "paid_product_breadth",
        "is_outreach_ready_group",
        "is_total_fee_group",
        "is_targeted_for_plus",
        "selection_group",
        "bundle_fit_score",
        "bundle_target_group",
    ]
    return export[column_order].round(2)


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
    summary = (
        dataframe[group_column]
        .value_counts(dropna=False)
        .rename_axis(group_column)
        .reset_index(name="registrations")
    )
    summary["share"] = summary["registrations"] / summary["registrations"].sum()
    return summary


Q3_EXPECTED_COLUMNS = ["User ID", "Customer type", "Bundle", "Start", "End"]
Q3_BUNDLE_PRICES = {"Basic": 19.99, "Plus": 49.99}


def load_q3_bundle_data(data_path=Q3_CSV_PATH):
    """Load, validate, and normalize the Q3 bundle registration intervals."""
    data = pd.read_csv(data_path)
    missing_columns = sorted(set(Q3_EXPECTED_COLUMNS) - set(data.columns))
    if missing_columns:
        raise ValueError(f"Missing expected columns: {missing_columns}")

    data = data.copy()
    data["Start"] = pd.to_datetime(data["Start"], errors="raise")
    data["End"] = pd.to_datetime(data["End"], errors="raise")
    data["Bundle"] = data["Bundle"].replace({"Basis": "Basic"})
    data["is_open_ended"] = data["End"].eq(ACTIVE_SUBSCRIPTION_END_DATE)
    data["End_actual"] = data["End"].mask(data["is_open_ended"])
    data["is_bundle"] = data["Bundle"].isin(Q3_BUNDLE_PRICES)
    return data


def q3_reference_dates(dataframe):
    """Return the launch start and dashboard reference date for Q3 monitoring."""
    finite_end_max = dataframe.loc[~dataframe["is_open_ended"], "End"].max()
    reference_date = max(dataframe["Start"].max(), finite_end_max)
    launch_start = dataframe.loc[dataframe["is_bundle"], "Start"].min()
    return launch_start, reference_date


def q3_week_start(series):
    """Map dates to Monday-start weekly buckets."""
    return series.dt.to_period("W-SUN").dt.start_time


def q3_overlap_count(group, reference_date):
    """Count potential overlapping intervals within one seller's history."""
    ordered = group.sort_values(["Start", "End"])
    active_until = pd.Timestamp.min
    overlaps = 0

    for row in ordered.itertuples(index=False):
        end = reference_date + pd.Timedelta(days=1) if row.is_open_ended else row.End
        if row.Start < active_until:
            overlaps += 1
        active_until = max(active_until, end)

    return overlaps


def q3_potential_overlaps(dataframe, reference_date):
    """Return potential overlap counts by seller."""
    return (
        dataframe.groupby(Q3_USER_COLUMN, sort=False)
        .apply(lambda group: q3_overlap_count(group, reference_date), include_groups=False)
        .rename("overlapping_intervals")
    )


def q3_structure_summary(dataframe, reference_date):
    """Return a compact data structure and quality summary for Q3."""
    finite_end = dataframe.loc[~dataframe["is_open_ended"], "End"]
    overlaps = q3_potential_overlaps(dataframe, reference_date)
    return pd.DataFrame(
        {
            "Metric": [
                "Rows",
                "Unique sellers",
                "Start date range",
                "Finite end date range",
                "Open-ended rows",
                "Missing values",
                "Duplicate rows",
                "Sellers with potential overlapping intervals",
            ],
            "Value": [
                f"{len(dataframe):,}",
                f"{dataframe[Q3_USER_COLUMN].nunique():,}",
                f"{dataframe['Start'].min():%Y-%m-%d} to {dataframe['Start'].max():%Y-%m-%d}",
                f"{finite_end.min():%Y-%m-%d} to {finite_end.max():%Y-%m-%d}",
                f"{dataframe['is_open_ended'].sum():,}",
                f"{int(dataframe[Q3_EXPECTED_COLUMNS].isna().sum().sum()):,}",
                f"{int(dataframe[Q3_EXPECTED_COLUMNS].duplicated().sum()):,}",
                f"{int((overlaps > 0).sum()):,}",
            ],
        }
    )


def q3_distribution_summary(dataframe):
    """Return compact distributions for customer type and bundle."""
    return pd.concat(
        [
            dataframe["Customer type"]
            .value_counts(dropna=False)
            .rename_axis("Value")
            .reset_index(name="Rows")
            .assign(Field="Customer type"),
            dataframe["Bundle"]
            .value_counts(dropna=False)
            .rename_axis("Value")
            .reset_index(name="Rows")
            .assign(Field="Bundle"),
        ],
        ignore_index=True,
    )[["Field", "Value", "Rows"]]


def q3_short_eda_summary(dataframe, sellers, weekly_metrics, revenue_4w, reference_date):
    """Return a compact EDA summary for the Q3 data structure section."""
    bundle_sellers = sellers.dropna(subset=["first_bundle_start"])
    first_bundle_mix = bundle_sellers["first_bundle_type"].value_counts()
    latest_week = weekly_metrics.iloc[-1]
    peak_week = weekly_metrics["New bundle registrations"].idxmax()
    peak_registrations = weekly_metrics.loc[peak_week, "New bundle registrations"]
    multi_interval_sellers = dataframe.loc[dataframe["is_bundle"]].groupby(Q3_USER_COLUMN).size().gt(1).sum()
    multi_bundle_sellers = dataframe.loc[dataframe["is_bundle"]].groupby(Q3_USER_COLUMN)["Bundle"].nunique().gt(1).sum()
    current_no_bundle = int(bundle_sellers["current_bundle_type"].eq("No bundle").sum())
    complete_revenue = q3_complete_revenue_periods(revenue_4w, reference_date)
    latest_complete_revenue = np.nan
    if not complete_revenue.empty:
        latest_complete_revenue = complete_revenue.iloc[-1]["modeled_paid_revenue_eur"]

    rows = [
        ("First bundle starters", f"{len(bundle_sellers):,}"),
        ("Basic-first share", pct(first_bundle_mix.get("Basic", 0) / len(bundle_sellers))),
        ("Plus-first share", pct(first_bundle_mix.get("Plus", 0) / len(bundle_sellers))),
        ("Peak weekly registrations", f"{int(peak_registrations):,} in week of {peak_week:%Y-%m-%d}"),
        ("Latest active paid sellers", f"{int(latest_week['Total active paid sellers']):,}"),
        ("Latest active trial sellers", f"{int(latest_week['Active trial sellers']):,}"),
        ("Current no-bundle sellers", f"{current_no_bundle:,}"),
        ("Current Plus share of paid base", pct(latest_week["Plus share of active paid sellers"])),
        ("Sellers with multiple bundle periods", f"{int(multi_interval_sellers):,}"),
        ("Sellers using both Basic and Plus", f"{int(multi_bundle_sellers):,}"),
        ("Latest complete modeled revenue", eur(latest_complete_revenue)),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Value"])


def q3_short_eda_findings(dataframe, sellers, weekly_metrics, reference_date):
    """Return short presentation-ready findings from the Q3 registration data."""
    bundle_sellers = sellers.dropna(subset=["first_bundle_start"])
    first_bundle_mix = bundle_sellers["first_bundle_type"].value_counts(normalize=True)
    peak_week = weekly_metrics["New bundle registrations"].idxmax()
    peak_registrations = weekly_metrics.loc[peak_week, "New bundle registrations"]
    latest_week = weekly_metrics.iloc[-1]
    open_ended_share = dataframe["is_open_ended"].mean()
    current_no_bundle = int(bundle_sellers["current_bundle_type"].eq("No bundle").sum())
    multi_interval_share = (
        dataframe.loc[dataframe["is_bundle"]]
        .groupby(Q3_USER_COLUMN)
        .size()
        .gt(1)
        .mean()
    )

    return pd.DataFrame(
        [
            {
                "Finding": "Launch demand was front-loaded",
                "Evidence": f"Peak week: {int(peak_registrations):,} new first-bundle registrations ({peak_week:%Y-%m-%d}).",
                "Interpretation": "The launch created an early registration spike; later monitoring should focus on paid-base retention.",
            },
            {
                "Finding": "Basic is the larger entry bundle",
                "Evidence": (
                    f"{pct(first_bundle_mix.get('Basic', 0))} of first bundle starts were Basic; "
                    f"{pct(first_bundle_mix.get('Plus', 0))} were Plus."
                ),
                "Interpretation": "Basic appears to be the default entry point; Plus share is the key monetization-quality signal.",
            },
            {
                "Finding": "Most visible intervals are still open",
                "Evidence": f"{pct(open_ended_share)} of rows use 2099-12-31 as the open-ended active marker.",
                "Interpretation": "Open-ended rows represent current active intervals, not real 2099 end dates.",
            },
            {
                "Finding": "Switching and repeat intervals exist",
                "Evidence": f"{pct(multi_interval_share)} of bundle sellers have more than one bundle period.",
                "Interpretation": "Seller-level metrics should use period logic, not one row per seller assumptions.",
            },
            {
                "Finding": "Many past starters currently have no bundle",
                "Evidence": (
                    f"{current_no_bundle:,} sellers have a current `No bundle` interval; "
                    f"{int(latest_week['Active trial sellers']):,} are still in trial as of {reference_date:%Y-%m-%d}."
                ),
                "Interpretation": "The file tracks bundle starters over time, including no-bundle intervals after stopping. It is not a full universe of never-adopting sellers.",
            },
        ]
    )


def q3_interval_complexity_summary(dataframe):
    """Summarize repeat intervals and bundle switching at seller level."""
    bundle_rows = dataframe.loc[dataframe["is_bundle"]]
    seller_intervals = (
        bundle_rows.groupby(Q3_USER_COLUMN)
        .agg(
            intervals=("Bundle", "size"),
            bundle_types=("Bundle", "nunique"),
        )
    )
    interval_buckets = (
        seller_intervals["intervals"]
        .clip(upper=4)
        .map({1: "1 interval", 2: "2 intervals", 3: "3 intervals", 4: "4+ intervals"})
        .value_counts()
        .reindex(["1 interval", "2 intervals", "3 intervals", "4+ intervals"], fill_value=0)
    )
    return interval_buckets, seller_intervals


def plot_q3_eda_launch_demand(weekly_metrics):
    """Plot weekly launch demand with peak-week annotation."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    plot_data = weekly_metrics["New bundle registrations"]
    peak_week = plot_data.idxmax()
    x_values = np.arange(len(plot_data))
    peak_position = plot_data.index.get_loc(peak_week)

    _, ax = plt.subplots(figsize=(11, 4))
    ax.bar(
        x_values,
        plot_data.to_numpy(),
        color=PLOT_COLORS["q3"],
        width=0.85,
    )
    ax.annotate(
        f"Peak: {int(plot_data.loc[peak_week]):,}",
        xy=(peak_position, plot_data.loc[peak_week]),
        xytext=(0, 12),
        textcoords="offset points",
        ha="center",
        color=PLOT_COLORS["text"],
    )
    format_q3_month_axis_for_weekly_bars(ax, plot_data.index, month_step=2)
    ax.set_title("EDA: Weekly First-Bundle Registrations")
    ax.set_xlabel("")
    ax.set_ylabel("Sellers")
    format_number_axis(ax, "y")
    return ax


def plot_q3_eda_bundle_mix_shift(sellers):
    """Compare first-bundle mix with current active paid mix."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    first_mix = (
        sellers.dropna(subset=["first_bundle_type"])["first_bundle_type"]
        .value_counts(normalize=True)
        .reindex(["Basic", "Plus"], fill_value=0)
    )
    paid_mix = (
        sellers.loc[sellers["active_paid_flag"], "current_bundle_type"]
        .value_counts(normalize=True)
        .reindex(["Basic", "Plus"], fill_value=0)
    )
    plot_data = pd.DataFrame(
        {
            "First bundle starts": first_mix,
            "Current active paid base": paid_mix,
        }
    ).mul(100)
    ax = plot_data.T.plot(
        kind="bar",
        figsize=(8, 4),
        color=[PLOT_COLORS["neutral"], PLOT_COLORS["q3"]],
        width=0.7,
    )
    ax.set_title("EDA: Bundle Mix at Entry vs Current Paid Base")
    ax.set_xlabel("")
    ax.set_ylabel("Share of sellers (%)")
    format_percent_axis(ax, "y")
    ax.tick_params(axis="x", rotation=0)
    ax.legend(title="")
    return ax


def plot_q3_eda_current_status(sellers):
    """Plot current seller status after first bundle start."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    starters = sellers.dropna(subset=["first_bundle_start"])
    status_counts = pd.Series(
        {
            "Active paid Basic": int(
                (starters["active_paid_flag"] & starters["current_bundle_type"].eq("Basic")).sum()
            ),
            "Active paid Plus": int(
                (starters["active_paid_flag"] & starters["current_bundle_type"].eq("Plus")).sum()
            ),
            "Active trial": int(starters["active_trial_flag"].sum()),
            "Currently no bundle": int(starters["current_bundle_type"].eq("No bundle").sum()),
            "No active interval": int(starters["current_status"].eq("Inactive").sum()),
        }
    )
    ax = status_counts.plot(
        kind="barh",
        figsize=(8, 4),
        color=[
            PLOT_COLORS["neutral"],
            PLOT_COLORS["q3"],
            PLOT_COLORS["warning"],
            PLOT_COLORS["danger"],
            PLOT_COLORS["danger"],
        ],
    )
    ax.set_title("EDA: Current Status of Bundle Starters")
    ax.set_xlabel("Sellers")
    ax.set_ylabel("")
    format_number_axis(ax, "x")
    ax.invert_yaxis()
    return ax


def q3_bundle_status_timeseries(dataframe, sellers, launch_start, reference_date):
    """Return weekly seller counts by current bundle and trial/subscription status."""
    weeks = pd.date_range(launch_start.to_period("W-SUN").start_time, reference_date, freq="W-MON")
    rows = []

    for week in weeks:
        snapshot_date = min(week + pd.Timedelta(days=6), reference_date)
        current_bundle = q3_current_bundle_at(dataframe, sellers.index, snapshot_date)
        current_bundle = current_bundle.where(current_bundle.isin(["Basic", "Plus"]), "No bundle")
        is_trial = snapshot_date < sellers["trial_end_date"]
        counts = current_bundle.value_counts().reindex(["Basic", "Plus", "No bundle"], fill_value=0)
        rows.append(
            {
                "week": week,
                "snapshot_date": snapshot_date,
                "Basic": int(counts["Basic"]),
                "Plus": int(counts["Plus"]),
                "No bundle": int(counts["No bundle"]),
                "Basic subscription": int((current_bundle.eq("Basic") & ~is_trial).sum()),
                "Basic trial": int((current_bundle.eq("Basic") & is_trial).sum()),
                "Plus subscription": int((current_bundle.eq("Plus") & ~is_trial).sum()),
                "Plus trial": int((current_bundle.eq("Plus") & is_trial).sum()),
            }
        )

    return pd.DataFrame(rows).set_index("week")


def plot_q3_eda_bundle_status_timeseries(dataframe, sellers, launch_start, reference_date):
    """Plot weekly seller counts by bundle status and trial/subscription split."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    status_ts = q3_bundle_status_timeseries(dataframe, sellers, launch_start, reference_date)
    fig, axes = plt.subplots(
        2,
        1,
        figsize=(11, 7),
        sharex=True,
        constrained_layout=True,
    )

    status_ts[["Basic", "Plus", "No bundle"]].plot(
        ax=axes[0],
        color=[PLOT_COLORS["neutral"], PLOT_COLORS["q3"], PLOT_COLORS["danger"]],
        linewidth=2,
    )
    axes[0].set_title("EDA: Seller Bundle Status Over Time")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Sellers")
    format_number_axis(axes[0], "y")
    axes[0].legend(title="")

    split_columns = [
        "Basic subscription",
        "Plus subscription",
        "Basic trial",
        "Plus trial",
        "No bundle",
    ]
    status_ts[split_columns].plot(
        ax=axes[1],
        color=[
            PLOT_COLORS["neutral"],
            PLOT_COLORS["q3"],
            PLOT_COLORS["neutral"],
            PLOT_COLORS["q3"],
            PLOT_COLORS["danger"],
        ],
        linewidth=2,
    )
    for line, linestyle in zip(axes[1].lines, ["-", "-", "--", "--", "-"]):
        line.set_linestyle(linestyle)
    axes[1].set_title("EDA: Bundle Status by Trial vs Subscription")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Sellers")
    format_number_axis(axes[1], "y")
    axes[1].legend(title="")
    return fig, axes


def plot_q3_eda_open_ended_intervals(dataframe):
    """Plot finite vs open-ended rows by bundle type."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    plot_data = (
        dataframe.assign(interval_status=np.where(dataframe["is_open_ended"], "Open-ended", "Finite end"))
        .pivot_table(index="Bundle", columns="interval_status", values=Q3_USER_COLUMN, aggfunc="count", fill_value=0)
        .reindex(index=["Basic", "Plus"], columns=["Finite end", "Open-ended"], fill_value=0)
    )
    ax = plot_data.plot(
        kind="bar",
        figsize=(8, 4),
        color=[PLOT_COLORS["neutral"], PLOT_COLORS["q3"]],
        width=0.7,
    )
    ax.set_title("EDA: Interval End-State by Bundle")
    ax.set_xlabel("")
    ax.set_ylabel("Rows")
    format_number_axis(ax, "y")
    ax.tick_params(axis="x", rotation=0)
    ax.legend(title="")
    return ax


def plot_q3_eda_interval_complexity(dataframe):
    """Plot seller-level repeat bundle periods and switching complexity."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    interval_buckets, seller_intervals = q3_interval_complexity_summary(dataframe)
    switcher_count = int(seller_intervals["bundle_types"].gt(1).sum())
    one_bundle_multi_interval = int(
        (seller_intervals["intervals"].gt(1) & seller_intervals["bundle_types"].eq(1)).sum()
    )
    complexity = pd.concat(
        [
            interval_buckets,
            pd.Series(
                {
                    "Repeat, same bundle": one_bundle_multi_interval,
                    "Used Basic and Plus": switcher_count,
                }
            ),
        ]
    )
    ax = complexity.plot(
        kind="barh",
        figsize=(9, 4.5),
        color=[
            PLOT_COLORS["neutral"],
            PLOT_COLORS["neutral"],
            PLOT_COLORS["neutral"],
            PLOT_COLORS["neutral"],
            PLOT_COLORS["warning"],
            PLOT_COLORS["q3"],
        ],
    )
    ax.set_title("EDA: Repeat Bundle Periods and Switching")
    ax.set_xlabel("Sellers")
    ax.set_ylabel("")
    format_number_axis(ax, "x")
    ax.invert_yaxis()
    return ax


def q3_customer_type_eda_summary(dataframe, sellers):
    """Return customer-type EDA metrics for Q3 bundle starters."""
    starters = sellers.dropna(subset=["first_bundle_start"]).copy()
    bundle_rows = dataframe.loc[dataframe["is_bundle"]]
    seller_intervals = (
        bundle_rows.groupby(Q3_USER_COLUMN)
        .agg(bundle_periods=("Bundle", "size"), bundle_types=("Bundle", "nunique"))
        .reindex(starters.index)
        .fillna(0)
    )
    rows = []

    for customer_type, group in starters.groupby("customer_type", dropna=False):
        users = group.index
        paid = group["active_paid_flag"]
        current_bundle = group["current_bundle_type"]
        active_paid_sellers = int(paid.sum())
        rows.append(
            {
                "Customer type": customer_type,
                "Bundle starters": len(group),
                "Basic-first share": group["first_bundle_type"].eq("Basic").mean(),
                "Plus-first share": group["first_bundle_type"].eq("Plus").mean(),
                "Active paid sellers": active_paid_sellers,
                "Plus share of active paid sellers": (
                    (paid & current_bundle.eq("Plus")).sum() / active_paid_sellers
                    if active_paid_sellers
                    else np.nan
                ),
                "Current no-bundle share": current_bundle.eq("No bundle").mean(),
                "Multiple bundle-period share": seller_intervals.loc[users, "bundle_periods"].gt(1).mean(),
                "Used Basic and Plus share": seller_intervals.loc[users, "bundle_types"].gt(1).mean(),
            }
        )

    return pd.DataFrame(rows).sort_values("Bundle starters", ascending=False).reset_index(drop=True)


def q3_customer_type_eda_display_table(dataframe, sellers):
    """Return formatted customer-type EDA metrics."""
    return q3_format_rate_table(
        q3_customer_type_eda_summary(dataframe, sellers),
        rate_columns=[
            "Basic-first share",
            "Plus-first share",
            "Plus share of active paid sellers",
            "Current no-bundle share",
            "Multiple bundle-period share",
            "Used Basic and Plus share",
        ],
        integer_columns=["Bundle starters", "Active paid sellers"],
    )


def q3_customer_type_insights(dataframe, sellers):
    """Return concise customer-type EDA findings."""
    summary = q3_customer_type_eda_summary(dataframe, sellers).set_index("Customer type")
    if not {"SYI", "Pro"}.issubset(summary.index):
        return pd.DataFrame(columns=["Finding", "Evidence", "Interpretation"])

    pro = summary.loc["Pro"]
    syi = summary.loc["SYI"]

    return pd.DataFrame(
        [
            {
                "Finding": "Pro sellers are a smaller part of the file",
                "Evidence": f"Pro: {int(pro['Bundle starters']):,} starters; SYI: {int(syi['Bundle starters']):,} starters.",
                "Interpretation": "Customer type matters for sizing, but not necessarily for quality.",
            },
            {
                "Finding": "Pro starts slightly more often on Plus",
                "Evidence": (
                    f"Plus-first share: Pro {pro['Plus-first share']:.1%}; "
                    f"SYI {syi['Plus-first share']:.1%}."
                ),
                "Interpretation": "This is directionally useful for positioning, but the gap is modest.",
            },
            {
                "Finding": "Paid mix is nearly the same",
                "Evidence": (
                    f"Paid Plus share: Pro {pro['Plus share of active paid sellers']:.1%}; "
                    f"SYI {syi['Plus share of active paid sellers']:.1%}."
                ),
                "Interpretation": "Customer type alone does not strongly separate monetization quality.",
            },
            {
                "Finding": "No-bundle share is also similar",
                "Evidence": (
                    f"No-bundle share: Pro {pro['Current no-bundle share']:.1%}; "
                    f"SYI {syi['Current no-bundle share']:.1%}."
                ),
                "Interpretation": "Customer type is not a strong churn/status signal in this dataset.",
            },
        ]
    )


def q3_customer_type_insights_markdown(dataframe, sellers):
    """Return customer-type EDA findings as a Markdown bullet list."""
    insights = q3_customer_type_insights(dataframe, sellers)
    if insights.empty:
        return "_No customer-type insight available._"

    lines = []
    for _, row in insights.iterrows():
        lines.append(
            f"- **{row['Finding']}**  \n"
            f"  Evidence: {row['Evidence']}  \n"
            f"  Interpretation: {row['Interpretation']}"
        )
    return "\n".join(lines)


def plot_q3_customer_type_comparison(dataframe, sellers):
    """Plot selected customer-type differences without duplicating all EDA views."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    summary = q3_customer_type_eda_summary(dataframe, sellers).set_index("Customer type")
    plot_data = summary[
        [
            "Plus-first share",
            "Plus share of active paid sellers",
            "Current no-bundle share",
            "Used Basic and Plus share",
        ]
    ].reindex(["SYI", "Pro"]).mul(100)
    plot_data = plot_data.rename(
        columns={
            "Plus-first share": "Plus-first",
            "Plus share of active paid sellers": "Paid Plus share",
            "Current no-bundle share": "No bundle now",
            "Used Basic and Plus share": "Used both bundles",
        }
    )
    ax = plot_data.T.plot(
        kind="bar",
        figsize=(10, 4.5),
        color=[PLOT_COLORS["neutral"], PLOT_COLORS["q3"]],
    )
    ax.set_title("EDA: Customer Type Comparison")
    ax.set_xlabel("")
    ax.set_ylabel("Share of sellers (%)")
    format_percent_axis(ax, "y")
    ax.tick_params(axis="x", rotation=0)
    ax.legend(title="")
    return ax


def q3_dashboard_data(data_path=Q3_CSV_PATH, cohort_window_days=FREE_TRIAL_DAYS):
    """Build the reusable Q3 dashboard inputs from the bundle registration file."""
    bundle_df = load_q3_bundle_data(data_path)
    launch_start, dashboard_reference_date = q3_reference_dates(bundle_df)
    seller_fields = q3_seller_fields(bundle_df, dashboard_reference_date)
    weekly_metrics = q3_weekly_metrics(
        bundle_df,
        seller_fields,
        launch_start,
        dashboard_reference_date,
    )
    revenue_events = q3_modeled_revenue_events(
        bundle_df,
        seller_fields,
        dashboard_reference_date,
    )
    revenue_4w = q3_revenue_by_4_week_period(revenue_events, launch_start)
    revenue_by_bundle = q3_revenue_by_4_week_period_and_bundle(revenue_events, launch_start)
    registrations_4w = q3_registrations_by_4_week_period(seller_fields, launch_start)
    cohort_metrics_28d = q3_cohort_metrics(
        bundle_df,
        seller_fields,
        launch_start,
        dashboard_reference_date,
        cohort_window_days=cohort_window_days,
    )
    segment_metrics = q3_segment_metrics(
        bundle_df,
        seller_fields,
        launch_start,
        dashboard_reference_date,
    )

    return {
        "bundle_df": bundle_df,
        "launch_start": launch_start,
        "dashboard_reference_date": dashboard_reference_date,
        "seller_fields": seller_fields,
        "weekly_metrics": weekly_metrics,
        "revenue_events": revenue_events,
        "revenue_4w": revenue_4w,
        "revenue_by_bundle": revenue_by_bundle,
        "registrations_4w": registrations_4w,
        "cohort_metrics_28d": cohort_metrics_28d,
        "segment_metrics": segment_metrics,
    }


def q3_current_bundle_at(dataframe, user_ids, as_of_date):
    """Return each seller's active interval bundle at a point in time."""
    active = dataframe[
        (dataframe[Q3_USER_COLUMN].isin(user_ids))
        & (dataframe["Start"] <= as_of_date)
        & (dataframe["is_open_ended"] | (dataframe["End"] > as_of_date))
    ].copy()
    current = active.sort_values([Q3_USER_COLUMN, "Start", "End"]).groupby(Q3_USER_COLUMN).tail(1)
    return current.set_index(Q3_USER_COLUMN)["Bundle"].reindex(user_ids)


def q3_current_bundle_at_checkpoints(dataframe, checkpoints):
    """Return active interval bundle for seller-specific checkpoint dates.

    ``checkpoints`` must be a Series indexed by seller ID, with one checkpoint date
    per seller. The latest active interval at that seller's checkpoint is returned.
    """
    checkpoint_frame = (
        checkpoints.rename("checkpoint")
        .dropna()
        .reset_index()
        .rename(columns={checkpoints.index.name or "index": Q3_USER_COLUMN})
    )
    if checkpoint_frame.empty:
        return pd.Series(index=checkpoints.index, dtype=object)

    candidate_intervals = checkpoint_frame.merge(
        dataframe[[Q3_USER_COLUMN, "Bundle", "Start", "End", "is_open_ended"]],
        on=Q3_USER_COLUMN,
        how="left",
    )
    active = candidate_intervals[
        (candidate_intervals["Start"] <= candidate_intervals["checkpoint"])
        & (
            candidate_intervals["is_open_ended"]
            | (candidate_intervals["End"] > candidate_intervals["checkpoint"])
        )
    ]
    current = (
        active.sort_values([Q3_USER_COLUMN, "checkpoint", "Start", "End"])
        .groupby([Q3_USER_COLUMN, "checkpoint"], as_index=False)
        .tail(1)
    )
    bundles = current.set_index(Q3_USER_COLUMN)["Bundle"]
    return bundles.reindex(checkpoints.index)


def q3_seller_fields(dataframe, reference_date):
    """Derive one row per seller for current trial/paid status monitoring."""
    bundle_events = dataframe.loc[dataframe["is_bundle"]].copy()
    first_bundle = (
        bundle_events.sort_values([Q3_USER_COLUMN, "Start", "Bundle"])
        .drop_duplicates(Q3_USER_COLUMN, keep="first")[[Q3_USER_COLUMN, "Customer type", "Bundle", "Start"]]
        .rename(columns={"Bundle": "first_bundle_type", "Start": "first_bundle_start"})
        .set_index(Q3_USER_COLUMN)
    )
    first_bundle["trial_end_date"] = first_bundle["first_bundle_start"] + pd.Timedelta(days=FREE_TRIAL_DAYS)

    seller_base = pd.DataFrame(index=pd.Index(dataframe[Q3_USER_COLUMN].unique(), name=Q3_USER_COLUMN))
    sellers = seller_base.join(first_bundle, how="left")
    current_bundle = q3_current_bundle_at(dataframe, sellers.index, reference_date)

    sellers["customer_type"] = sellers["Customer type"].fillna(
        dataframe.drop_duplicates(Q3_USER_COLUMN).set_index(Q3_USER_COLUMN)["Customer type"]
    )
    sellers["current_status"] = np.where(current_bundle.notna(), "Active", "Inactive")
    sellers["current_bundle_type"] = current_bundle.fillna("Inactive")
    sellers["active_trial_flag"] = (
        sellers["current_bundle_type"].isin(Q3_BUNDLE_PRICES)
        & (reference_date < sellers["trial_end_date"])
    )
    sellers["active_paid_flag"] = (
        sellers["current_bundle_type"].isin(Q3_BUNDLE_PRICES)
        & (reference_date >= sellers["trial_end_date"])
    )
    return sellers.drop(columns=["Customer type"])


def q3_seller_snapshot(sellers):
    """Summarize seller-level trial and paid status as of the reference date."""
    return pd.DataFrame(
        {
            "Metric": [
                "Bundle starters",
                "Currently active trial sellers",
                "Currently active paid Basic sellers",
                "Currently active paid Plus sellers",
                "Currently inactive after bundle start",
            ],
            "Sellers": [
                sellers["first_bundle_start"].notna().sum(),
                sellers["active_trial_flag"].sum(),
                ((sellers["active_paid_flag"]) & (sellers["current_bundle_type"].eq("Basic"))).sum(),
                ((sellers["active_paid_flag"]) & (sellers["current_bundle_type"].eq("Plus"))).sum(),
                ((sellers["first_bundle_start"].notna()) & (sellers["current_status"].eq("Inactive"))).sum(),
            ],
        }
    )


def q3_weekly_metrics(dataframe, sellers, launch_start, reference_date):
    """Calculate weekly registration, trial, paid-base, and Plus-share metrics."""
    first_bundle_starts = (
        sellers.dropna(subset=["first_bundle_start"])
        .reset_index()
        .rename(
            columns={
                "first_bundle_start": "Start",
                "first_bundle_type": "Bundle",
            }
        )
    )
    registrations = (
        first_bundle_starts.assign(week=q3_week_start(first_bundle_starts["Start"]))
        .pivot_table(index="week", columns="Bundle", values=Q3_USER_COLUMN, aggfunc="nunique", fill_value=0)
        .reindex(columns=["Basic", "Plus"], fill_value=0)
    )
    registrations["New bundle registrations"] = registrations.sum(axis=1)

    weeks = pd.date_range(launch_start.to_period("W-SUN").start_time, reference_date, freq="W-MON")
    rows = []
    for week in weeks:
        snapshot_date = min(week + pd.Timedelta(days=6), reference_date)
        current_bundle = q3_current_bundle_at(dataframe, sellers.index, snapshot_date)
        paid_mask = snapshot_date >= sellers["trial_end_date"]
        trial_mask = snapshot_date < sellers["trial_end_date"]
        active_bundle_mask = current_bundle.isin(Q3_BUNDLE_PRICES)
        trial_basic = (active_bundle_mask & trial_mask & current_bundle.eq("Basic")).sum()
        trial_plus = (active_bundle_mask & trial_mask & current_bundle.eq("Plus")).sum()
        paid_basic = (active_bundle_mask & paid_mask & current_bundle.eq("Basic")).sum()
        paid_plus = (active_bundle_mask & paid_mask & current_bundle.eq("Plus")).sum()
        total_paid = paid_basic + paid_plus
        rows.append(
            {
                "week": week,
                "snapshot_date": snapshot_date,
                "Active trial Basic sellers": int(trial_basic),
                "Active trial Plus sellers": int(trial_plus),
                "Active trial sellers": int((active_bundle_mask & trial_mask).sum()),
                "Active paid Basic sellers": int(paid_basic),
                "Active paid Plus sellers": int(paid_plus),
                "Total active paid sellers": int(total_paid),
                "Plus share of active paid sellers": paid_plus / total_paid if total_paid else np.nan,
            }
        )

    weekly = pd.DataFrame(rows).set_index("week")
    weekly = weekly.join(registrations, how="left").fillna(
        {"Basic": 0, "Plus": 0, "New bundle registrations": 0}
    )
    weekly = weekly.rename(
        columns={
            "Basic": "Weekly new Basic registrations",
            "Plus": "Weekly new Plus registrations",
        }
    )
    count_columns = [
        "Weekly new Basic registrations",
        "Weekly new Plus registrations",
        "New bundle registrations",
    ]
    weekly[count_columns] = weekly[count_columns].astype(int)
    return weekly


def q3_modeled_bill_dates(row, sellers, reference_date):
    """Return modeled 4-week billing dates for one bundle interval."""
    if row["Bundle"] not in Q3_BUNDLE_PRICES:
        return []

    interval_end = reference_date if row["is_open_ended"] else min(row["End"], reference_date)
    first_start = sellers.loc[row[Q3_USER_COLUMN], "first_bundle_start"]
    first_paid_date = (
        row["Start"] + pd.Timedelta(days=FREE_TRIAL_DAYS)
        if row["Start"] == first_start
        else row["Start"]
    )
    if first_paid_date > interval_end:
        return []
    return list(pd.date_range(first_paid_date, interval_end, freq=f"{FREE_TRIAL_DAYS}D"))


def q3_modeled_revenue_events(dataframe, sellers, reference_date):
    """Create modeled paid revenue events from bundle intervals and list prices."""
    events = []
    for _, row in dataframe.loc[dataframe["is_bundle"]].iterrows():
        for bill_date in q3_modeled_bill_dates(row, sellers, reference_date):
            events.append(
                {
                    Q3_USER_COLUMN: row[Q3_USER_COLUMN],
                    "Bundle": row["Bundle"],
                    "bill_date": bill_date,
                    "modeled_paid_revenue_eur": Q3_BUNDLE_PRICES[row["Bundle"]],
                }
            )
    return pd.DataFrame(events)


def q3_revenue_by_4_week_period(revenue_events, launch_start):
    """Aggregate modeled paid revenue into 28-day launch periods."""
    if revenue_events.empty:
        return pd.DataFrame(columns=["period_start", "modeled_paid_revenue_eur", "paid_billing_events"])

    revenue = q3_add_revenue_period(revenue_events, launch_start)
    return (
        revenue.groupby("period_start")
        .agg(
            modeled_paid_revenue_eur=("modeled_paid_revenue_eur", "sum"),
            paid_billing_events=(Q3_USER_COLUMN, "count"),
        )
        .reset_index()
    )


def q3_add_revenue_period(revenue_events, launch_start):
    """Add 28-day launch-period fields to modeled revenue events."""
    revenue = revenue_events.copy()
    revenue["period_number"] = ((revenue["bill_date"] - launch_start).dt.days // FREE_TRIAL_DAYS).astype(int)
    revenue["period_start"] = launch_start + pd.to_timedelta(
        revenue["period_number"] * FREE_TRIAL_DAYS,
        unit="D",
    )
    return revenue


def q3_revenue_by_4_week_period_and_bundle(revenue_events, launch_start):
    """Aggregate modeled paid revenue by 28-day period and bundle type."""
    if revenue_events.empty:
        return pd.DataFrame(
            columns=["period_start", "Bundle", "modeled_paid_revenue_eur", "paid_billing_events"]
        )

    revenue = q3_add_revenue_period(revenue_events, launch_start)
    return (
        revenue.groupby(["period_start", "Bundle"], as_index=False)
        .agg(
            modeled_paid_revenue_eur=("modeled_paid_revenue_eur", "sum"),
            paid_billing_events=(Q3_USER_COLUMN, "count"),
        )
    )


def q3_complete_revenue_periods(revenue_4w, reference_date):
    """Return only modeled revenue periods fully observable by the reference date."""
    if revenue_4w.empty:
        return revenue_4w.copy()

    revenue = revenue_4w.copy()
    period_end = revenue["period_start"] + pd.Timedelta(days=FREE_TRIAL_DAYS - 1)
    return revenue.loc[period_end <= reference_date].copy()


def q3_registrations_by_4_week_period(sellers, launch_start):
    """Aggregate first-ever bundle registrations into 28-day launch periods."""
    starters = sellers.dropna(subset=["first_bundle_start"]).copy()
    if starters.empty:
        return pd.DataFrame(columns=["period_start", "new_bundle_registrations"])

    period_number = ((starters["first_bundle_start"] - launch_start).dt.days // FREE_TRIAL_DAYS).astype(int)
    starters["period_start"] = launch_start + pd.to_timedelta(period_number * FREE_TRIAL_DAYS, unit="D")
    return (
        starters.groupby("period_start")
        .size()
        .rename("new_bundle_registrations")
        .reset_index()
    )


def q3_complete_registration_periods(registrations_4w, reference_date):
    """Return registration periods fully observable by the reference date."""
    if registrations_4w.empty:
        return registrations_4w.copy()

    registrations = registrations_4w.copy()
    period_end = registrations["period_start"] + pd.Timedelta(days=FREE_TRIAL_DAYS - 1)
    return registrations.loc[period_end <= reference_date].copy()


def q3_complete_bundle_revenue_periods(revenue_by_bundle, reference_date):
    """Return bundle-level modeled revenue periods fully observable by the reference date."""
    if revenue_by_bundle.empty:
        return revenue_by_bundle.copy()

    revenue = revenue_by_bundle.copy()
    period_end = revenue["period_start"] + pd.Timedelta(days=FREE_TRIAL_DAYS - 1)
    return revenue.loc[period_end <= reference_date].copy()


def q3_revenue_display_table(revenue_4w, periods=8):
    """Return a compact formatted modeled-revenue table for notebook display."""
    return format_display_table(
        revenue_4w.tail(periods),
        euro_columns=["modeled_paid_revenue_eur"],
        integer_columns=["paid_billing_events"],
    )


def q3_trials_reaching_day_28_soon(sellers, reference_date, days_ahead=14):
    """List active trial sellers expected to reach day 28 soon."""
    cutoff_date = reference_date + pd.Timedelta(days=days_ahead)
    trial_sellers = sellers[
        sellers["active_trial_flag"]
        & sellers["trial_end_date"].between(reference_date, cutoff_date, inclusive="right")
    ].copy()
    trial_sellers["days_to_day_28"] = (trial_sellers["trial_end_date"] - reference_date).dt.days
    return (
        trial_sellers.reset_index()[
            [
                Q3_USER_COLUMN,
                "customer_type",
                "first_bundle_type",
                "first_bundle_start",
                "trial_end_date",
                "days_to_day_28",
            ]
        ]
        .sort_values(["trial_end_date", Q3_USER_COLUMN])
        .reset_index(drop=True)
    )


def q3_sales_kpis(weekly_metrics, revenue_4w, reference_date, registrations_4w=None):
    """Return latest Sales Overview KPIs for compact dashboard display."""
    latest_week = weekly_metrics.iloc[-1]
    previous_week = weekly_metrics.iloc[-2] if len(weekly_metrics) > 1 else None
    complete_revenue = q3_complete_revenue_periods(revenue_4w, reference_date)
    latest_complete_revenue = (
        0 if complete_revenue.empty else complete_revenue.iloc[-1]["modeled_paid_revenue_eur"]
    )
    previous_complete_revenue = (
        np.nan if len(complete_revenue) < 2 else complete_revenue.iloc[-2]["modeled_paid_revenue_eur"]
    )
    complete_registrations = (
        pd.DataFrame()
        if registrations_4w is None
        else q3_complete_registration_periods(registrations_4w, reference_date)
    )
    latest_complete_registrations = (
        np.nan if complete_registrations.empty else complete_registrations.iloc[-1]["new_bundle_registrations"]
    )
    previous_complete_registrations = (
        np.nan
        if len(complete_registrations) < 2
        else complete_registrations.iloc[-2]["new_bundle_registrations"]
    )

    def change_text(current, previous, suffix):
        if previous is None or pd.isna(current) or pd.isna(previous):
            return f"(n/a {suffix})"
        if previous == 0:
            return f"(+0% {suffix})" if current == 0 else f"(n/a {suffix})"
        return f"({(current / previous - 1):+.0%} {suffix})"

    def point_change_text(current, previous, suffix):
        if previous is None or pd.isna(current) or pd.isna(previous):
            return f"(n/a {suffix})"
        return f"({(current - previous) * 100:+.1f}pp {suffix})"

    latest_paid = latest_week["Total active paid sellers"]
    previous_paid = None if previous_week is None else previous_week["Total active paid sellers"]
    latest_trial = latest_week["Active trial sellers"]
    previous_trial = None if previous_week is None else previous_week["Active trial sellers"]
    latest_plus_share = latest_week["Plus share of active paid sellers"]
    previous_plus_share = None if previous_week is None else previous_week["Plus share of active paid sellers"]

    return pd.DataFrame(
        {
            "KPI": [
                "Reference date",
                "Active paid sellers",
                "Active trial sellers",
                "New registrations in latest complete 4wk period",
                "Plus share of active paid sellers",
                "Modeled revenue in latest complete 4wk period",
            ],
            "Value": [
                f"{reference_date:%Y-%m-%d}",
                f"{int(latest_paid):,} {change_text(latest_paid, previous_paid, 'w/w')}",
                f"{int(latest_trial):,} {change_text(latest_trial, previous_trial, 'w/w')}",
                (
                    ""
                    if pd.isna(latest_complete_registrations)
                    else f"{int(latest_complete_registrations):,} "
                    f"{change_text(latest_complete_registrations, previous_complete_registrations, 'vs prev 4wk')}"
                ),
                f"{pct(latest_plus_share)} {point_change_text(latest_plus_share, previous_plus_share, 'w/w')}",
                f"{eur(latest_complete_revenue)} "
                f"{change_text(latest_complete_revenue, previous_complete_revenue, 'vs prev 4wk')}",
            ],
        }
    )


def q3_active_paid_on(dataframe, sellers, user_ids, checkpoint):
    """Return whether sellers are active in a paid bundle at a checkpoint."""
    current_bundle = q3_current_bundle_at(dataframe, user_ids, checkpoint)
    trial_ended = checkpoint >= sellers.loc[user_ids, "trial_end_date"]
    return current_bundle.isin(Q3_BUNDLE_PRICES) & trial_ended


def q3_active_paid_at_checkpoints(dataframe, sellers, checkpoints):
    """Return whether sellers are active paid at seller-specific checkpoint dates."""
    current_bundle = q3_current_bundle_at_checkpoints(dataframe, checkpoints)
    trial_ended = checkpoints >= sellers.loc[checkpoints.index, "trial_end_date"]
    return current_bundle.isin(Q3_BUNDLE_PRICES) & trial_ended


def q3_cohort_base(sellers, launch_start, cohort_window_days=FREE_TRIAL_DAYS):
    """Assign first-bundle sellers to fixed-width first-start cohorts."""
    cohorts = sellers.dropna(subset=["first_bundle_start"]).copy()
    cohorts["cohort_number"] = (
        (cohorts["first_bundle_start"] - launch_start).dt.days // cohort_window_days
    ).astype(int)
    cohorts["cohort_start"] = launch_start + pd.to_timedelta(
        cohorts["cohort_number"] * cohort_window_days,
        unit="D",
    )
    cohorts["cohort_end"] = cohorts["cohort_start"] + pd.Timedelta(days=cohort_window_days - 1)
    cohorts["cohort_window_days"] = cohort_window_days
    return cohorts


def q3_maturity_rate_column(day):
    """Return the active-paid rate column name for a maturity checkpoint."""
    return f"maturity_day_{day}_active_paid_rate"


def q3_maturity_seller_column(day):
    """Return the active-paid seller-count column name for a maturity checkpoint."""
    return f"maturity_day_{day}_active_paid_sellers"


def q3_maturity_week_label(day):
    """Return a compact week label for a maturity checkpoint."""
    return f"{day // 7}wk"


def q3_maturity_rate_columns(maturity_days=Q3_COHORT_MATURITY_DAYS):
    """Return active-paid rate columns for maturity checkpoints."""
    return [q3_maturity_rate_column(day) for day in maturity_days]


def q3_cohort_metrics(
    dataframe,
    sellers,
    launch_start,
    reference_date,
    cohort_window_days=FREE_TRIAL_DAYS,
    maturity_days=Q3_COHORT_MATURITY_DAYS,
):
    """Calculate paid cohort metrics across aggregation windows and maturity checkpoints."""
    cohorts = q3_cohort_base(sellers, launch_start, cohort_window_days=cohort_window_days)
    rows = []
    for cohort_start, group in cohorts.groupby("cohort_start"):
        row = {
            "cohort_start": cohort_start,
            "cohort_end": group["cohort_end"].iloc[0],
            "cohort_window_days": cohort_window_days,
            "trial_starters": len(group),
        }
        for day in maturity_days:
            seller_checkpoints = group["first_bundle_start"] + pd.Timedelta(days=day)
            rate_column = q3_maturity_rate_column(day)
            seller_column = q3_maturity_seller_column(day)
            if (reference_date >= seller_checkpoints).all():
                active_values = q3_active_paid_at_checkpoints(dataframe, sellers, seller_checkpoints)
                row[rate_column] = active_values.mean()
                row[seller_column] = int(active_values.sum())
            else:
                row[rate_column] = np.nan
                row[seller_column] = np.nan
        rows.append(row)
    return pd.DataFrame(rows).sort_values("cohort_start")


def q3_format_rate_table(dataframe, date_columns=None, rate_columns=None, integer_columns=None):
    """Format date, rate, and count columns while keeping immature metrics blank."""
    display = dataframe.copy()
    date_columns = date_columns or []
    rate_columns = rate_columns or []
    integer_columns = integer_columns or []

    for column in existing_columns(display, date_columns):
        display[column] = display[column].dt.strftime("%Y-%m-%d")
    for column in existing_columns(display, rate_columns):
        display[column] = display[column].map(lambda value: "" if pd.isna(value) else f"{value:.1%}")
    for column in existing_columns(display, integer_columns):
            display[column] = display[column].map(lambda value: "" if pd.isna(value) else f"{int(value):,}")
    return display


def q3_markdown_table(dataframe):
    """Return a compact Markdown table for text-only dashboard tables."""
    display = dataframe.copy()
    headers = [str(column) for column in display.columns]
    rows = []
    for _, row in display.iterrows():
        rows.append(
            [
                "" if pd.isna(value) else str(value).replace("|", "\\|").replace("\n", " ")
                for value in row
            ]
        )

    header_row = "| " + " | ".join(headers) + " |"
    separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_rows = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_row, separator_row] + body_rows)


def q3_cohort_display_table(cohort_metrics):
    """Return a presentation-ready cohort table with rates only for maturity points."""
    rate_columns = q3_maturity_rate_columns()
    display = q3_format_rate_table(
        cohort_metrics,
        date_columns=["cohort_start", "cohort_end"],
        rate_columns=rate_columns,
        integer_columns=["cohort_window_days", "trial_starters"],
    )
    display["cohort_window_days"] = display["cohort_window_days"].map(
        lambda value: "" if pd.isna(value) or value == "" else f"{int(str(value).replace(',', ''))}d"
    )
    return display[
        [
            "cohort_start",
            "cohort_end",
            "cohort_window_days",
            "trial_starters",
        ]
        + rate_columns
    ].rename(
        columns={
            "cohort_start": "Cohort start",
            "cohort_end": "Cohort end",
            "cohort_window_days": "Agg Window",
            "trial_starters": "Trial starters",
            **{
                q3_maturity_rate_column(day): f"Week {day // 7} active paid rate"
                for day in Q3_COHORT_MATURITY_DAYS
            },
        }
    )


def q3_cohort_heatmap_table(cohort_metrics):
    """Return a styled cohort table with heat-map coloring on active paid rates."""
    rate_columns = [
        ("Active paid rate by maturity period", q3_maturity_week_label(day))
        for day in Q3_COHORT_MATURITY_DAYS
    ]
    table = cohort_metrics[
        [
            "cohort_start",
            "cohort_end",
            "cohort_window_days",
            "trial_starters",
        ]
        + q3_maturity_rate_columns()
    ].rename(
        columns={
            "cohort_start": ("", "Cohort start"),
            "cohort_end": ("", "Cohort end"),
            "cohort_window_days": ("", "Agg Window"),
            "trial_starters": ("", "Trial starters"),
            **{
                q3_maturity_rate_column(day): label
                for day, label in zip(Q3_COHORT_MATURITY_DAYS, rate_columns)
            },
        }
    )
    table.columns = pd.MultiIndex.from_tuples(table.columns)
    formatters = {
        ("", "Cohort start"): lambda value: value.strftime("%Y-%m-%d"),
        ("", "Cohort end"): lambda value: value.strftime("%Y-%m-%d"),
        ("", "Agg Window"): lambda value: "" if pd.isna(value) else f"{int(value)}d",
        ("", "Trial starters"): "{:,.0f}",
        **{column: "{:.1%}" for column in rate_columns},
    }
    heatmap_values = table[rate_columns].to_numpy(dtype=float)
    heatmap_min = np.nanmin(heatmap_values)
    heatmap_max = np.nanmax(heatmap_values)
    return (
        table.style.format(formatters, na_rep="")
        .background_gradient(
            cmap=Q3_HEATMAP_CMAP,
            subset=rate_columns,
            vmin=heatmap_min,
            vmax=heatmap_max,
        )
        .set_properties(subset=rate_columns, **{"color": PLOT_COLORS["text"]})
    )


def q3_segment_metrics_for_series(dataframe, sellers, reference_date, segment_name, segment_values):
    """Create segment diagnostics for one seller-level segmentation."""
    cohorts = sellers.dropna(subset=["first_bundle_start"]).copy()
    cohorts["segment_value"] = segment_values.reindex(cohorts.index).fillna("Unknown")
    rows = []

    for segment_value, group in cohorts.groupby("segment_value", dropna=False):
        users = group.index
        checkpoints_28 = group["first_bundle_start"] + pd.Timedelta(days=FREE_TRIAL_DAYS)
        mature_28 = checkpoints_28 <= reference_date
        if mature_28.any():
            converted = q3_active_paid_at_checkpoints(dataframe, sellers, checkpoints_28.loc[mature_28])
            day_28_conversion = converted.mean()
        else:
            day_28_conversion = np.nan

        current_bundle = sellers.loc[users, "current_bundle_type"]
        active_paid = sellers.loc[users, "active_paid_flag"]
        active_paid_sellers = int(active_paid.sum())
        active_paid_plus = int((active_paid & current_bundle.eq("Plus")).sum())
        current_no_bundle = int(current_bundle.eq("No bundle").sum())

        rows.append(
            {
                "Segment": segment_name,
                "Segment value": segment_value,
                "Registrations": len(group),
                "Day-28 paid conversion": day_28_conversion,
                "Plus share of active paid sellers": (
                    active_paid_plus / active_paid_sellers if active_paid_sellers else np.nan
                ),
                "Active paid sellers": active_paid_sellers,
                "Current no-bundle share": current_no_bundle / len(group) if len(group) else np.nan,
            }
        )

    return pd.DataFrame(rows)


def q3_segment_metrics(dataframe, sellers, launch_start, reference_date):
    """Create compact segment diagnostics using fields currently available in Q3."""
    del launch_start
    segment_frames = [
        q3_segment_metrics_for_series(
            dataframe,
            sellers,
            reference_date,
            "Customer type",
            sellers["customer_type"],
        ),
        q3_segment_metrics_for_series(
            dataframe,
            sellers,
            reference_date,
            "First bundle type",
            sellers["first_bundle_type"].map(lambda value: f"{value}-first" if pd.notna(value) else value),
        ),
        q3_segment_metrics_for_series(
            dataframe,
            sellers,
            reference_date,
            "Current bundle status",
            sellers["current_bundle_type"],
        ),
    ]
    return (
        pd.concat(segment_frames, ignore_index=True)
        .sort_values(["Segment", "Registrations"], ascending=[True, False])
        .reset_index(drop=True)
    )


def q3_segment_display_table(segment_metrics):
    """Return a formatted segment diagnosis table for notebook display."""
    return q3_format_rate_table(
        segment_metrics,
        rate_columns=[
            "Day-28 paid conversion",
            "Plus share of active paid sellers",
            "Current no-bundle share",
        ],
        integer_columns=["Registrations", "Active paid sellers"],
    )


def q3_segment_merge_audit(sellers, q2_data_path=Q2_CSV_PATH):
    """Show which high-value segment enrichments are available or blocked."""
    q3_ids = set(sellers.index)
    q2 = read_q2_data(q2_data_path)
    q2_ids = set(q2[Q2_USER_COLUMN].dropna().unique())
    overlap = len(q3_ids & q2_ids)
    q2_coverage = overlap / len(q3_ids) if q3_ids else np.nan

    return pd.DataFrame(
        [
            {
                "Source": "Q3 registrations",
                "Potential segment": "Customer type: SYI / Pro",
                "Useful fields": "`Customer type`",
                "Status": "Available now",
                "Note": "Use for Pro vs SYI adoption, conversion, Plus share, and no-bundle status.",
            },
            {
                "Source": "Q3 registrations",
                "Potential segment": "Bundle journey",
                "Useful fields": "`First bundle type`, `Current bundle type`, start/end dates",
                "Status": "Available now",
                "Note": "Use for Basic-first vs Plus-first and current Basic / Plus / No bundle cuts.",
            },
            {
                "Source": "Q2 outreach data",
                "Potential segment": "Outreach readiness score",
                "Useful fields": "`outreach_readiness_score`, recent paid usage, active months, total fees",
                "Status": f"Blocked: {overlap:,} overlapping seller IDs ({q2_coverage:.0%} coverage)",
                "Note": "Needs consistent seller IDs between Q2 and Q3 before joining.",
            },
            {
                "Source": "Q2 outreach data",
                "Potential segment": "SMB activity proxy",
                "Useful fields": "listing volume, category breadth, paid product breadth, paid visibility, total fees",
                "Status": f"Blocked: {overlap:,} overlapping seller IDs ({q2_coverage:.0%} coverage)",
                "Note": "Could approximate Q1 SMB likelihood, but should be labelled as a proxy.",
            },
            {
                "Source": "Q1 User Related Info",
                "Potential segment": "Business setup strength",
                "Useful fields": "corporate bank account flag, reviews, registration age, seller description/photo",
                "Status": "Needs user-level table",
                "Note": "Best source for true SMB likelihood beyond behavior.",
            },
            {
                "Source": "Q1 Ad Related Info",
                "Potential segment": "Seller size and listing quality",
                "Useful fields": "active ads, category, photos, phone shown, external URL, insertion fees",
                "Status": "Needs ad-level table",
                "Note": "Would support seller-size and category segment cuts.",
            },
            {
                "Source": "Q1 Pro Info",
                "Potential segment": "Pro performance tier",
                "Useful fields": "CPC, daily impressions, daily clicks, URL clicks",
                "Status": "Needs Pro ad table",
                "Note": "Useful for separating high-intent Pro sellers from light Pro users.",
            },
            {
                "Source": "Q1 Pro Invoicing Info",
                "Potential segment": "Historical spend tier",
                "Useful fields": "invoice month, total costs, discount, total invoice amount, paid date",
                "Status": "Needs invoicing table",
                "Note": "Best added cut for revenue quality and cannibalization risk.",
            },
            {
                "Source": "Q1 Messaging / Traffic Info",
                "Potential segment": "Seller outcome tier",
                "Useful fields": "messages, leads, ad views, bids, phone clicks, web clicks",
                "Status": "Needs engagement tables",
                "Note": "Required to show whether bundle adoption improves seller outcomes.",
            },
        ]
    )


def q3_segment_enrichment_opportunities():
    """Describe theoretical high-value segment merges for the Q3 dashboard."""
    return pd.DataFrame(
        [
            {
                "Potential merge": "SMB likelihood score",
                "Why it helps": "Separates likely business sellers from lighter consumer-like sellers.",
            },
            {
                "Potential merge": "Outreach readiness score",
                "Why it helps": "Shows whether sales-prioritized sellers convert and retain better.",
            },
            {
                "Potential merge": "Historical spend tier",
                "Why it helps": "Distinguishes high-value sellers from low-spend adopters.",
            },
            {
                "Potential merge": "Seller size / activity tier",
                "Why it helps": "Identifies whether bundles work better for large or small sellers.",
            },
            {
                "Potential merge": "Pro performance tier",
                "Why it helps": "Separates Pro sellers with real traffic from Pro sellers with low engagement.",
            },
            {
                "Potential merge": "Seller outcome tier",
                "Why it helps": "Shows whether bundles create value for sellers, not only platform revenue.",
            },
            {
                "Potential merge": "Outreach batch / channel",
                "Why it helps": "Connects launch execution to registration and paid conversion quality.",
            },
        ]
    )


def q3_segment_mockup_descriptions():
    """Describe high-value segmentation visuals that require merged data."""
    return pd.DataFrame(
        [
            {
                "Mock visualization": "Recent change alerts",
                "Potential merged data": "Daily or weekly segment snapshots joined to registration history",
                "What it would show": "Sharp 4-week changes in active paid sellers, no-bundle share, or Plus share.",
            },
        ]
    )


def q3_dummy_segment_enrichment_data():
    """Return small synthetic datasets for segmentation mockups."""
    return {
        "change_alerts": pd.DataFrame(
            {
                "Segment": [
                    "High readiness",
                    "Medium readiness",
                    "Low readiness",
                    "Large sellers",
                    "Low spend",
                    "Pro performance low",
                ],
                "4wk active paid change": [9, 3, -5, 7, -8, -11],
            }
        ),
    }


def add_q3_dummy_data_label(ax):
    """Add a consistent dummy-data label to a mock chart."""
    ax.text(
        0.01,
        0.98,
        "Dummy Data",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        fontweight="bold",
        color=PLOT_COLORS["text"],
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": PLOT_COLORS["background"],
            "edgecolor": PLOT_COLORS["grid"],
            "alpha": 0.9,
        },
    )
    return ax


def plot_q3_mock_smb_fit_seller_size(dummy_data=None):
    """Plot dummy recent segment change alerts."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    data = dummy_data or q3_dummy_segment_enrichment_data()
    alerts = data["change_alerts"].sort_values("4wk active paid change")
    _, ax = plt.subplots(figsize=(8, 4))
    colors = [
        PLOT_COLORS["danger"] if value < 0 else PLOT_COLORS["q3"]
        for value in alerts["4wk active paid change"]
    ]
    ax.barh(alerts["Segment"], alerts["4wk active paid change"], color=colors)
    ax.axvline(0, color=PLOT_COLORS["grid"], linewidth=1)
    ax.set_title("Recent Segment Change Alerts")
    ax.set_xlabel("4-week active paid change (pp)")
    ax.set_ylabel("")
    for y_position, value in enumerate(alerts["4wk active paid change"]):
        label_x = value - 0.45 if value >= 0 else value + 0.45
        ax.text(
            label_x,
            y_position,
            f"{value:+.0f}pp",
            va="center",
            ha="right" if value >= 0 else "left",
            color=PLOT_COLORS["text"],
            fontweight="bold",
        )
    ax.tick_params(axis="x", bottom=False, labelbottom=False)
    ax.tick_params(axis="y", length=0)
    ax.spines["bottom"].set_visible(False)
    ax.margins(x=0.05)
    add_q3_dummy_data_label(ax)
    return ax


def plot_q3_segment_enrichment_mockups(dummy_data=None):
    """Plot retained dummy segmentation mockups as separate figures."""
    return [
        plot_q3_mock_smb_fit_seller_size(dummy_data),
    ]


def format_q3_month_axis_for_weekly_bars(ax, weekly_index, month_step=1):
    """Label weekly bar charts at month starts to keep the date axis readable."""
    tick_positions = []
    tick_labels = []
    previous_month = None
    previous_year = None
    month_counter = 0

    for position, week in enumerate(pd.DatetimeIndex(weekly_index)):
        month_key = (week.year, week.month)
        if month_key == previous_month:
            continue
        month_counter += 1
        if (month_counter - 1) % month_step != 0 and week.year == previous_year:
            previous_month = month_key
            continue

        label = week.strftime("%b")
        if previous_year != week.year:
            label = f"{label}\n{week.year}"

        tick_positions.append(position)
        tick_labels.append(label)
        previous_month = month_key
        previous_year = week.year

    ax.set_xticks(tick_positions)
    ax.set_xticklabels(tick_labels, rotation=0, ha="center")
    return ax


def plot_q3_weekly_new_registrations(weekly_metrics):
    """Plot first-ever weekly registrations overall and by bundle type."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(11, 7),
        sharex=True,
        constrained_layout=True,
    )

    weekly_metrics["New bundle registrations"].plot(
        ax=axes[0],
        color=PLOT_COLORS["q3"],
        linewidth=2,
    )
    axes[0].set_title("Weekly New First-Ever Bundle Registrations")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Sellers")
    format_number_axis(axes[0], "y")

    weekly_metrics[["Weekly new Basic registrations", "Weekly new Plus registrations"]].plot(
        ax=axes[1],
        color=[PLOT_COLORS["neutral"], PLOT_COLORS["q3"]],
        linewidth=2,
    )
    axes[1].set_title("Weekly New First-Ever Bundle Registrations - by Bundle")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Sellers")
    format_number_axis(axes[1], "y")
    return fig, axes


def plot_q3_active_paid_sellers(weekly_metrics):
    """Plot active paid sellers over time, split by current bundle."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    ax = weekly_metrics[["Active paid Basic sellers", "Active paid Plus sellers"]].plot(
        figsize=(11, 4),
        color=[PLOT_COLORS["neutral"], PLOT_COLORS["q3"]],
        linewidth=2,
    )
    ax.set_title("Active Paid Sellers")
    ax.set_xlabel("")
    ax.set_ylabel("Sellers")
    format_number_axis(ax, "y")
    return ax


def plot_q3_active_bundle_sellers(weekly_metrics):
    """Plot active bundle sellers overall and by bundle type."""
    if plt is None or Line2D is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    fig, axes = plt.subplots(
        2,
        1,
        figsize=(11, 7),
        sharex=True,
        constrained_layout=True,
    )

    overall = pd.DataFrame(
        {
            "Subscription": weekly_metrics["Total active paid sellers"],
            "Trial": weekly_metrics["Active trial sellers"],
        },
        index=weekly_metrics.index,
    )
    overall.plot(
        ax=axes[0],
        color=[PLOT_COLORS["q3"], PLOT_COLORS["q3"]],
        linewidth=2,
        legend=False,
    )
    for line, linestyle in zip(axes[0].lines, ["-", "--"]):
        line.set_linestyle(linestyle)
    axes[0].legend(
        handles=[
            Line2D([0], [0], color=PLOT_COLORS["q3"], lw=2, linestyle="-", label="Subscription"),
            Line2D([0], [0], color=PLOT_COLORS["q3"], lw=2, linestyle="--", label="Trial"),
        ]
    )
    axes[0].set_title("Active Bundle Sellers")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("Sellers")
    format_number_axis(axes[0], "y")

    plot_columns = [
        "Active paid Basic sellers",
        "Active paid Plus sellers",
        "Active trial Basic sellers",
        "Active trial Plus sellers",
    ]
    weekly_metrics[plot_columns].plot(
        ax=axes[1],
        color=[
            PLOT_COLORS["neutral"],
            PLOT_COLORS["q3"],
            PLOT_COLORS["neutral"],
            PLOT_COLORS["q3"],
        ],
        linewidth=2,
        legend=False,
    )
    for line, linestyle in zip(axes[1].lines, ["-", "-", "--", "--"]):
        line.set_linestyle(linestyle)
    legend_handles = [
        Line2D([0], [0], color=PLOT_COLORS["neutral"], lw=2, linestyle="-", label="Paid Basic"),
        Line2D([0], [0], color=PLOT_COLORS["q3"], lw=2, linestyle="-", label="Paid Plus"),
        Line2D([0], [0], color=PLOT_COLORS["neutral"], lw=2, linestyle="--", label="Trial Basic"),
        Line2D([0], [0], color=PLOT_COLORS["q3"], lw=2, linestyle="--", label="Trial Plus"),
    ]
    axes[1].legend(handles=legend_handles)
    axes[1].set_title("Active Bundle Sellers - by Bundle")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("Sellers")
    format_number_axis(axes[1], "y")
    return fig, axes


def plot_q3_active_trial_sellers(weekly_metrics):
    """Plot active trial sellers as the near-term paid pipeline."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    ax = weekly_metrics["Active trial sellers"].plot(
        figsize=(11, 3.5),
        color=PLOT_COLORS["q3"],
        linewidth=2,
    )
    ax.set_title("Active Trial Sellers")
    ax.set_xlabel("")
    ax.set_ylabel("Sellers")
    format_number_axis(ax, "y")
    return ax


def plot_q3_plus_share(weekly_metrics):
    """Plot Plus share of active paid sellers over time."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    plus_share = weekly_metrics["Plus share of active paid sellers"].mul(100)
    ax = plus_share.plot(
        figsize=(7, 3.5),
        color=PLOT_COLORS["q3"],
        linewidth=2,
    )
    latest_date = plus_share.index[-1]
    latest_value = plus_share.iloc[-1]
    ax.scatter(
        [latest_date],
        [latest_value],
        color=PLOT_COLORS["q3"],
        s=36,
        zorder=3,
    )
    ax.annotate(
        f"{latest_value:.1f}%",
        xy=(latest_date, latest_value),
        xytext=(-10, 12),
        textcoords="offset points",
        ha="right",
        va="bottom",
        color=PLOT_COLORS["text"],
        fontweight="bold",
    )
    ax.set_title("Plus Share of Active Paid Sellers")
    ax.set_xlabel("")
    ax.set_ylabel("Share (%)")
    ax.set_ylim(0, 100)
    format_percent_axis(ax, "y")
    ax.margins(x=0.04)
    return ax


def plot_q3_sales_overview(weekly_metrics):
    """Plot the core weekly Q3 launch-monitoring views."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    fig, axes = plt.subplots(2, 2, figsize=(14, 8), constrained_layout=True)

    weekly_metrics[["Weekly new Basic registrations", "Weekly new Plus registrations"]].plot(
        kind="line",
        ax=axes[0, 0],
        color=[PLOT_COLORS["neutral"], PLOT_COLORS["q3"]],
        linewidth=2,
    )
    axes[0, 0].set_title("Weekly New First-Ever Bundle Registrations")
    axes[0, 0].set_xlabel("")
    axes[0, 0].set_ylabel("Sellers")
    format_number_axis(axes[0, 0], "y")

    weekly_metrics[["Active trial sellers", "Active paid Basic sellers", "Active paid Plus sellers"]].plot(
        ax=axes[0, 1],
        color=[PLOT_COLORS["neutral"], PLOT_COLORS["q3"], PLOT_COLORS["q3"]],
        linewidth=2,
    )
    if len(axes[0, 1].lines) > 2:
        axes[0, 1].lines[2].set_linestyle("--")
    axes[0, 1].set_title("Active Trial and Paid Sellers")
    axes[0, 1].set_xlabel("")
    axes[0, 1].set_ylabel("Sellers")
    format_number_axis(axes[0, 1], "y")

    weekly_metrics["Plus share of active paid sellers"].mul(100).plot(
        ax=axes[1, 0],
        color=PLOT_COLORS["q3"],
        linewidth=2,
    )
    axes[1, 0].set_title("Plus Share of Active Paid Sellers")
    axes[1, 0].set_xlabel("")
    axes[1, 0].set_ylabel("Share (%)")
    axes[1, 0].set_ylim(0, 100)
    format_percent_axis(axes[1, 0], "y")

    weekly_metrics["Total active paid sellers"].plot(
        ax=axes[1, 1],
        color=PLOT_COLORS["q3"],
        linewidth=2,
    )
    axes[1, 1].set_title("Total Active Paid Sellers")
    axes[1, 1].set_xlabel("")
    axes[1, 1].set_ylabel("Sellers")
    format_number_axis(axes[1, 1], "y")
    return fig, axes


def plot_q3_modeled_revenue(revenue_4w, reference_date=None):
    """Plot modeled paid revenue by 4-week launch period, marking incomplete periods."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    revenue_plot = revenue_4w.sort_values("period_start").reset_index(drop=True).copy()
    revenue_plot["period_label"] = revenue_plot["period_start"].dt.strftime("%b %d")
    x_values = np.arange(len(revenue_plot))
    y_values = revenue_plot["modeled_paid_revenue_eur"].to_numpy()

    _, ax = plt.subplots(figsize=(12, 4))
    if reference_date is None:
        ax.plot(
            x_values,
            y_values,
            color=PLOT_COLORS["q3"],
            marker="o",
            linewidth=2,
        )
        last_complete_index = len(revenue_plot) - 1
    else:
        period_end = revenue_plot["period_start"] + pd.Timedelta(days=FREE_TRIAL_DAYS - 1)
        incomplete_period = period_end > reference_date
        first_incomplete = np.flatnonzero(incomplete_period.to_numpy())

        if len(first_incomplete) == 0:
            last_complete_index = len(revenue_plot) - 1
            ax.plot(
                x_values,
                y_values,
                color=PLOT_COLORS["q3"],
                marker="o",
                linewidth=2,
            )
        else:
            incomplete_start = first_incomplete[0]
            last_complete_index = incomplete_start - 1
            solid_end = max(incomplete_start, 1)
            ax.plot(
                x_values[:solid_end],
                y_values[:solid_end],
                color=PLOT_COLORS["q3"],
                marker="o",
                linewidth=2,
            )
            dashed_start = max(incomplete_start - 1, 0)
            ax.plot(
                x_values[dashed_start:],
                y_values[dashed_start:],
                color=PLOT_COLORS["q3"],
                marker="o",
                linewidth=2,
                linestyle="--",
            )

            label_index = first_incomplete[-1]
            ax.annotate(
                "Incomplete data",
                xy=(x_values[label_index], y_values[label_index]),
                xytext=(0, -28),
                textcoords="offset points",
                color=PLOT_COLORS["neutral"],
                ha="center",
                va="top",
            )
            ax.margins(y=0.16)
    if last_complete_index >= 0:
        complete_value = y_values[last_complete_index]
        ax.annotate(
            f"€{complete_value / 1000:.1f}k",
            xy=(x_values[last_complete_index], complete_value),
            xytext=(-8, 12),
            textcoords="offset points",
            color=PLOT_COLORS["text"],
            ha="right",
            va="bottom",
            fontweight="bold",
        )
    ax.set_title("Modeled Paid Revenue by 4-Week Period")
    ax.set_xlabel("4-week period start")
    ax.set_ylabel("Modeled revenue (€)")
    format_eur_axis(ax, "y")
    ax.set_xticks(x_values)
    ax.set_xticklabels(revenue_plot["period_label"])
    ax.tick_params(axis="x", rotation=45)
    return ax


def plot_q3_latest_revenue_by_bundle(revenue_by_bundle, reference_date=None):
    """Plot latest complete-period modeled paid revenue split by Basic and Plus."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")
    revenue_plot = (
        revenue_by_bundle
        if reference_date is None
        else q3_complete_bundle_revenue_periods(revenue_by_bundle, reference_date)
    )
    if revenue_plot.empty:
        raise ValueError("revenue_by_bundle must contain at least one period")

    latest_period = revenue_plot["period_start"].max()
    latest = (
        revenue_plot[revenue_plot["period_start"].eq(latest_period)]
        .set_index("Bundle")
        .reindex(["Basic", "Plus"])
        .fillna({"modeled_paid_revenue_eur": 0, "paid_billing_events": 0})
    )
    ax = latest["modeled_paid_revenue_eur"].plot(
        kind="bar",
        figsize=(5.5, 3.5),
        color=[PLOT_COLORS["neutral"], PLOT_COLORS["q3"]],
        legend=False,
    )
    total_revenue = latest["modeled_paid_revenue_eur"].sum()
    max_revenue = latest["modeled_paid_revenue_eur"].max()
    for position, value in enumerate(latest["modeled_paid_revenue_eur"]):
        share = value / total_revenue if total_revenue else np.nan
        ax.text(
            position,
            value + max_revenue * 0.04,
            f"€{value / 1000:.1f}k\n{share:.1%}",
            ha="center",
            va="bottom",
            color=PLOT_COLORS["text"],
            fontweight="bold",
        )
    ax.set_title(f"Latest Complete Modeled Revenue Split ({latest_period:%Y-%m-%d})")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="x", rotation=0, length=0)
    ax.tick_params(axis="y", left=False, labelleft=False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.margins(y=0.18)
    return ax


def plot_q3_cohort_metrics(cohort_metrics):
    """Plot active-paid rates for mature cohorts."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    plot_data = cohort_metrics.set_index("cohort_start")[q3_maturity_rate_columns()].mul(100)
    plot_data = plot_data.rename(
        columns={
            q3_maturity_rate_column(day): q3_maturity_week_label(day)
            for day in Q3_COHORT_MATURITY_DAYS
        }
    )
    ax = plot_data.plot(
        figsize=(12, 4),
        marker="o",
        linewidth=2,
        color=[
            PLOT_COLORS["q3"],
            PLOT_COLORS["q1"],
            PLOT_COLORS["q2"],
            PLOT_COLORS["q4"],
            PLOT_COLORS["neutral"],
            PLOT_COLORS["warning"],
        ],
    )
    ax.set_title("28-Day Cohort Customer Quality")
    ax.set_xlabel("First-bundle cohort start")
    ax.set_ylabel("Active paid rate (%)")
    ax.set_ylim(0, 100)
    return ax


def q3_business_impact_placeholder_table():
    """Return high-value dashboard modules that require additional datasets."""
    return pd.DataFrame(
        [
            {
                "Module": "Revenue impact",
                "Business question": "Is bundle revenue incremental?",
                "Placeholder visual": "Revenue waterfall: new bundle revenue, lost feature/CPC revenue, net impact",
            },
            {
                "Module": "Seller value",
                "Business question": "Do sellers get better outcomes?",
                "Placeholder visual": "Indexed before/after line for leads per active ad",
            },
            {
                "Module": "Sales steering",
                "Business question": "Where should launch effort focus?",
                "Placeholder visual": "Compact segment table by category, seller size, spend tier, and outreach batch",
            },
        ]
    )


def q3_dummy_business_impact_data():
    """Return small synthetic datasets for Business Impact visual mockups."""
    return {
        "revenue_waterfall": pd.DataFrame(
            {
                "Component": [
                    "Bundle revenue",
                    "Lost feature revenue",
                    "Lost CPC revenue",
                    "Refunds / credits",
                    "Net impact",
                ],
                "Value": [120_000, -28_000, -12_000, -5_000, 75_000],
            }
        ),
    }


def plot_q3_mock_revenue_impact_waterfall(dummy_data=None):
    """Plot a dummy revenue impact waterfall for business-impact analysis."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting helpers")

    data = dummy_data or q3_dummy_business_impact_data()
    waterfall = data["revenue_waterfall"].copy()
    waterfall["Component"] = pd.Categorical(
        waterfall["Component"],
        categories=waterfall["Component"],
        ordered=True,
    )
    waterfall = waterfall.iloc[::-1]
    colors = [
        PLOT_COLORS["q3"] if value >= 0 else PLOT_COLORS["danger"]
        for value in waterfall["Value"]
    ]
    _, ax = plt.subplots(figsize=(7, 4))
    ax.barh(waterfall["Component"], waterfall["Value"], color=colors)
    ax.axvline(0, color=PLOT_COLORS["grid"], linewidth=1)
    ax.set_title("Modeled Net Revenue Impact per 4-Week Period")
    ax.set_xlabel("Revenue impact (€)")
    ax.set_ylabel("")
    format_eur_axis(ax, "x")
    for y_position, value in enumerate(waterfall["Value"]):
        label = f"{value / 1000:+.0f}k"
        label = label.replace("+", "+€").replace("-", "-€")
        ax.text(
            value + (2_500 if value >= 0 else -2_500),
            y_position,
            label,
            va="center",
            ha="left" if value >= 0 else "right",
            color=PLOT_COLORS["text"],
            fontweight="bold",
        )
    ax.margins(x=0.18)
    add_q3_dummy_data_label(ax)
    return ax


def plot_q3_business_impact_mockups(dummy_data=None):
    """Plot business-impact mockups as separate figures."""
    return [
        plot_q3_mock_revenue_impact_waterfall(dummy_data),
    ]

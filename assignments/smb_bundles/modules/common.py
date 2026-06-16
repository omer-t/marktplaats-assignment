"""Shared constants and formatting utilities for the SMB bundle analysis."""

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


ASSIGNMENT_DIR = Path(__file__).resolve().parents[1]
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


def format_percentage(value):
    """Format a share as a readable percentage."""
    if pd.isna(value):
        return pd.NA
    return f"{value:.1%}"


def pct(value):
    """Short alias for percentage formatting."""
    return format_percentage(value)


def format_euros(value):
    """Format a numeric value as whole euros."""
    if pd.isna(value):
        return pd.NA
    return f"€{value:,.0f}"


def format_euros_k(value):
    """Format a numeric euro value in thousands for compact chart labels."""
    if pd.isna(value):
        return pd.NA
    return f"€{value / 1_000:,.1f}k"


def eur(value):
    """Short alias for euro formatting."""
    return format_euros(value)


def format_display_table(dataframe, euro_columns=None, decimal_columns=None, integer_columns=None):
    """Return a copy with selected columns formatted for notebook display."""
    display = dataframe.copy()
    euro_columns = euro_columns or []
    decimal_columns = decimal_columns or []
    integer_columns = integer_columns or []

    for column in existing_columns(display, euro_columns):
        display[column] = display[column].map(lambda value: format_euros(value))
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
        raise ModuleNotFoundError("matplotlib is required for plotting")

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
    return f"{category_name}\n({translation})"


def format_number_axis(ax, axis="x"):
    """Use thousands separators on a numeric chart axis."""
    if FuncFormatter is None:
        raise ModuleNotFoundError("matplotlib is required for plotting")

    formatter = FuncFormatter(lambda value, _: f"{value:,.0f}")
    if axis in ("x", "both"):
        ax.xaxis.set_major_formatter(formatter)
    if axis in ("y", "both"):
        ax.yaxis.set_major_formatter(formatter)
    return ax


def format_number_k_axis(ax, axis="x"):
    """Format a numeric chart axis in thousands."""
    if FuncFormatter is None:
        raise ModuleNotFoundError("matplotlib is required for plotting")

    formatter = FuncFormatter(lambda value, _: f"{value / 1_000:,.0f}k")
    if axis in ("x", "both"):
        ax.xaxis.set_major_formatter(formatter)
    if axis in ("y", "both"):
        ax.yaxis.set_major_formatter(formatter)
    return ax


def format_eur_axis(ax, axis="x"):
    """Format a numeric chart axis as whole euros."""
    if FuncFormatter is None:
        raise ModuleNotFoundError("matplotlib is required for plotting")

    formatter = FuncFormatter(lambda value, _: f"€{value:,.0f}")
    if axis in ("x", "both"):
        ax.xaxis.set_major_formatter(formatter)
    if axis in ("y", "both"):
        ax.yaxis.set_major_formatter(formatter)
    return ax


def format_eur_k_axis(ax, axis="x"):
    """Format a numeric chart axis as euros in thousands."""
    if FuncFormatter is None:
        raise ModuleNotFoundError("matplotlib is required for plotting")

    formatter = FuncFormatter(lambda value, _: f"€{value / 1_000:,.0f}k")
    if axis in ("x", "both"):
        ax.xaxis.set_major_formatter(formatter)
    if axis in ("y", "both"):
        ax.yaxis.set_major_formatter(formatter)
    return ax


def format_percent_axis(ax, axis="y"):
    """Format a 0-100 axis as whole percentages."""
    if FuncFormatter is None:
        raise ModuleNotFoundError("matplotlib is required for plotting")

    formatter = FuncFormatter(lambda value, _: f"{value:.0f}%")
    if axis in ("x", "both"):
        ax.xaxis.set_major_formatter(formatter)
    if axis in ("y", "both"):
        ax.yaxis.set_major_formatter(formatter)
    return ax


def add_horizontal_bar_text_labels(ax, labels, padding=4, x_values=None):
    """Add custom text labels to the right of horizontal bars."""
    x_values = x_values if x_values is not None else [patch.get_width() for patch in ax.patches]
    for patch, label, x_value in zip(ax.patches, labels, x_values):
        width = x_value
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

Q3_EXPECTED_COLUMNS = ["User ID", "Customer type", "Bundle", "Start", "End"]
Q3_BUNDLE_PRICES = {"Basic": 19.99, "Plus": 49.99}

# Shared Q3 utilities used across EDA, modeling, and charts.

def q3_current_bundle_at(dataframe, user_ids, as_of_date):
    """Return each seller's active interval bundle at one snapshot date."""
    active = dataframe[
        (dataframe[Q3_USER_COLUMN].isin(user_ids))
        & (dataframe["Start"] <= as_of_date)
        & (dataframe["is_open_ended"] | (dataframe["End"] > as_of_date))
    ].copy()
    current = active.sort_values([Q3_USER_COLUMN, "Start", "End"]).groupby(Q3_USER_COLUMN).tail(1)
    return current.set_index(Q3_USER_COLUMN)["Bundle"].reindex(user_ids)


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


def add_q3_chart_note(ax, text, y=0.98):
    """Add a compact note for the active chart view."""
    ax.text(
        0.01,
        y,
        text,
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

"""Synthetic examples for optional Q3 concept charts."""

import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "marketplaats-matplotlib"))

import pandas as pd

try:
    import matplotlib.pyplot as plt
except ModuleNotFoundError:
    plt = None

from functions import PLOT_COLORS, format_percent_axis


def _q3_segment_example_data():
    """Return small synthetic datasets for segmentation concept charts."""
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


def _add_q3_synthetic_data_label(ax):
    """Label a chart that uses synthetic example data."""
    ax.text(
        0.01,
        0.98,
        "Synthetic Example",
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


def _plot_q3_synthetic_smb_fit_seller_size(example_data=None):
    """Plot synthetic recent segment change alerts."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting")

    data = example_data or _q3_segment_example_data()
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
    ax.spines["left"].set_visible(False)
    ax.margins(x=0.05)
    _add_q3_synthetic_data_label(ax)
    add_q3_chart_note(ax, "Metric: Active paid bundle rate", y=0.88)
    return ax


def plot_q3_segment_change_alerts(example_data=None):
    """Plot synthetic recent segment change alerts."""
    return _plot_q3_synthetic_smb_fit_seller_size(example_data)


def _q3_business_impact_example_data():
    """Return small synthetic datasets for business impact concept charts."""
    return {
        "seller_leads_uplift": pd.DataFrame(
            {
                "Week from bundle start": [-8, -4, 0, 4, 8, 12] * 2,
                "Bundle": ["Basic"] * 6 + ["Plus"] * 6,
                "Avg leads per seller": [8.0, 8.1, 8.0, 9.1, 9.4, 9.5, 8.4, 8.5, 8.4, 10.8, 11.2, 11.4],
            }
        ),
    }


def _plot_q3_synthetic_seller_leads_uplift(example_data=None):
    """Plot synthetic seller lead uplift versus pre-bundle baseline by bundle."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting")

    data = example_data or _q3_business_impact_example_data()
    leads = data["seller_leads_uplift"].copy()
    _, ax = plt.subplots(figsize=(7, 4))
    for bundle, color in [("Basic", PLOT_COLORS["neutral"]), ("Plus", PLOT_COLORS["q3"])]:
        bundle_data = leads.loc[leads["Bundle"].eq(bundle)].sort_values("Week from bundle start")
        baseline = bundle_data.loc[bundle_data["Week from bundle start"] < 0, "Avg leads per seller"].mean()
        bundle_data = bundle_data.assign(
            lead_uplift=(bundle_data["Avg leads per seller"] / baseline - 1) * 100
        )
        ax.plot(
            bundle_data["Week from bundle start"],
            bundle_data["lead_uplift"],
            color=color,
            marker="o",
            linewidth=2,
            label=bundle,
        )
    ax.axvline(0, color=PLOT_COLORS["grid"], linewidth=1)
    ax.axhline(0, color=PLOT_COLORS["grid"], linewidth=1)
    ax.set_title("Avg Seller Leads Uplift vs Pre-Bundle Baseline")
    ax.set_xlabel("Weeks from bundle start")
    ax.set_ylabel("Lead uplift (%)")
    format_percent_axis(ax, "y")
    week_ticks = sorted(leads["Week from bundle start"].unique())
    ax.set_xticks(week_ticks)
    ax.set_xticklabels([f"{week:+.0f}".replace("+", "") for week in week_ticks])
    for bundle, color in [("Basic", PLOT_COLORS["neutral"]), ("Plus", PLOT_COLORS["q3"])]:
        bundle_data = leads.loc[leads["Bundle"].eq(bundle)].sort_values("Week from bundle start")
        baseline = bundle_data.loc[bundle_data["Week from bundle start"] < 0, "Avg leads per seller"].mean()
        bundle_data = bundle_data.assign(
            lead_uplift=(bundle_data["Avg leads per seller"] / baseline - 1) * 100
        )
        latest = bundle_data.iloc[-1]
        ax.annotate(
            f"+{latest['lead_uplift']:.0f}%",
            xy=(latest["Week from bundle start"], latest["lead_uplift"]),
            xytext=(0, 10),
            textcoords="offset points",
            ha="center",
            va="bottom",
            color=PLOT_COLORS["text"],
            fontweight="bold",
        )
    ax.legend(title="")
    ax.margins(x=0.08, y=0.18)
    _add_q3_synthetic_data_label(ax)
    add_q3_chart_note(ax, "Breakdown: Bundle type", y=0.88)
    return ax


def plot_q3_seller_leads_uplift(example_data=None):
    """Plot synthetic seller lead uplift versus pre-bundle baseline by bundle."""
    return _plot_q3_synthetic_seller_leads_uplift(example_data)

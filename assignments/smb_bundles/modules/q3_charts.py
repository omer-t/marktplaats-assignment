"""SMB Q3 sales and revenue charts."""
from common import *
from q3_model import *


def plot_q3_weekly_new_registrations(weekly_metrics):
    """Plot first bundle weekly registrations by bundle type."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting")

    ax = weekly_metrics[["Weekly new Basic registrations", "Weekly new Plus registrations"]].plot(
        figsize=(11, 4),
        color=[PLOT_COLORS["neutral"], PLOT_COLORS["q3"]],
        linewidth=2,
    )
    ax.set_title("Weekly New First Bundle Registrations")
    ax.set_xlabel("")
    ax.set_ylabel("Sellers")
    format_number_axis(ax, "y")
    add_q3_chart_note(ax, "Breakdown: Bundle type")
    return ax

def plot_q3_active_bundle_sellers(weekly_metrics):
    """Plot active bundle sellers by bundle type and paid/trial status."""
    if plt is None or Line2D is None:
        raise ModuleNotFoundError("matplotlib is required for plotting")

    plot_columns = [
        "Active paid Basic sellers",
        "Active paid Plus sellers",
        "Active trial Basic sellers",
        "Active trial Plus sellers",
    ]
    weekly_metrics[plot_columns].plot(
        figsize=(11, 4),
        color=[
            PLOT_COLORS["neutral"],
            PLOT_COLORS["q3"],
            PLOT_COLORS["neutral"],
            PLOT_COLORS["q3"],
        ],
        linewidth=2,
        legend=False,
    )
    ax = plt.gca()
    for line, linestyle in zip(ax.lines, ["-", "-", "--", "--"]):
        line.set_linestyle(linestyle)
    legend_handles = [
        Line2D([0], [0], color=PLOT_COLORS["neutral"], lw=2, linestyle="-", label="Paid Basic bundles"),
        Line2D([0], [0], color=PLOT_COLORS["q3"], lw=2, linestyle="-", label="Paid Plus bundles"),
        Line2D([0], [0], color=PLOT_COLORS["neutral"], lw=2, linestyle="--", label="Trial Basic bundles"),
        Line2D([0], [0], color=PLOT_COLORS["q3"], lw=2, linestyle="--", label="Trial Plus bundles"),
    ]
    ax.legend(handles=legend_handles, loc="upper right")
    add_q3_chart_note(ax, "Breakdown: Bundle type")
    ax.set_title("Active Bundles")
    ax.set_xlabel("")
    ax.set_ylabel("Bundles")
    format_number_axis(ax, "y")
    return ax

def plot_q3_plus_share(weekly_metrics):
    """Plot Plus share of active paid bundles over time."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting")

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
    ax.set_title("Plus Share of Active Paid Bundles")
    ax.set_xlabel("")
    ax.set_ylabel("Share (%)")
    ax.set_ylim(0, 100)
    format_percent_axis(ax, "y")
    ax.margins(x=0.04)
    add_q3_chart_note(ax, "Breakdown: All sellers")
    return ax

def plot_q3_modeled_revenue(revenue_4w, reference_date=None):
    """Plot modeled paid revenue by 4-week launch period, marking incomplete periods."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting")

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
                xytext=(0, -18),
                textcoords="offset points",
                color=PLOT_COLORS["neutral"],
                ha="center",
                va="top",
                annotation_clip=False,
            )
            y_max = max(y_values.max(), 1)
            ax.set_ylim(bottom=0, top=y_max * 1.16)
    if last_complete_index >= 0:
        complete_value = y_values[last_complete_index]
        ax.annotate(
            f"€{complete_value / 1000:.1f}k",
            xy=(x_values[last_complete_index], complete_value),
            xytext=(0, 12),
            textcoords="offset points",
            color=PLOT_COLORS["text"],
            ha="center",
            va="bottom",
            fontweight="bold",
        )
    ax.set_title("Modeled Paid Revenue by 4-Week Period")
    ax.set_xlabel("4-week period start")
    ax.set_ylabel("Modeled revenue (€)")
    format_eur_axis(ax, "y")
    add_q3_chart_note(ax, "Breakdown: All sellers")
    if ax.get_ylim()[0] < 0:
        ax.set_ylim(bottom=0)
    ax.set_xticks(x_values)
    ax.set_xticklabels(revenue_plot["period_label"])
    ax.tick_params(axis="x", rotation=45)
    return ax

def plot_q3_latest_revenue_by_bundle(revenue_by_bundle, reference_date=None):
    """Plot latest complete-period modeled paid revenue split by Basic and Plus."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting")
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
        kind="barh",
        figsize=(5.5, 3.5),
        color=[PLOT_COLORS["neutral"], PLOT_COLORS["q3"]],
        legend=False,
    )
    total_revenue = latest["modeled_paid_revenue_eur"].sum()
    max_revenue = latest["modeled_paid_revenue_eur"].max()
    for position, value in enumerate(latest["modeled_paid_revenue_eur"]):
        share = value / total_revenue if total_revenue else np.nan
        ax.text(
            value + max_revenue * 0.03,
            position,
            f"€{value / 1000:.1f}k ({share:.1%})",
            ha="left",
            va="center",
            color=PLOT_COLORS["text"],
            fontweight="bold",
        )
    ax.set_title("Latest Complete 4wk Modeled Revenue Split")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="x", bottom=False, labelbottom=False)
    ax.tick_params(axis="y", length=0)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.margins(x=0.22)
    return ax

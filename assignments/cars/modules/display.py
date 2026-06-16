"""Cars table formatting and charts."""
from common import *
from data import *
from analysis import *

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

def plot_duplicated_ad_id_sensitivity(dataframe):
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

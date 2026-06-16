"""SMB Q3 loading, validation, exploratory summaries, and EDA charts."""
from common import *

def load_q3_bundle_data(data_path=Q3_CSV_PATH):
    """Load and normalize Q3 registration intervals for dashboard modeling."""
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
    """Return launch start and latest observable dashboard reference date."""
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
        raise ModuleNotFoundError("matplotlib is required for plotting")

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
        raise ModuleNotFoundError("matplotlib is required for plotting")

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
    ax.tick_params(axis="x", rotation=0, length=0)
    ax.legend(title="")
    return ax

def plot_q3_eda_current_status(sellers):
    """Plot current seller status after first bundle start."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting")

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
        raise ModuleNotFoundError("matplotlib is required for plotting")

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
        raise ModuleNotFoundError("matplotlib is required for plotting")

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
    ax.tick_params(axis="x", rotation=0, length=0)
    ax.legend(title="")
    return ax

def plot_q3_eda_interval_complexity(dataframe):
    """Plot seller-level repeat bundle periods and switching complexity."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting")

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
        active_paid_bundles = int(paid.sum())
        rows.append(
            {
                "Customer type": customer_type,
                "Bundle starters": len(group),
                "Basic-first share": group["first_bundle_type"].eq("Basic").mean(),
                "Plus-first share": group["first_bundle_type"].eq("Plus").mean(),
                "Active paid bundles": active_paid_bundles,
                "Plus share of active paid bundles": (
                    (paid & current_bundle.eq("Plus")).sum() / active_paid_bundles
                    if active_paid_bundles
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
            "Plus share of active paid bundles",
            "Current no-bundle share",
            "Multiple bundle-period share",
            "Used Basic and Plus share",
        ],
        integer_columns=["Bundle starters", "Active paid bundles"],
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
                    f"Paid Plus share: Pro {pro['Plus share of active paid bundles']:.1%}; "
                    f"SYI {syi['Plus share of active paid bundles']:.1%}."
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
        raise ModuleNotFoundError("matplotlib is required for plotting")

    summary = q3_customer_type_eda_summary(dataframe, sellers).set_index("Customer type")
    plot_data = summary[
        [
            "Plus-first share",
            "Plus share of active paid bundles",
            "Current no-bundle share",
            "Used Basic and Plus share",
        ]
    ].reindex(["SYI", "Pro"]).mul(100)
    plot_data = plot_data.rename(
        columns={
            "Plus-first share": "Plus-first",
            "Plus share of active paid bundles": "Paid Plus share",
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
    ax.tick_params(axis="x", rotation=0, length=0)
    ax.legend(title="")
    return ax


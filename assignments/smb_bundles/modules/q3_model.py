"""SMB Q3 dashboard data model, revenue, cohort, and segment metrics."""
from common import *
from q3_eda import *

# Summary text for the EDA section.

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
        ("Latest active paid bundles", f"{int(latest_week['Total active paid sellers']):,}"),
        ("Latest active trial bundles", f"{int(latest_week['Active trial sellers']):,}"),
        ("Current no-bundle sellers", f"{current_no_bundle:,}"),
        ("Current Plus share of paid base", pct(latest_week["Plus share of active paid sellers"])),
        ("Sellers with multiple bundle periods", f"{int(multi_interval_sellers):,}"),
        ("Sellers using both Basic and Plus", f"{int(multi_bundle_sellers):,}"),
        ("Latest complete modeled revenue", eur(latest_complete_revenue)),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Value"])


# Main transformation entrypoint called from the Q3 notebook.

def q3_dashboard_data(data_path=Q3_CSV_PATH, cohort_window_days=FREE_TRIAL_DAYS):
    """Build all reusable Q3 dashboard inputs from registration intervals.

    Loads intervals, derives one seller row, builds weekly status, models paid
    revenue, and creates cohort and segment tables.
    """
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


# Seller-level model and weekly status snapshots.

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
    """Derive one seller row with first bundle, trial end, and current status.

    Converts interval-level rows to the seller grain used by weekly, cohort,
    revenue, and segment reporting.
    """
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


def _q3_first_bundle_registrations_by_week(sellers):
    """Return weekly first-bundle registrations split by bundle type."""
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
    return registrations


def _q3_weekly_status_snapshot(dataframe, sellers, week, reference_date):
    """Calculate trial, paid, and Plus-share status for one weekly snapshot."""
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
    return {
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


def q3_weekly_metrics(dataframe, sellers, launch_start, reference_date):
    """Calculate weekly registration, trial, paid-base, and Plus-share metrics."""
    registrations = _q3_first_bundle_registrations_by_week(sellers)
    weeks = pd.date_range(launch_start.to_period("W-SUN").start_time, reference_date, freq="W-MON")
    rows = [
        _q3_weekly_status_snapshot(dataframe, sellers, week, reference_date)
        for week in weeks
    ]

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
    """Return modeled 4-week billing dates for one paid bundle interval.

    Billing starts after the seller's free trial and stops at the interval end
    or the dashboard reference date, whichever comes first.
    """
    if row["Bundle"] not in Q3_BUNDLE_PRICES:
        return []

    interval_end = reference_date if row["is_open_ended"] else min(row["End"], reference_date)
    trial_end_date = sellers.loc[row[Q3_USER_COLUMN], "trial_end_date"]
    first_paid_date = max(row["Start"], trial_end_date)
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
    """Aggregate modeled paid revenue into consecutive 28-day launch periods."""
    if revenue_events.empty:
        return pd.DataFrame(
            {
                "period_start": [launch_start],
                "modeled_paid_revenue_eur": [0.0],
                "paid_billing_events": [0],
            }
        )

    revenue = q3_add_revenue_period(revenue_events, launch_start)
    aggregated = (
        revenue.groupby("period_start")
        .agg(
            modeled_paid_revenue_eur=("modeled_paid_revenue_eur", "sum"),
            paid_billing_events=(Q3_USER_COLUMN, "count"),
        )
    )
    all_periods = pd.date_range(
        launch_start,
        aggregated.index.max(),
        freq=f"{FREE_TRIAL_DAYS}D",
    )
    return (
        aggregated.reindex(all_periods, fill_value=0)
        .rename_axis("period_start")
        .reset_index()
        .assign(paid_billing_events=lambda frame: frame["paid_billing_events"].astype(int))
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
    """Aggregate first bundle registrations into 28-day launch periods."""
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

def q3_rolling_new_registrations(sellers, reference_date, days=FREE_TRIAL_DAYS):
    """Return first-bundle registrations in the latest rolling window and prior window."""
    starters = sellers.dropna(subset=["first_bundle_start"])
    registration_end = starters.loc[
        starters["first_bundle_start"] <= reference_date,
        "first_bundle_start",
    ].max()
    if pd.isna(registration_end):
        registration_end = reference_date
    current_start = registration_end - pd.Timedelta(days=days - 1)
    previous_start = registration_end - pd.Timedelta(days=(2 * days) - 1)
    previous_end = current_start - pd.Timedelta(days=1)
    current_count = starters["first_bundle_start"].between(
        current_start,
        registration_end,
        inclusive="both",
    ).sum()
    previous_count = starters["first_bundle_start"].between(
        previous_start,
        previous_end,
        inclusive="both",
    ).sum()
    return int(current_count), int(previous_count)


def _q3_change_text(current, previous, suffix):
    """Format percent change text for KPI cards."""
    if previous is None or pd.isna(current) or pd.isna(previous):
        return f"(n/a {suffix})"
    if previous == 0:
        return f"(+0% {suffix})" if current == 0 else f"(n/a {suffix})"
    return f"({(current / previous - 1):+.0%} {suffix})"


def _q3_point_change_text(current, previous, suffix):
    """Format percentage-point change text for KPI cards."""
    if previous is None or pd.isna(current) or pd.isna(previous):
        return f"(n/a {suffix})"
    return f"({(current - previous) * 100:+.1f}pp {suffix})"


def _q3_latest_and_previous_week(weekly_metrics):
    """Return latest and previous weekly metric rows."""
    latest_week = weekly_metrics.iloc[-1]
    previous_week = weekly_metrics.iloc[-2] if len(weekly_metrics) > 1 else None
    return latest_week, previous_week


def _q3_complete_revenue_comparison(revenue_4w, reference_date):
    """Return latest and previous complete-period modeled revenue."""
    complete_revenue = q3_complete_revenue_periods(revenue_4w, reference_date)
    latest_complete_revenue = (
        0 if complete_revenue.empty else complete_revenue.iloc[-1]["modeled_paid_revenue_eur"]
    )
    previous_complete_revenue = (
        np.nan if len(complete_revenue) < 2 else complete_revenue.iloc[-2]["modeled_paid_revenue_eur"]
    )
    return latest_complete_revenue, previous_complete_revenue


def _q3_registration_comparison(reference_date, registrations_4w=None, sellers=None):
    """Return latest and previous registration counts plus comparison label."""
    if sellers is not None:
        latest_registrations, previous_registrations = q3_rolling_new_registrations(sellers, reference_date)
        return latest_registrations, previous_registrations, "vs prior 4wk"

    complete_registrations = (
        pd.DataFrame()
        if registrations_4w is None
        else q3_complete_registration_periods(registrations_4w, reference_date)
    )
    latest_registrations = (
        np.nan if complete_registrations.empty else complete_registrations.iloc[-1]["new_bundle_registrations"]
    )
    previous_registrations = (
        np.nan
        if len(complete_registrations) < 2
        else complete_registrations.iloc[-2]["new_bundle_registrations"]
    )
    return latest_registrations, previous_registrations, "vs prev 4wk"


def q3_sales_kpis(weekly_metrics, revenue_4w, reference_date, registrations_4w=None, sellers=None):
    """Return latest Sales Overview KPIs as a single-row dashboard table."""
    latest_week, previous_week = _q3_latest_and_previous_week(weekly_metrics)
    latest_complete_revenue, previous_complete_revenue = _q3_complete_revenue_comparison(
        revenue_4w,
        reference_date,
    )
    latest_registrations, previous_registrations, registration_change_suffix = _q3_registration_comparison(
        reference_date,
        registrations_4w=registrations_4w,
        sellers=sellers,
    )
    latest_paid = latest_week["Total active paid sellers"]
    previous_paid = None if previous_week is None else previous_week["Total active paid sellers"]
    latest_trial = latest_week["Active trial sellers"]
    previous_trial = None if previous_week is None else previous_week["Active trial sellers"]
    latest_plus_share = latest_week["Plus share of active paid sellers"]
    previous_plus_share = None if previous_week is None else previous_week["Plus share of active paid sellers"]

    return pd.DataFrame(
        [
            {
                "Reference date": f"{reference_date:%Y-%m-%d}",
                "Active paid bundles": f"{int(latest_paid):,} {_q3_change_text(latest_paid, previous_paid, 'w/w')}",
                "Active trial bundles": f"{int(latest_trial):,} {_q3_change_text(latest_trial, previous_trial, 'w/w')}",
                "New registration in 4wk": (
                    ""
                    if pd.isna(latest_registrations)
                    else f"{int(latest_registrations):,} "
                    f"{_q3_change_text(latest_registrations, previous_registrations, registration_change_suffix)}"
                ),
                "Plus share of active paid bundles": (
                    f"{format_percentage(latest_plus_share)} {_q3_point_change_text(latest_plus_share, previous_plus_share, 'w/w')}"
                ),
                "Modeled revenue in latest complete 4wk period": (
                    f"{format_euros(latest_complete_revenue)} "
                    f"{_q3_change_text(latest_complete_revenue, previous_complete_revenue, 'vs prev 4wk')}"
                ),
            }
        ]
    )

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
    """Calculate active-paid cohort rates at fixed maturity checkpoints.

    Immature checkpoints are left blank (`NaN`) so the dashboard does not mix
    partial observation windows with mature cohort outcomes.
    """
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
        .hide(axis="index")
        .background_gradient(
            cmap=Q3_HEATMAP_CMAP,
            subset=rate_columns,
            vmin=heatmap_min,
            vmax=heatmap_max,
        )
        .set_properties(subset=rate_columns, **{"color": PLOT_COLORS["text"]})
    )

def q3_segment_metrics_for_series(dataframe, sellers, reference_date, segment_name, segment_values):
    """Create conversion, paid mix, and no-bundle diagnostics for one segment."""
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
        active_paid_bundles = int(active_paid.sum())
        active_paid_plus = int((active_paid & current_bundle.eq("Plus")).sum())
        current_no_bundle = int(current_bundle.eq("No bundle").sum())

        rows.append(
            {
                "Segment": segment_name,
                "Segment value": segment_value,
                "Registrations": len(group),
                "Day-28 paid conversion": day_28_conversion,
                "Plus share of active paid bundles": (
                    active_paid_plus / active_paid_bundles if active_paid_bundles else np.nan
                ),
                "Active paid bundles": active_paid_bundles,
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
    display_metrics = segment_metrics.loc[
        ~(
            segment_metrics["Segment"].eq("Current bundle status")
            & segment_metrics["Segment value"].eq("No bundle")
        )
    ].reset_index(drop=True)
    return q3_format_rate_table(
        display_metrics,
        rate_columns=[
            "Day-28 paid conversion",
            "Plus share of active paid bundles",
            "Current no-bundle share",
        ],
        integer_columns=["Registrations", "Active paid bundles"],
    )

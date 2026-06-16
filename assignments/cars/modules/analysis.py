"""Cars analytical summaries, quality checks, and experiment inference."""
from common import *
from data import *

# Data quality and assignment checks.

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

def group_size_summary(dataframe):
    """Count rows by assignment status and compute each row share."""
    assignment_status = dataframe["group"].where(dataframe["group"].isin(VALID_GROUPS), "Unassigned")
    summary = assignment_status.value_counts().rename_axis("group").reset_index(name="rows")
    group_order = pd.Categorical(summary["group"], categories=VALID_GROUPS + ["Unassigned"], ordered=True)
    summary = summary.assign(group_order=group_order).sort_values("group_order").drop(columns="group_order")
    summary["share"] = summary["rows"] / len(dataframe)
    return summary

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


# Primary A/B test result and sensitivity checks.

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

# Descriptive summaries for the Q3 insight notebook.

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

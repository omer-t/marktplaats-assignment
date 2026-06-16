"""SMB Q2 outreach readiness scoring and seller export."""
from common import *
from q2_analysis import *

Q2_WINDOW_FILL_COLUMNS = [
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
Q2_OUTREACH_SCORE_COLUMNS = [
    "recent_paid_usage_score",
    "paid_product_breadth_score",
    "consistency_score",
    "category_breadth_score",
    "growth_score",
    "fee_score",
]
Q2_BUNDLE_FIT_SCORE_COLUMNS = [
    "paid_visibility_score",
    "paid_product_breadth_score",
    "listing_volume_score",
]


# Shared scoring inputs and transformations.

def percentile_rank(series):
    """Rank a numeric signal as a 0-1 percentile."""
    return series.rank(pct=True, method="average")


def q2_window_summary(dataframe, prefix):
    """Aggregate seller activity for a named scoring window."""
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
    """Count distinct paid product types each seller has used at least once."""
    paid_product_columns = existing_columns(dataframe, ["N_PAID_AD_INSERTIONS"] + FEATURE_COUNT_COLUMNS)
    return (
        dataframe.assign(**{column: dataframe[column].gt(0) for column in paid_product_columns})
        .groupby(Q2_USER_COLUMN)[paid_product_columns]
        .max()
        .sum(axis=1)
        .rename("paid_product_breadth")
        .reset_index()
    )


# Private steps used by the public scoring function.

def _q2_scoring_windows(data):
    """Return date boundaries for recent and previous scoring windows."""
    last_month = data[Q2_DATE_COLUMN].max()
    recent_start = last_month - pd.DateOffset(months=5)
    previous_start = recent_start - pd.DateOffset(months=6)
    previous_end = recent_start - pd.DateOffset(days=1)
    return {
        "last_month": last_month,
        "recent_start": recent_start,
        "previous_start": previous_start,
        "previous_end": previous_end,
    }


def _q2_merge_scoring_inputs(data, seller_summary, windows):
    """Merge seller-level totals with recent, previous, and product breadth signals."""
    scored = (
        seller_summary.merge(
            q2_window_summary(
                data[data[Q2_DATE_COLUMN].between(windows["recent_start"], windows["last_month"])],
                "recent",
            ),
            on=Q2_USER_COLUMN,
            how="left",
        )
        .merge(
            q2_window_summary(
                data[data[Q2_DATE_COLUMN].between(windows["previous_start"], windows["previous_end"])],
                "previous",
            ),
            on=Q2_USER_COLUMN,
            how="left",
        )
        .merge(q2_paid_product_breadth(data), on=Q2_USER_COLUMN, how="left")
    )
    scored[Q2_WINDOW_FILL_COLUMNS] = scored[Q2_WINDOW_FILL_COLUMNS].fillna(0)
    return scored


def _q2_add_growth_signals(scored):
    """Add recent-vs-previous usage growth and recent usage share."""
    scored = scored.copy()
    scored["paid_usage_growth_ratio"] = (
        (scored["recent_paid_usage"] + 1) / (scored["previous_paid_usage"] + 1)
    )
    scored["commercial_growth_ratio"] = scored["paid_usage_growth_ratio"]
    scored["recent_paid_usage_share"] = (
        scored["recent_paid_usage"] / scored["paid_marketplace_actions"].clip(lower=1)
    )
    return scored


def _q2_add_outreach_scores(scored):
    """Add equal-weighted percentile scores used for outreach readiness."""
    scored = scored.copy()
    scored["recent_paid_usage_score"] = percentile_rank(scored["recent_paid_usage"])
    scored["paid_product_breadth_score"] = percentile_rank(scored["paid_product_breadth"])
    scored["consistency_score"] = percentile_rank(scored["active_months"])
    scored["category_breadth_score"] = percentile_rank(scored["categories"])
    scored["growth_score"] = percentile_rank(scored["paid_usage_growth_ratio"])
    scored["fee_score"] = percentile_rank(scored["total_fees"])
    scored["outreach_readiness_score"] = scored[Q2_OUTREACH_SCORE_COLUMNS].mean(axis=1)
    return scored


def _q2_add_selection_groups(scored, top_share):
    """Flag outreach-ready and fee-only comparison cohorts."""
    scored = scored.copy()
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
    return scored


def _q2_add_bundle_targeting(scored):
    """Add Basic/Plus targeting flags within the outreach-ready cohort."""
    scored = scored.copy()
    scored["paid_visibility_score"] = percentile_rank(scored["paid_visibility_uses"])
    scored["listing_volume_score"] = percentile_rank(scored["total_ad_insertions"])
    scored["bundle_fit_score"] = scored[Q2_BUNDLE_FIT_SCORE_COLUMNS].mean(axis=1)
    bundle_fit_cutoff = scored.loc[scored["is_outreach_ready_group"], "bundle_fit_score"].quantile(0.60)
    scored["is_targeted_for_plus"] = (
        scored["is_outreach_ready_group"] & scored["bundle_fit_score"].ge(bundle_fit_cutoff)
    )
    scored["bundle_target_group"] = np.select(
        [
            scored["is_targeted_for_plus"],
            scored["is_outreach_ready_group"],
        ],
        ["Targeted for Plus group", "Targeted for Basic group"],
        default="Not outreach ready",
    )
    return scored


# Main scoring entrypoint called from the Q2 notebook.

def q2_score_outreach_readiness(dataframe, seller_summary=None, top_share=0.25):
    """Score sellers for outreach using recency, breadth, consistency, growth, and fees.

    Percentile ranks allow signals with different units to be averaged without
    one raw scale dominating the selection.
    """
    data = add_q2_row_metrics(dataframe)

    if seller_summary is None:
        seller_summary = q2_seller_level_summary(data)

    windows = _q2_scoring_windows(data)
    scored = _q2_merge_scoring_inputs(data, seller_summary, windows)
    scored = _q2_add_growth_signals(scored)
    scored = _q2_add_outreach_scores(scored)
    scored = _q2_add_selection_groups(scored, top_share)
    scored = _q2_add_bundle_targeting(scored)

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
    """Return the seller-level scoring table used for preview and CSV export."""
    export = scored_sellers.copy()

    score_columns = [
        "recent_paid_usage_score",
        "consistency_score",
        "category_breadth_score",
        "growth_score",
        "fee_score",
        "paid_visibility_score",
        "paid_product_breadth_score",
        "listing_volume_score",
        "outreach_readiness_score",
        "bundle_fit_score",
    ]
    export[score_columns] = export[score_columns] * 100
    export = export.rename(
        columns={
            Q2_USER_COLUMN: "seller_id",
            "recent_paid_usage_score": "recent_paid_usage_percentile",
            "consistency_score": "consistency_percentile",
            "category_breadth_score": "category_breadth_percentile",
            "growth_score": "recent_growth_percentile",
            "fee_score": "total_fees_percentile",
            "paid_visibility_score": "paid_visibility_percentile",
            "paid_product_breadth_score": "paid_product_breadth_percentile",
            "listing_volume_score": "listing_volume_percentile",
            "is_targeted_for_plus": "is_targeted_for_plus_group",
        }
    )

    column_order = [
        "seller_id",
        "outreach_readiness_score",
        "bundle_fit_score",
        "recent_paid_usage_percentile",
        "consistency_percentile",
        "category_breadth_percentile",
        "recent_growth_percentile",
        "total_fees_percentile",
        "paid_visibility_percentile",
        "paid_product_breadth_percentile",
        "listing_volume_percentile",
        "is_outreach_ready_group",
        "is_targeted_for_plus_group",
    ]
    return export[column_order].round(2)

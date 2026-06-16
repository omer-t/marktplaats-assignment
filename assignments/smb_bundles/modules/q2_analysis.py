"""SMB Q2 data preparation, exploratory summaries, and Q2 charts."""
from common import *

def read_q2_data(data_path=Q2_CSV_PATH):
    """Read the Q2 outreach dataset and coerce dates/numeric metrics."""
    dataframe = pd.read_csv(data_path)
    dataframe[Q2_DATE_COLUMN] = pd.to_datetime(dataframe[Q2_DATE_COLUMN], errors="coerce")

    for column in existing_columns(dataframe, Q2_NUMERIC_COLUMNS):
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce").fillna(0)

    return dataframe

def add_q2_row_metrics(dataframe):
    """Add row-level commercial activity signals used by Q2 scoring.

    These definitions translate raw product columns into seller-level signals
    used later for prioritization.
    """
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

def q2_seller_level_summary(dataframe):
    """Aggregate seller-month-category rows to one row per seller.

    This is the base table for outreach prioritization: totals measure scale,
    active months measure consistency, and boolean flags preserve adoption.
    """
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

def q2_top_categories(dataframe, value_column="total_fees", top_n=10):
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

def apply_multisize_category_labels(ax, categories, dutch_size=9.5, english_size=8):
    """Draw category labels with smaller English translations under Dutch names."""
    labels = [readable_category_label(category).split("\n", 1) for category in categories]
    y_positions = ax.get_yticks()
    ax.set_yticklabels([])

    for y_position, label_parts in zip(y_positions, labels):
        dutch = label_parts[0]
        english = label_parts[1] if len(label_parts) > 1 else ""
        ax.annotate(
            dutch,
            xy=(0, y_position),
            xycoords=ax.get_yaxis_transform(),
            xytext=(-8, 4),
            textcoords="offset points",
            ha="right",
            va="center",
            fontsize=dutch_size,
            color=PLOT_COLORS["muted_text"],
            annotation_clip=False,
        )
        if english:
            ax.annotate(
                english,
                xy=(0, y_position),
                xycoords=ax.get_yaxis_transform(),
                xytext=(-8, -8),
                textcoords="offset points",
                ha="right",
                va="center",
                fontsize=english_size,
                color=PLOT_COLORS["muted_text"],
                annotation_clip=False,
            )
    return ax

def plot_q2_combined_anomaly_overview(monthly_summary, monthly_without_seller, anomaly_seller_id=65950787):
    """Combine active sellers with the anomaly comparison into one compact visual."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting")

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

    format_number_axis(axes[0], axis="y")
    format_number_k_axis(axes[1], axis="y")
    format_eur_k_axis(axes[2], axis="y")
    for ax in axes:
        ax.grid(axis="y", alpha=0.3)
    for ax in axes[1:]:
        ax.legend()

    fig.tight_layout()
    return fig, axes

def plot_q2_activity_mix_stacked_anomaly(dataframe, anomaly_seller_id=65950787):
    """Plot activity count mix with the anomaly seller stacked over all other sellers."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting")

    activity_columns = existing_columns(dataframe, ["N_FREE_AD_INSERTIONS", "N_PAID_AD_INSERTIONS"] + FEATURE_COUNT_COLUMNS)
    activity_mix = dataframe[activity_columns].sum().sort_values()
    anomaly_data = dataframe[dataframe[Q2_USER_COLUMN].eq(anomaly_seller_id)]
    anomaly_activity_mix = anomaly_data[activity_columns].sum().reindex(activity_mix.index).fillna(0)
    non_anomaly_activity_mix = activity_mix.to_numpy() - anomaly_activity_mix.to_numpy()
    labels = [readable_metric_label(column) for column in activity_mix.index]
    bar_labels = [f"{value / 1_000:,.1f}k" for value in activity_mix.values]

    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    ax.barh(labels, non_anomaly_activity_mix, color=PLOT_COLORS["q2"], label="All other sellers")
    ax.barh(
        labels,
        anomaly_activity_mix.to_numpy(),
        left=non_anomaly_activity_mix,
        color=PLOT_COLORS["neutral"],
        label=f"Seller {anomaly_seller_id}",
    )
    ax.set_title("Activity Count by Product Type")
    add_horizontal_bar_text_labels(ax, bar_labels, x_values=activity_mix.to_numpy())
    style_minimal_horizontal_bar(ax)
    ax.legend(loc="lower right")
    fig.tight_layout()
    return fig, ax

def plot_q2_fee_breakdown_stacked_anomaly(category_summary, dataframe, anomaly_seller_id=65950787):
    """Plot fee breakdown with the anomaly seller stacked over all other sellers."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting")

    data = add_q2_row_metrics(dataframe)
    anomaly_data = data[data[Q2_USER_COLUMN].eq(anomaly_seller_id)]
    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.2))

    top_category_fees = category_summary.head(10).sort_values("total_fees")
    y = np.arange(len(top_category_fees))
    category_total_fees = category_summary["total_fees"].sum()
    category_totals = top_category_fees["total_fees"]
    anomaly_category_fees = (
        anomaly_data.groupby(Q2_CATEGORY_COLUMN)["total_fees"]
        .sum()
        .reindex(top_category_fees[Q2_CATEGORY_COLUMN])
        .fillna(0)
    )
    non_anomaly_category_fees = category_totals.to_numpy() - anomaly_category_fees.to_numpy()
    category_bar_labels = [
        f"{format_euros_k(value)} ({value / category_total_fees:.1%})"
        for value in category_totals
    ]
    axes[0].barh(y, non_anomaly_category_fees, color=PLOT_COLORS["primary"], label="All other sellers")
    axes[0].barh(
        y,
        anomaly_category_fees.to_numpy(),
        left=non_anomaly_category_fees,
        color=PLOT_COLORS["neutral"],
        label=f"Seller {anomaly_seller_id}",
    )
    axes[0].set_yticks(y)
    apply_multisize_category_labels(axes[0], top_category_fees[Q2_CATEGORY_COLUMN])
    axes[0].set_title("Top Categories by Fees")
    add_horizontal_bar_text_labels(axes[0], category_bar_labels, x_values=category_totals)
    style_minimal_horizontal_bar(axes[0])

    fee_mix = dataframe[existing_columns(dataframe, FEE_COLUMNS)].sum().sort_values()
    anomaly_fee_mix = anomaly_data[existing_columns(anomaly_data, FEE_COLUMNS)].sum().reindex(fee_mix.index).fillna(0)
    non_anomaly_fee_mix = fee_mix.to_numpy() - anomaly_fee_mix.to_numpy()
    product_total_fees = fee_mix.sum()
    product_bar_labels = [f"{format_euros_k(value)} ({value / product_total_fees:.1%})" for value in fee_mix.values]
    fee_mix.index = [readable_metric_label(column) for column in fee_mix.index]
    axes[1].barh(fee_mix.index, non_anomaly_fee_mix, color=PLOT_COLORS["q2"], label="All other sellers")
    axes[1].barh(
        fee_mix.index,
        anomaly_fee_mix.to_numpy(),
        left=non_anomaly_fee_mix,
        color=PLOT_COLORS["neutral"],
        label=f"Seller {anomaly_seller_id}",
    )
    axes[1].set_title("Fee Mix by Paid Product")
    add_horizontal_bar_text_labels(axes[1], product_bar_labels, x_values=fee_mix.to_numpy())
    style_minimal_horizontal_bar(axes[1])
    axes[1].legend(loc="lower right")

    fig.tight_layout(w_pad=4)
    fig.subplots_adjust(left=0.25, right=0.98)
    return fig, axes

def plot_q2_fee_concentration(seller_summary):
    """Plot cumulative fee concentration by seller rank."""
    if plt is None:
        raise ModuleNotFoundError("matplotlib is required for plotting")

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

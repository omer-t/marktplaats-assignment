from pathlib import Path
from math import erf, erfc, sqrt
from numbers import Number

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_PATH = PROJECT_ROOT / "data" / "Adevinta Cars Dataset May 2019.csv"

MISSING_VALUE_MARKERS = ["?"]
VALID_GROUPS = ["A", "B"]
SIGNIFICANCE_LEVEL = 0.05
TWO_SIDED_Z_CRITICAL_95 = 1.96

METRIC_COLUMNS = ["telclicks", "bids", "n_asq", "webclicks"]
IMPORTANT_COLUMNS = [
    "src_ad_id",
    "telclicks",
    "bids",
    "carrosserie",
    "photo_cnt",
    "aantaldeuren",
    "n_asq",
    "bouwjaar",
    "emissie",
    "energielabel",
    "brand",
    "ad_start_dt",
    "vermogen",
    "webclicks",
    "model",
    "aantalstoelen",
    "price",
    "group",
]
NUMERIC_DIMENSION_COLUMNS = [
    "price",
    "kmstand",
    "days_live",
    "photo_cnt",
    "bouwjaar",
    "aantaldeuren",
    "aantalstoelen",
    "emissie",
    "vermogen",
]
CATEGORICAL_DIMENSION_COLUMNS = [
    "brand",
    "model",
    "kleur",
    "carrosserie",
    "energielabel",
]
UNDOCUMENTED_COLUMN_NOTES = {
    "kleur": "used as an optional car-color dimension",
    "kmstand": "used as an optional mileage dimension",
    "days_live": "used as an optional ad-tenure dimension",
    "l2": "not used; meaning is unclear",
}
NUMERIC_IMPORT_COLUMNS = sorted(set(METRIC_COLUMNS + NUMERIC_DIMENSION_COLUMNS + ["l2"]))
SEGMENT_SOURCE_COLUMNS = {
    "price_band": "price",
    "km_band": "kmstand",
    "car_age_band": "car_age",
    "photo_count_band": "photo_cnt",
}


def pct(series_or_number):
    """Format shares consistently for readable notebook/script output."""
    if pd.isna(series_or_number):
        return pd.NA
    return f"{series_or_number:.2%}"


def normal_cdf(value):
    return 0.5 * (1 + erf(value / sqrt(2)))


def infer_numeric_dtype(series):
    numeric_series = pd.to_numeric(series, errors="coerce")
    non_missing_values = numeric_series.dropna()

    if non_missing_values.mod(1).eq(0).all():
        integer_dtype = "Int64" if numeric_series.hasnans else "int64"
        return numeric_series.astype(integer_dtype)

    return numeric_series


def read_ab_test_data(data_path=DATA_PATH):
    dataframe = pd.read_csv(
        data_path,
        dtype={"src_ad_id": "string"},
        na_values=MISSING_VALUE_MARKERS,
    )

    for column in NUMERIC_IMPORT_COLUMNS:
        if column in dataframe.columns:
            dataframe[column] = infer_numeric_dtype(dataframe[column])

    if "ad_start_dt" in dataframe.columns:
        dataframe["ad_start_dt"] = pd.to_datetime(dataframe["ad_start_dt"], errors="coerce")

    return dataframe


def existing_columns(dataframe, requested_columns):
    return [column for column in requested_columns if column in dataframe.columns]


def prepare_ab_data(dataframe):
    ab_data = dataframe.loc[dataframe["group"].isin(VALID_GROUPS)].copy()
    excluded_data = dataframe.loc[~dataframe["group"].isin(VALID_GROUPS)].copy()

    metric_columns = existing_columns(ab_data, METRIC_COLUMNS)
    ab_data[metric_columns] = ab_data[metric_columns].fillna(0)
    ab_data["has_any_lead"] = ab_data[metric_columns].gt(0).any(axis=1)
    ab_data["total_leads"] = ab_data[metric_columns].sum(axis=1)

    if "bouwjaar" in ab_data.columns:
        reference_year = int(ab_data["bouwjaar"].max())
        ab_data["car_age"] = reference_year - ab_data["bouwjaar"]

    return ab_data, excluded_data


def column_quality_summary(dataframe, columns=IMPORTANT_COLUMNS):
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


def data_quality_checks(dataframe):
    duplicated_ad_rows = dataframe["src_ad_id"].duplicated(keep=False).sum()
    return pd.DataFrame(
        {
            "check": [
                "rows",
                "columns",
                "fully_duplicated_rows",
                "rows_with_duplicated_ad_id",
                "unique_ad_ids",
            ],
            "value": [
                len(dataframe),
                dataframe.shape[1],
                int(dataframe.duplicated().sum()),
                int(duplicated_ad_rows),
                int(dataframe["src_ad_id"].nunique(dropna=True)),
            ],
        }
    )


def undocumented_column_notes(dataframe):
    rows = []
    for column in dataframe.columns:
        if column not in IMPORTANT_COLUMNS:
            rows.append(
                {
                    "column": column,
                    "note": UNDOCUMENTED_COLUMN_NOTES.get(column, "not used in this analysis"),
                }
            )
    return pd.DataFrame(rows)


def duplicated_ad_id_rows(dataframe, columns=IMPORTANT_COLUMNS):
    columns = existing_columns(dataframe, columns)
    return (
        dataframe.loc[dataframe["src_ad_id"].duplicated(keep=False)]
        .sort_values(["src_ad_id", "group"])
        [columns]
        .reset_index(drop=True)
    )


def duplicated_ad_id_differences(dataframe, columns=IMPORTANT_COLUMNS):
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
    summary = dataframe["group"].value_counts(dropna=False).rename_axis("group").reset_index(name="rows")
    summary["share"] = summary["rows"] / len(dataframe)
    return summary


def excluded_group_summary(raw_data, excluded_data):
    dropped_rows = len(excluded_data)
    return pd.DataFrame(
        {
            "metric": ["raw_rows", "valid_ab_rows", "excluded_missing_group_rows"],
            "rows": [len(raw_data), len(raw_data) - dropped_rows, dropped_rows],
            "share_of_raw_rows": [1.0, (len(raw_data) - dropped_rows) / len(raw_data), dropped_rows / len(raw_data)],
        }
    )


def lead_metric_quality(dataframe):
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


def lead_outcome_summary(dataframe):
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
    by_group = lead_outcome_summary(dataframe).set_index("group")
    a = by_group.loc["A"]
    b = by_group.loc["B"]
    diff = b["lead_rate"] - a["lead_rate"]
    relative_lift = diff / a["lead_rate"]
    standard_error = ((a["lead_rate"] * (1 - a["lead_rate"]) / a["ads"]) + (b["lead_rate"] * (1 - b["lead_rate"]) / b["ads"])) ** 0.5

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
    observed_effect_power = (
        1 - normal_cdf((TWO_SIDED_Z_CRITICAL_95 * pooled_standard_error - abs(diff)) / unpooled_standard_error)
        + normal_cdf((-TWO_SIDED_Z_CRITICAL_95 * pooled_standard_error - abs(diff)) / unpooled_standard_error)
    )

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
                "Approx. power for observed effect",
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
                observed_effect_power,
            ],
        }
    )


def duplicate_id_sensitivity(dataframe):
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


def lead_distribution_summary(dataframe):
    summary = dataframe["total_leads"].describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.95, 0.99]).reset_index()
    summary.columns = ["metric", "value"]
    return summary


def numeric_balance_summary(dataframe):
    dimension_columns = existing_columns(dataframe, NUMERIC_DIMENSION_COLUMNS + ["car_age"])
    summary = dataframe.groupby("group")[dimension_columns].mean().T.reset_index().rename(columns={"index": "dimension"})
    if {"A", "B"}.issubset(summary.columns):
        summary["diff_B_minus_A"] = summary["B"] - summary["A"]
        summary["pct_diff_vs_A"] = summary["diff_B_minus_A"] / summary["A"]
    return summary


def categorical_balance_summary(dataframe, column, top_n=8):
    top_values = dataframe[column].value_counts(dropna=False).head(top_n).index
    filtered = dataframe.loc[dataframe[column].isin(top_values)].copy()
    counts = pd.crosstab(filtered[column], filtered["group"], dropna=False)
    shares = counts.div(counts.sum(axis=0), axis=1)
    summary = shares.reset_index()
    if {"A", "B"}.issubset(summary.columns):
        summary["share_diff_B_minus_A"] = summary["B"] - summary["A"]
    return summary


def add_segments(dataframe):
    segmented = dataframe.copy()

    segmented["price_band"] = pd.cut(
        segmented["price"],
        bins=[0, 25000, 60000, 120000, float("inf")],
        labels=["0-25k", "25k-60k", "60k-120k", "120k+"],
        include_lowest=True,
    )
    segmented["km_band"] = pd.cut(
        segmented["kmstand"],
        bins=[0, 75000, 150000, 200000, float("inf")],
        labels=["0-75k", "75k-150k", "150k-200k", "200k+"],
        include_lowest=True,
    )
    segmented["car_age_band"] = pd.cut(
        segmented["car_age"],
        bins=[-1, 3, 7, 12, 100],
        labels=["0-3", "4-7", "8-12", "13+"],
    )
    segmented["photo_count_band"] = pd.cut(
        segmented["photo_cnt"],
        bins=[-1, 5, 12, 20, 100],
        labels=["0-5", "6-12", "13-20", "21+"],
    )

    return segmented


def segment_coverage_summary(dataframe, segment_columns):
    rows = []
    for column in segment_columns:
        source_column = SEGMENT_SOURCE_COLUMNS.get(column, column)
        used_rows = dataframe[column].notna().sum()
        dropped_rows = len(dataframe) - used_rows
        missing_source_rows = dataframe[source_column].isna().sum() if source_column in dataframe.columns else pd.NA
        out_of_band_rows = (
            dataframe[source_column].notna().sum() - used_rows
            if source_column in dataframe.columns
            else pd.NA
        )
        rows.append(
            {
                "segment": column,
                "source_column": source_column,
                "rows_used": used_rows,
                "rows_dropped": dropped_rows,
                "missing_source_rows": missing_source_rows,
                "out_of_band_rows": out_of_band_rows,
                "pct_rows_dropped": dropped_rows / len(dataframe),
            }
        )
    return pd.DataFrame(rows)


def segment_outcome_summary(dataframe, segment_column, min_ads_per_group=200):
    summary = (
        dataframe.dropna(subset=[segment_column])
        .groupby([segment_column, "group"], observed=True)
        .agg(
            ads=("src_ad_id", "count"),
            lead_rate=("has_any_lead", "mean"),
            avg_total_leads=("total_leads", "mean"),
        )
        .reset_index()
    )

    wide = summary.pivot(index=segment_column, columns="group", values=["ads", "lead_rate", "avg_total_leads"])
    wide.columns = [f"{metric}_{group}" for metric, group in wide.columns]
    wide = wide.reset_index()

    if {"lead_rate_A", "lead_rate_B"}.issubset(wide.columns):
        wide["lead_rate_diff_B_minus_A"] = wide["lead_rate_B"] - wide["lead_rate_A"]
        wide["relative_lift_vs_A"] = wide["lead_rate_diff_B_minus_A"] / wide["lead_rate_A"]

    if {"ads_A", "ads_B"}.issubset(wide.columns):
        wide["small_segment_flag"] = (wide["ads_A"] < min_ads_per_group) | (wide["ads_B"] < min_ads_per_group)

    return wide


def top_category_segment_summary(dataframe, column, top_n=8, min_ads_per_group=200):
    top_values = dataframe[column].value_counts().head(top_n).index
    filtered = dataframe.loc[dataframe[column].isin(top_values)].copy()
    return segment_outcome_summary(filtered, column, min_ads_per_group=min_ads_per_group)


def business_insight_table(ab_data):
    lift = lead_rate_lift(ab_data).set_index("metric")["value"]
    outcomes = lead_outcome_summary(ab_data).set_index("group")
    numeric_balance = numeric_balance_summary(ab_data)
    largest_numeric_gap = numeric_balance.assign(abs_pct_diff=numeric_balance["pct_diff_vs_A"].abs()).sort_values("abs_pct_diff", ascending=False).iloc[0]

    return pd.DataFrame(
        {
            "topic": [
                "Primary outcome",
                "Statistical inference",
                "Lead volume",
                "Group balance",
                "Interpretation",
            ],
            "insight": [
                f"B has a {pct(lift['B minus A lead-rate difference'])} higher share of ads with any lead than A ({pct(lift['Relative lift vs A'])} relative lift).",
                "At a 5% significance level, the B-A lead-rate gap is statistically significant (p < 0.001). Approximate power for the observed effect is above 99.9%, meaning this sample size would be very likely to detect a true effect of this size.",
                f"B also has higher average total leads per ad ({outcomes.loc['B', 'avg_total_leads']:.3f} vs {outcomes.loc['A', 'avg_total_leads']:.3f}).",
                f"The largest average numeric balance gap is {largest_numeric_gap['dimension']} ({pct(largest_numeric_gap['pct_diff_vs_A'])} B vs A).",
                "The result is directionally positive, but should be framed as causal only after confirming the assignment process and exposure logging.",
            ],
        }
    )


def business_insight_lines(ab_data):
    insights = business_insight_table(ab_data)
    return [
        f"- {row['topic'].title()}: {row['insight']}"
        for _, row in insights.iterrows()
    ]


def print_business_insights(ab_data):
    print("\n".join(business_insight_lines(ab_data)))


def print_section(title):
    print(f"\n{'=' * len(title)}")
    print(title)
    print(f"{'=' * len(title)}")


DECIMAL_FORMAT_COLUMN_KEYWORDS = [
    "avg",
    "diff",
    "lift",
    "mean",
    "median",
    "p-value",
    "pct",
    "rate",
    "share",
    "std",
]
TABLE_DECIMALS = 3
NO_THOUSANDS_SEPARATOR_COLUMN_KEYWORDS = ["jaar", "year"]
HEADER_WORD_REPLACEMENTS = {
    "a": "A",
    "ab": "A/B",
    "ads": "Ads",
    "avg": "Average",
    "b": "B",
    "ci": "CI",
    "diff": "Difference",
    "id": "ID",
    "kpi": "KPI",
    "of": "of",
    "pct": "Percent",
    "vs": "vs",
}
DISPLAY_HEADER_ALIASES = {
    "ad_start_dt": "Start Date",
    "ads_a": "Ad Count A",
    "ads_b": "Ad Count B",
    "ads_with_any_lead": "Ads With Leads",
    "aantaldeuren": "Doors",
    "aantalstoelen": "Seats",
    "avg_total_leads": "Avg Leads/Ad",
    "avg_total_leads_a": "Avg Leads/Ad A",
    "avg_total_leads_b": "Avg Leads/Ad B",
    "avg_bids": "Avg Bids",
    "avg_questions": "Avg Questions",
    "avg_telclicks": "Avg Tel Clicks",
    "avg_webclicks": "Avg Web Clicks",
    "bouwjaar": "Build Year",
    "carrosserie": "Body Type",
    "diff_b_minus_a": "Diff B-A",
    "emissie": "Emissions",
    "energielabel": "Energy Label",
    "excluding_duplicate_id_rows": "Excl Dup IDs",
    "lead_rate_diff_b_minus_a": "Abs Lift",
    "group": "Test Group",
    "car_age_band": "Car Age Band",
    "km_band": "Mileage Band",
    "lead_rate": "Lead Rate",
    "lead_rate_a": "Lead Rate A",
    "lead_rate_b": "Lead Rate B",
    "median_total_leads": "Median Leads/Ad",
    "missing_pct": "Missing %",
    "missing_source_rows": "Missing Source",
    "n_asq": "Questions",
    "out_of_band_rows": "Out of Band",
    "pct_rows_dropped": "% Rows Dropped",
    "pct_diff_vs_a": "% Diff",
    "photo_count_band": "Photo Count Band",
    "photo_cnt": "Photos",
    "price_band": "Price Band",
    "relative_lift_vs_a": "Rel Lift",
    "rows_dropped": "Rows Dropped",
    "rows_used": "Rows Used",
    "share": "Row Share",
    "share_diff_b_minus_a": "Share Diff",
    "share_of_raw_rows": "Row Share",
    "small_segment_flag": "Small Segment",
    "source_column": "Source Column",
    "src_ad_id": "Ad ID",
    "telclicks": "Tel Clicks",
    "unique_values": "Unique",
    "vermogen": "Power",
    "webclicks": "Web Clicks",
    "with_duplicate_id_rows": "With Dup IDs",
}
DISPLAY_VALUE_ALIASES = {
    "A lead rate": "A Lead Rate",
    "A ads": "A Ads",
    "A ads with leads": "A Ads With Leads",
    "B lead rate": "B Lead Rate",
    "B ads": "B Ads",
    "B ads with leads": "B Ads With Leads",
    "B minus A lead-rate difference": "Abs Lead-Rate Lift",
    "Significance level": "Significance Level",
    "Approx. 95% CI lower for difference": "Approx 95% CI Lower",
    "Approx. 95% CI upper for difference": "Approx 95% CI Upper",
    "z statistic": "z Statistic",
    "Two-sided p-value": "Two-Sided p-Value",
    "Approx. power for observed effect": "Approx Power for Observed Effect",
    "ad_start_dt": "Start Date",
    "avg_total_leads": "Avg Leads/Ad",
    "aantaldeuren": "Doors",
    "aantalstoelen": "Seats",
    "bids": "Bids",
    "bouwjaar": "Build Year",
    "brand": "Brand",
    "car_age": "Car Age",
    "car_age_band": "Car Age Band",
    "carrosserie": "Body Type",
    "columns": "Columns",
    "count": "Count",
    "days_live": "Days Live",
    "diff_b_minus_a": "Diff B-A",
    "emissie": "Emissions",
    "energielabel": "Energy Label",
    "excluded_missing_group_rows": "Missing-Group Rows",
    "fully_duplicated_rows": "Fully Duplicated Rows",
    "km_band": "Mileage Band",
    "kmstand": "Mileage",
    "kleur": "Color",
    "l2": "L2",
    "max": "Max",
    "mean": "Mean",
    "median_total_leads": "Median Leads/Ad",
    "min": "Min",
    "model": "Model",
    "n_asq": "Questions",
    "pct_rows_dropped": "% Rows Dropped",
    "photo_count_band": "Photo Count Band",
    "photo_cnt": "Photos",
    "price": "Price",
    "price_band": "Price Band",
    "raw_rows": "Raw Rows",
    "Relative lift vs A": "Relative Lift vs A",
    "relative_lift_vs_a": "Relative Lift vs A",
    "rows": "Rows",
    "rows_dropped": "Rows Dropped",
    "rows_with_duplicated_ad_id": "Rows With Duplicated Ad ID",
    "std": "Std",
    "src_ad_id": "Ad ID",
    "telclicks": "Tel Clicks",
    "group": "Test Group",
    "unique_ad_ids": "Unique Ad IDs",
    "valid_ab_rows": "Valid A/B Rows",
    "vermogen": "Power",
    "webclicks": "Web Clicks",
}


def format_table_header(column):
    normalized_column = str(column).lower()
    if normalized_column in DISPLAY_HEADER_ALIASES:
        return DISPLAY_HEADER_ALIASES[normalized_column]

    words = str(column).replace("_", " ").split()
    return " ".join(
        HEADER_WORD_REPLACEMENTS.get(word.lower(), word.title())
        for word in words
    )


def format_table_value(value, column, row=None):
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
    return format_table_for_display(table, max_rows=max_rows).style


def print_table(title, table, max_rows=30):
    print(f"\n{title}")
    display_table = format_table_for_display(table, max_rows=max_rows)
    print(display_table.to_string(index=False))

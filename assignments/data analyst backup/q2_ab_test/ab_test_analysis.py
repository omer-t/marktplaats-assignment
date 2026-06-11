import pandas as pd

pd.set_option("display.float_format", "{:.3f}".format)


DATA_PATH = "../../../data/Adevinta Cars Dataset May 2019.csv"

COLUMN_DTYPES = {
    "src_ad_id": "string",
    "telclicks": "Int64",
    "bids": "Int64",
    "n_asq": "Int64",
    "webclicks": "Int64",
    "price": "Int64",
    "kmstand": "Int64",
    "days_live": "Int64",
    "photo_cnt": "Int64",
    "aantaldeuren": "Int64",
    "aantalstoelen": "Int64",
    "bouwjaar": "Int64",
    "emissie": "Int64",
    "vermogen": "Float64",
    "l2": "Int64",
}

MISSING_VALUE_MARKERS = ["?"]

METRIC_COLUMNS = ["telclicks", "bids", "n_asq", "webclicks"]
DIMENSION_COLUMNS = [
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


# ---------- Helpers ----------

def print_table(table_title, table_data, max_rows=30):
    print(f"\n{table_title}")
    print(table_data.head(max_rows).to_string(index=False))


def read_csv_with_column_dtypes(file_path, column_dtypes, missing_value_markers):
    dataframe = pd.read_csv(
        file_path,
        dtype={"src_ad_id": "string"},
        na_values=missing_value_markers,
    )

    for column_name, dtype in column_dtypes.items():
        if column_name not in dataframe.columns or column_name == "src_ad_id":
            continue

        dataframe[column_name] = pd.to_numeric(dataframe[column_name], errors="coerce").astype(dtype)

    return dataframe


def existing_columns(dataframe, requested_columns):
    return [column_name for column_name in requested_columns if column_name in dataframe.columns]


# ---------- 1. Data Validity ----------

def summarize_columns(dataframe):
    return (
        pd.DataFrame({
            "column": dataframe.columns,
            "dtype": dataframe.dtypes.astype(str),
            "missing_rows": dataframe.isna().sum().values,
            "missing_pct": dataframe.isna().mean().values,
            "unique_values": dataframe.nunique(dropna=True).values,
        })
        .sort_values(["missing_pct", "column"], ascending=[False, True])
        .reset_index(drop=True)
    )


def show_duplicated_ad_ids(dataframe):
    duplicated_ad_ids = dataframe.loc[dataframe["src_ad_id"].duplicated(keep=False), "src_ad_id"]

    print(f"Fully duplicated rows: {dataframe.duplicated().sum():,}")
    print(f"Rows with duplicated ad ID: {len(duplicated_ad_ids):,}")
    print(f"Duplicated ad IDs: {duplicated_ad_ids.nunique():,}")


# ---------- 2. A/B Group Sizes ----------

def summarize_groups(dataframe):
    group_summary = (
        dataframe["group"]
        .value_counts(dropna=False)
        .rename_axis("group")
        .reset_index(name="rows")
    )
    group_summary["share"] = group_summary["rows"] / len(dataframe)
    return group_summary


def build_clean_data(dataframe, metric_columns):
    clean_data = dataframe.loc[dataframe["group"].isin(["A", "B"])].copy()
    missing_group_rows = dataframe.loc[~dataframe["group"].isin(["A", "B"])]

    clean_data[metric_columns] = clean_data[metric_columns].fillna(0)
    clean_data["has_any_lead"] = clean_data[metric_columns].gt(0).any(axis=1)
    clean_data["total_leads"] = clean_data[metric_columns].sum(axis=1)
    clean_data["car_age"] = clean_data["bouwjaar"].max() - clean_data["bouwjaar"]

    print(f"Raw rows before cleaning: {len(dataframe):,}")
    print(f"Rows with valid A/B group: {len(clean_data):,}")
    print(f"Rows with missing group: {len(missing_group_rows):,}")

    return clean_data


# ---------- 3. Lead Metric Quality ----------

def summarize_lead_metric_quality(dataframe, metric_columns):
    return pd.DataFrame({
        "column": metric_columns,
        "missing_rows": [dataframe[column_name].isna().sum() for column_name in metric_columns],
        "missing_pct": [dataframe[column_name].isna().mean() for column_name in metric_columns],
        "negative_rows": [(dataframe[column_name] < 0).sum() for column_name in metric_columns],
        "zero_rows": [(dataframe[column_name] == 0).sum() for column_name in metric_columns],
        "max_value": [dataframe[column_name].max() for column_name in metric_columns],
    })


# ---------- 4. Raw Leads by Group ----------

def summarize_overall_leads(dataframe):
    return pd.DataFrame({
        "metric": [
            "Ads",
            "Share with any lead",
            "Average total leads per ad",
            "Median total leads per ad",
        ],
        "value": [
            f"{len(dataframe):,}",
            dataframe["has_any_lead"].mean(),
            dataframe["total_leads"].mean(),
            dataframe["total_leads"].median(),
        ],
    })


def summarize_leads_by_group(dataframe):
    return (
        dataframe
        .groupby("group")
        .agg(
            ads=("src_ad_id", "count"),
            share_with_any_lead=("has_any_lead", "mean"),
            avg_total_leads=("total_leads", "mean"),
            median_total_leads=("total_leads", "median"),
            avg_telclicks=("telclicks", "mean"),
            avg_bids=("bids", "mean"),
            avg_questions=("n_asq", "mean"),
            avg_webclicks=("webclicks", "mean"),
        )
        .reset_index()
    )


# ---------- 5. Lead Distribution ----------

def summarize_lead_distribution(dataframe):
    lead_distribution_summary = (
        dataframe["total_leads"]
        .describe(percentiles=[0.25, 0.50, 0.75, 0.90, 0.95, 0.99])
        .reset_index()
    )
    lead_distribution_summary.columns = ["metric", "value"]
    return lead_distribution_summary


# ---------- 6. Dimensions by Group ----------

def summarize_dimensions_by_group(dataframe, dimension_columns):
    dimension_summary = (
        dataframe
        .groupby("group")[dimension_columns]
        .mean()
        .T
        .reset_index()
        .rename(columns={"index": "variable"})
    )

    if {"A", "B"}.issubset(dimension_summary.columns):
        dimension_summary["diff_B_minus_A"] = dimension_summary["B"] - dimension_summary["A"]
        dimension_summary["pct_diff_vs_A"] = dimension_summary["diff_B_minus_A"] / dimension_summary["A"]

    return dimension_summary


# ---------- 7. Segmented Leads by Key Dimensions ----------

def add_lead_segments(dataframe):
    segmented_data = dataframe.copy()

    segmented_data["price_band"] = pd.qcut(segmented_data["price"], q=4, duplicates="drop")
    segmented_data["km_band"] = pd.qcut(segmented_data["kmstand"], q=4, duplicates="drop")
    segmented_data["car_age_band"] = pd.cut(
        segmented_data["car_age"],
        bins=[-1, 3, 7, 12, 100],
        labels=["0-3", "4-7", "8-12", "13+"],
    )
    segmented_data["photo_count_band"] = pd.cut(
        segmented_data["photo_cnt"],
        bins=[-1, 5, 12, 20, 100],
        labels=["0-5", "6-12", "13-20", "21+"],
    )

    return segmented_data


def summarize_leads_by_segment(dataframe, segment_column):
    return (
        dataframe
        .dropna(subset=[segment_column])
        .groupby([segment_column, "group"], observed=True)
        .agg(
            ads=("src_ad_id", "count"),
            share_with_any_lead=("has_any_lead", "mean"),
            avg_total_leads=("total_leads", "mean"),
        )
        .reset_index()
    )


# ---------- Run Analysis ----------

raw_df = read_csv_with_column_dtypes(DATA_PATH, COLUMN_DTYPES, MISSING_VALUE_MARKERS)

metric_columns = existing_columns(raw_df, METRIC_COLUMNS)
dimension_columns = existing_columns(raw_df, DIMENSION_COLUMNS)

print("\n1. Data Validity")
print(f"Rows: {raw_df.shape[0]:,}")
print(f"Columns: {raw_df.shape[1]:,}")
print_table("Column Summary", summarize_columns(raw_df))
show_duplicated_ad_ids(raw_df)

print("\n2. A/B Group Sizes")
print_table("Rows by Group", summarize_groups(raw_df))
clean_df = build_clean_data(raw_df, metric_columns)
print_table("Clean Rows by Group", summarize_groups(clean_df))

print("\n3. Lead Metric Quality")
print_table("Lead Metric Quality", summarize_lead_metric_quality(raw_df, metric_columns))

print("\n4. Raw Leads by Group")
print_table("Overall Lead Summary", summarize_overall_leads(clean_df))
print_table("Leads by Group", summarize_leads_by_group(clean_df))

print("\n5. Lead Distribution")
print_table("Total Lead Distribution", summarize_lead_distribution(clean_df))

print("\n6. Dimensions by Group")
print_table("Dimensions by Group", summarize_dimensions_by_group(clean_df, dimension_columns))

print("\n7. Segmented Leads by Key Dimensions")
segmented_df = add_lead_segments(clean_df)
print_table("Leads by Price Band", summarize_leads_by_segment(segmented_df, "price_band"))
print_table("Leads by Mileage Band", summarize_leads_by_segment(segmented_df, "km_band"))
print_table("Leads by Car Age Band", summarize_leads_by_segment(segmented_df, "car_age_band"))
print_table("Leads by Photo Count Band", summarize_leads_by_segment(segmented_df, "photo_count_band"))
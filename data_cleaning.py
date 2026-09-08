"""
data_cleaning.py

Takes raw scraped quotes (messy: sold-outs, missing values, outliers) and
produces a clean, analysis-ready dataset.

Steps (matches "Expected Solution" part b of the problem statement):
  1. Drop sold-out / unavailable quotes
  2. Handle missing values (recompute from what's available, else drop)
  3. Remove statistical outliers per route+window group (IQR method)
  4. De-duplicate exact duplicate rows
  5. Ensure base_fare + taxes = total_fare consistently
"""

import pandas as pd


def load_raw(path="raw_airfare_quotes.csv"):
    return pd.read_csv(path)


def clean(df):
    original_count = len(df)

    # 1. Drop sold-out / unavailable flights
    df = df[df["status"] == "OK"].copy()

    # 2. Coerce numeric columns, handle missing values
    for col in ["base_fare", "taxes", "total_fare"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # If taxes missing but base_fare + total_fare present, back-fill it
    mask = df["taxes"].isna() & df["base_fare"].notna() & df["total_fare"].notna()
    df.loc[mask, "taxes"] = df.loc[mask, "total_fare"] - df.loc[mask, "base_fare"]

    # If total_fare missing but base+taxes present, recompute it
    mask = df["total_fare"].isna() & df["base_fare"].notna() & df["taxes"].notna()
    df.loc[mask, "total_fare"] = df.loc[mask, "base_fare"] + df.loc[mask, "taxes"]

    # Drop rows still missing the essentials after backfill attempts
    df = df.dropna(subset=["base_fare", "total_fare"])

    # 3. Remove outliers per (route, advance_window) group using IQR.
    # Using transform (not apply) so it's robust across pandas versions and
    # never silently drops the grouping columns from the result.
    group_cols = ["origin", "destination", "advance_window_days"]
    grouped = df.groupby(group_cols)["total_fare"]
    q1 = grouped.transform(lambda s: s.quantile(0.25))
    q3 = grouped.transform(lambda s: s.quantile(0.75))
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    df = df[(df["total_fare"] >= lower) & (df["total_fare"] <= upper)]

    # 4. De-duplicate
    df = df.drop_duplicates()

    # 5. Sanity: recompute total_fare consistently from base+taxes
    df["total_fare"] = (df["base_fare"] + df["taxes"]).round(2)

    cleaned_count = len(df)
    print(
        f"Cleaned: {original_count} raw rows -> {cleaned_count} clean rows "
        f"({original_count - cleaned_count} removed: sold-out/missing/outliers/dupes)"
    )
    return df.reset_index(drop=True)


def run(raw_path="raw_airfare_quotes.csv", out_path="clean_airfare_quotes.csv"):
    df = load_raw(raw_path)
    clean_df = clean(df)
    clean_df.to_csv(out_path, index=False)
    print(f"Saved cleaned dataset -> {out_path}")
    return out_path


if __name__ == "__main__":
    run()

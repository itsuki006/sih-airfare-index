"""
index_calculator.py

Computes the Real-time Airfare Price Index (APIx) from cleaned fare data.

Method (Laspeyres-style weighted price relative -- same family of formula
CPI itself uses):

    APIx_t = 100 * sum( weight_route * (price_route,t / price_route,base) )

where:
  - price_route,t   = average total_fare for that route on day t
                       (averaged across carriers & advance-purchase windows)
  - price_route,base = average total_fare for that route in the base period
                       (first N days of available data)
  - weight_route     = route's share in the basket (proxy for passenger
                       traffic share -- swap in real DGCA weights later)

Output: one APIx value per day, plus weekly/monthly rollups, plus a
per-route sub-index (useful for the "sector-wise heatmap" requirement).
"""

import pandas as pd

# same weights as used in mock_data_generator.py -- in the real system this
# comes from DGCA passenger-traffic data, not hardcoded here
ROUTE_WEIGHTS = {
    ("DEL", "BOM"): 0.25,
    ("DEL", "BLR"): 0.20,
    ("BOM", "BLR"): 0.15,
    ("DEL", "CCU"): 0.15,
    ("BLR", "HYD"): 0.10,
    ("MAA", "DEL"): 0.15,
}

BASE_PERIOD_DAYS = 7  # first week of data = base period, index = 100


def load_clean(path="clean_airfare_quotes.csv"):
    df = pd.read_csv(path)
    df["scrape_date"] = pd.to_datetime(df["scrape_date"])
    return df


def daily_route_price(df):
    """Average total_fare per route per day (across carriers + advance windows)."""
    grouped = (
        df.groupby(["scrape_date", "origin", "destination"])["total_fare"]
        .mean()
        .reset_index()
    )
    return grouped


def compute_index(df):
    route_daily = daily_route_price(df)

    base_period_end = route_daily["scrape_date"].min() + pd.Timedelta(days=BASE_PERIOD_DAYS - 1)
    base_prices = (
        route_daily[route_daily["scrape_date"] <= base_period_end]
        .groupby(["origin", "destination"])["total_fare"]
        .mean()
        .rename("base_price")
    )

    route_daily = route_daily.merge(base_prices, on=["origin", "destination"], how="left")
    route_daily["weight"] = route_daily.apply(
        lambda r: ROUTE_WEIGHTS.get((r["origin"], r["destination"]), 0), axis=1
    )
    route_daily["price_relative"] = route_daily["total_fare"] / route_daily["base_price"]
    route_daily["weighted_relative"] = route_daily["price_relative"] * route_daily["weight"]

    # Sub-index per route (useful for heatmap / route-wise breakdown)
    route_daily["route_sub_index"] = 100 * route_daily["price_relative"]

    daily_index = (
        route_daily.groupby("scrape_date")["weighted_relative"]
        .sum()
        .mul(100)
        .rename("APIx")
        .reset_index()
    )

    return daily_index, route_daily


def rollups(daily_index):
    df = daily_index.set_index("scrape_date")
    weekly = df["APIx"].resample("W").mean().rename("APIx_weekly").reset_index()
    monthly = df["APIx"].resample("ME").mean().rename("APIx_monthly").reset_index()
    return weekly, monthly


def run(clean_path="clean_airfare_quotes.csv"):
    df = load_clean(clean_path)
    daily_index, route_daily = compute_index(df)
    weekly, monthly = rollups(daily_index)

    daily_index.to_csv("apix_daily.csv", index=False)
    weekly.to_csv("apix_weekly.csv", index=False)
    monthly.to_csv("apix_monthly.csv", index=False)
    route_daily.to_csv("apix_route_breakdown.csv", index=False)

    print("Daily APIx (last 5 days):")
    print(daily_index.tail())
    print(f"\nBase period: first {BASE_PERIOD_DAYS} days = index 100")
    print("Saved: apix_daily.csv, apix_weekly.csv, apix_monthly.csv, apix_route_breakdown.csv")

    return daily_index, weekly, monthly, route_daily


if __name__ == "__main__":
    run()

"""
mock_data_generator.py

Simulates raw airfare quotes as if collected by the web-scraping engine.
This lets us build/demo the cleaning + index pipeline WITHOUT depending on
live scraping (which is fragile mid-demo due to anti-bot measures).

Once a real scraper is ready, its output just needs to match this same
CSV schema and it plugs straight into data_cleaning.py.
"""

import random
import datetime
import csv

random.seed(42)  # reproducible demo data

# ---- Representative city-pair basket (from problem statement) ----
# weight = rough share of domestic passenger traffic (illustrative, based on
# DGCA-style route importance -- replace with real DGCA figures later)
ROUTES = [
    {"origin": "DEL", "destination": "BOM", "weight": 0.25, "base_price": 4500},
    {"origin": "DEL", "destination": "BLR", "weight": 0.20, "base_price": 5200},
    {"origin": "BOM", "destination": "BLR", "weight": 0.15, "base_price": 4000},
    {"origin": "DEL", "destination": "CCU", "weight": 0.15, "base_price": 5500},
    {"origin": "BLR", "destination": "HYD", "weight": 0.10, "base_price": 3200},
    {"origin": "MAA", "destination": "DEL", "weight": 0.15, "base_price": 6000},
]

CARRIERS = ["IndiGo", "Air India", "Air India Express", "Akasa Air", "SpiceJet"]

# Advance purchase windows (days before travel)
ADVANCE_WINDOWS = [1, 7, 15, 30, 45]

# Advance-window price multiplier: booking last-minute (T+1) costs more
WINDOW_MULTIPLIER = {1: 1.9, 7: 1.5, 15: 1.2, 30: 1.0, 45: 0.85}

CARRIER_MULTIPLIER = {
    "IndiGo": 1.0,
    "Air India": 1.1,
    "Air India Express": 0.85,
    "Akasa Air": 0.95,
    "SpiceJet": 0.9,
}

TAX_RATE = 0.16  # approx taxes + UDF + convenience fee as % of base fare


def day_of_week_multiplier(date):
    # Fri/Sun busier -> pricier; midweek cheaper
    dow = date.weekday()  # 0=Mon
    return {0: 1.0, 1: 0.95, 2: 0.95, 3: 1.0, 4: 1.15, 5: 1.05, 6: 1.2}[dow]


def festival_spike(date):
    # simulate a demand spike window (e.g. festival season) for realism
    festival_ranges = [
        (datetime.date(2026, 10, 15), datetime.date(2026, 10, 25)),
    ]
    for start, end in festival_ranges:
        if start <= date <= end:
            return 1.4
    return 1.0


def generate_quote(route, carrier, window, scrape_date):
    base = route["base_price"]
    price = (
        base
        * WINDOW_MULTIPLIER[window]
        * CARRIER_MULTIPLIER[carrier]
        * day_of_week_multiplier(scrape_date)
        * festival_spike(scrape_date)
        * random.uniform(0.92, 1.08)  # market noise
    )

    # occasionally simulate sold-out flights (no fare available)
    if random.random() < 0.04:
        return {
            "scrape_date": scrape_date.isoformat(),
            "origin": route["origin"],
            "destination": route["destination"],
            "carrier": carrier,
            "advance_window_days": window,
            "base_fare": "",
            "taxes": "",
            "total_fare": "",
            "status": "SOLD_OUT",
        }

    # occasionally inject a bad/outlier record (to give the cleaning step real work)
    if random.random() < 0.02:
        price *= random.choice([0.1, 5.0])  # obviously broken scrape

    base_fare = round(price, 2)
    taxes = round(base_fare * TAX_RATE, 2)
    total_fare = round(base_fare + taxes, 2)

    # occasionally drop a field to simulate missing data
    if random.random() < 0.03:
        taxes = ""

    return {
        "scrape_date": scrape_date.isoformat(),
        "origin": route["origin"],
        "destination": route["destination"],
        "carrier": carrier,
        "advance_window_days": window,
        "base_fare": base_fare,
        "taxes": taxes,
        "total_fare": total_fare,
        "status": "OK",
    }


def generate_dataset(num_days=45, out_path="raw_airfare_quotes.csv"):
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=num_days - 1)

    rows = []
    d = start_date
    while d <= end_date:
        for route in ROUTES:
            for window in ADVANCE_WINDOWS:
                for carrier in CARRIERS:
                    rows.append(generate_quote(route, carrier, window, d))
        d += datetime.timedelta(days=1)

    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} raw quote rows -> {out_path}")
    return out_path


if __name__ == "__main__":
    generate_dataset()

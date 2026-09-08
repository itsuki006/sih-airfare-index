"""
export_static_data.py

Converts the pipeline's CSV outputs into static JSON files that
apix_dashboard.html can fetch directly -- no backend/API required.
This is what makes the dashboard deployable on GitHub Pages (or any
static host), since those can't run api.py's Python server.

Run this AFTER main.py (which generates the CSVs).

Output: a data/ folder containing daily.json, weekly.json, monthly.json,
heatmap.json, elasticity.json -- the dashboard fetches these by relative path.
"""

import json
from pathlib import Path
import pandas as pd

OUT_DIR = Path("data")


def export():
    OUT_DIR.mkdir(exist_ok=True)

    daily = pd.read_csv("apix_daily.csv")
    daily.to_json(OUT_DIR / "daily.json", orient="records")

    weekly = pd.read_csv("apix_weekly.csv")
    weekly.to_json(OUT_DIR / "weekly.json", orient="records")

    monthly = pd.read_csv("apix_monthly.csv")
    monthly.to_json(OUT_DIR / "monthly.json", orient="records")

    # heatmap: 7-day average sub-index per route (same logic as api.py)
    rb = pd.read_csv("apix_route_breakdown.csv")
    rb["scrape_date"] = pd.to_datetime(rb["scrape_date"])
    cutoff = rb["scrape_date"].max() - pd.Timedelta(days=7)
    recent = rb[rb["scrape_date"] > cutoff]
    heatmap = (
        recent.groupby(["origin", "destination"])["route_sub_index"]
        .mean().round(1).reset_index()
    )
    heatmap["route"] = heatmap["origin"] + "\u2013" + heatmap["destination"]
    heatmap = heatmap[["route", "route_sub_index"]].rename(columns={"route_sub_index": "v"})
    heatmap.to_json(OUT_DIR / "heatmap.json", orient="records")

    # elasticity: average fare by advance-purchase window
    clean = pd.read_csv("clean_airfare_quotes.csv")
    elasticity = (
        clean.groupby("advance_window_days")["total_fare"]
        .mean().round(0).reset_index().sort_values("advance_window_days")
    )
    elasticity["window"] = "T+" + elasticity["advance_window_days"].astype(str)
    elasticity = elasticity[["window", "total_fare"]].rename(columns={"total_fare": "fare"})
    elasticity.to_json(OUT_DIR / "elasticity.json", orient="records")

    print(f"Exported static JSON files to {OUT_DIR}/")
    for f in sorted(OUT_DIR.glob("*.json")):
        print(f"  {f}")


if __name__ == "__main__":
    export()

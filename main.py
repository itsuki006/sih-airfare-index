"""
main.py

Runs the full prototype pipeline end-to-end:
  mock scraping -> cleaning -> index calculation -> chart

This is the "safe demo core" -- it always works because it doesn't depend
on live websites. Swap mock_data_generator's output for a real scraper's
output later; nothing downstream needs to change since the CSV schema
is the same.
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import mock_data_generator
import data_cleaning
import index_calculator


def main():
    print("=" * 60)
    print("STEP 1: Simulating scraped airfare quotes")
    print("=" * 60)
    raw_path = mock_data_generator.generate_dataset(num_days=45)

    print("\n" + "=" * 60)
    print("STEP 2: Cleaning raw quotes")
    print("=" * 60)
    clean_path = data_cleaning.run(raw_path)

    print("\n" + "=" * 60)
    print("STEP 3: Computing Airfare Price Index (APIx)")
    print("=" * 60)
    daily_index, weekly, monthly, route_breakdown = index_calculator.run(clean_path)

    print("\n" + "=" * 60)
    print("STEP 4: Generating chart")
    print("=" * 60)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(daily_index["scrape_date"], daily_index["APIx"], marker="o", markersize=3, linewidth=1.5)
    ax.axhline(100, color="gray", linestyle="--", linewidth=1, label="Base period (=100)")
    ax.set_title("Real-time Airfare Price Index (APIx) - Prototype")
    ax.set_xlabel("Date")
    ax.set_ylabel("Index value")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig("apix_trend_chart.png", dpi=150)
    print("Saved chart -> apix_trend_chart.png")

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)
    print(f"Latest APIx: {daily_index['APIx'].iloc[-1]:.2f}")
    print(f"Change from base period: {daily_index['APIx'].iloc[-1] - 100:+.2f} points")


if __name__ == "__main__":
    main()

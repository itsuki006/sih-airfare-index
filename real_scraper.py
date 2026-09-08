"""
real_scraper.py

Template for the real (non-mock) scraping stage.

IMPORTANT — READ BEFORE RUNNING:
1. This has NOT been run against a live site. It was written without live
   network access, so the CSS selectors below are PLACEHOLDERS. You must
   open the target site in a real browser, inspect the flight-search
   results with dev tools, and replace the selector strings marked "ADJUST".
   Sites like this are JS-heavy SPAs whose markup changes often, so expect
   to iterate.
2. This deliberately does NOT include CAPTCHA-solving or IP-rotation /
   proxy-evasion logic. Those exist specifically to defeat a site's
   anti-bot protections, which is a different (and legally greyer) thing
   than automating a normal browsing session. For a hackathon prototype,
   the honest options if you get blocked are: (a) scrape at low frequency
   from a single IP like a real user would, (b) scrape fewer routes, or
   (c) look into whether the OTA offers an official partner/affiliate API
   -- several do, and that's the legitimate path for a production system.
3. Always re-check robots.txt at runtime (done below) rather than assuming
   it hasn't changed since you last looked.

Output schema matches mock_data_generator.py exactly, so this plugs
straight into data_cleaning.py with zero changes downstream:
    scrape_date, origin, destination, carrier, advance_window_days,
    base_fare, taxes, total_fare, status
"""

import csv
import datetime
import random
import time
import urllib.robotparser
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

# ---- Config: same route basket as the rest of the pipeline ----
ROUTES = [
    {"origin": "DEL", "destination": "BOM"},
    {"origin": "DEL", "destination": "BLR"},
]
ADVANCE_WINDOWS = [7, 15, 30]  # start small; expand once this is verified working

MIN_DELAY_SECONDS = 4  # rate-limiting: don't hammer the site
MAX_DELAY_SECONDS = 9

SOURCE_NAME = "IndiGo"  # ADJUST: which airline/OTA this instance targets
BASE_URL = "https://www.goindigo.in"  # ADJUST if targeting a different source


def robots_allows(base_url, path, user_agent="*"):
    """Check robots.txt at runtime -- don't hardcode assumptions about it."""
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(urljoin(base_url, "/robots.txt"))
    try:
        rp.read()
    except Exception as e:
        print(f"Could not fetch robots.txt ({e}) -- aborting rather than guessing.")
        return False
    return rp.can_fetch(user_agent, urljoin(base_url, path))


def scrape_one_quote(page, route, advance_window, scrape_date):
    """
    Scrapes a single fare quote for one route + advance-purchase window.

    ADJUST EVERYTHING BELOW to match the real site once you've inspected it
    with browser dev tools (right-click -> Inspect on the fare element).
    This structure (fill origin -> fill destination -> pick date -> submit
    -> read fare) is the general shape of most flight-search flows, but
    the actual selectors will not match until you supply real ones.
    """
    travel_date = scrape_date + datetime.timedelta(days=advance_window)

    search_path = "/"  # ADJUST: path to the flight search form
    if not robots_allows(BASE_URL, search_path):
        print(f"robots.txt disallows {search_path} -- skipping.")
        return {
            "scrape_date": scrape_date.isoformat(),
            "origin": route["origin"],
            "destination": route["destination"],
            "carrier": SOURCE_NAME,
            "advance_window_days": advance_window,
            "base_fare": "", "taxes": "", "total_fare": "",
            "status": "SKIPPED_ROBOTS_TXT",
        }

    page.goto(urljoin(BASE_URL, search_path), wait_until="networkidle")

    # --- Fill search form (ADJUST selectors) ---
    page.fill("input#origin-city", route["origin"])          # ADJUST
    page.fill("input#destination-city", route["destination"])  # ADJUST
    page.fill("input#travel-date", travel_date.strftime("%d/%m/%Y"))  # ADJUST
    page.click("button#search-flights")                       # ADJUST
    page.wait_for_selector(".fare-result-card", timeout=15000)  # ADJUST

    # --- Read the cheapest fare shown (ADJUST selectors/parsing) ---
    try:
        base_fare_text = page.inner_text(".fare-result-card .base-fare")   # ADJUST
        taxes_text = page.inner_text(".fare-result-card .taxes-fees")      # ADJUST
        base_fare = float(base_fare_text.replace("₹", "").replace(",", "").strip())
        taxes = float(taxes_text.replace("₹", "").replace(",", "").strip())
        status = "OK"
    except Exception:
        base_fare, taxes, status = None, None, "NO_FARE_FOUND"

    total_fare = round(base_fare + taxes, 2) if base_fare is not None else ""

    return {
        "scrape_date": scrape_date.isoformat(),
        "origin": route["origin"],
        "destination": route["destination"],
        "carrier": SOURCE_NAME,
        "advance_window_days": advance_window,
        "base_fare": base_fare if base_fare is not None else "",
        "taxes": taxes if taxes is not None else "",
        "total_fare": total_fare,
        "status": status,
    }


def run(out_path="real_airfare_quotes.csv"):
    scrape_date = datetime.date.today()
    rows = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        for route in ROUTES:
            for window in ADVANCE_WINDOWS:
                print(f"Scraping {route['origin']}-{route['destination']} T+{window}...")
                try:
                    row = scrape_one_quote(page, route, window, scrape_date)
                except Exception as e:
                    print(f"  Failed: {e}")
                    row = {
                        "scrape_date": scrape_date.isoformat(),
                        "origin": route["origin"], "destination": route["destination"],
                        "carrier": SOURCE_NAME, "advance_window_days": window,
                        "base_fare": "", "taxes": "", "total_fare": "",
                        "status": "SCRAPE_ERROR",
                    }
                rows.append(row)

                # rate limiting -- be a polite, low-volume visitor
                time.sleep(random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS))

        browser.close()

    if rows:
        with open(out_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        print(f"Saved {len(rows)} rows -> {out_path}")

    return out_path


if __name__ == "__main__":
    run()

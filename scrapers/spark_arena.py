from urllib.parse import urljoin

import pandas as pd
from dateutil import parser
from playwright.sync_api import sync_playwright
from datetime import date


def scrape_spark_arena():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        base_url = "https://www.sparkarena.co.nz"
        page.goto(f"{base_url}/all-events")

        year = date.today().year
        events = []
        event_cards = page.query_selector_all("li.MuiCardActionArea-root")
        print(f"Found {len(event_cards)} event cards")

        for card in event_cards:
            try:
                # Title
                title = (
                    card.query_selector("h3.MuiTypography-header3").inner_text().strip()
                )
            except Exception as e:
                title = "N/A"
                print(f"Warning: Could not find event title: {e}")
                continue

            try:
                raw_date = (
                    card.query_selector("time[class*='bgcce-ltr']").inner_text().strip()
                )
                # Convert "TUE 18 FEB" to "18 FEB 2024"
                date_str = " ".join(raw_date.split()[1:]) + f" {year}"  # Remove weekday
                event_date = parser.parse(date_str, dayfirst=True).date().isoformat()
            except Exception as e:
                print(f"Date parsing failed for '{raw_date}': {e}")
                event_date = "N/A"

            try:
                # URL handling
                rel_url = card.query_selector("a.event-ticket-link").get_attribute(
                    "href"
                )
                full_url = urljoin(base_url, rel_url)
            except Exception as e:
                print(f"Warning: Could not find URL :{e}")
                full_url = "N/A"

            events.append({"Title": title, "Event Date": event_date, "URL": full_url})

        # Save to CSV
        df = pd.DataFrame(events)
        df.to_csv("data/spark_arena_events.csv", index=False)
        print(f"Successfully saved {len(events)} events")

        browser.close()


if __name__ == "__main__":
    scrape_spark_arena()

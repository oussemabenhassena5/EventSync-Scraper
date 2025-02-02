import time
from datetime import date
from urllib.parse import urljoin

import pandas as pd
from dateutil import parser
from playwright.sync_api import sync_playwright


def scrape_spark_arena():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        base_url = "https://www.sparkarena.co.nz"
        page.goto(f"{base_url}/all-events")

        year = date.today().year
        events = []
        page_number = 1

        while True:
            print(f"Scraping page {page_number}...")
            page.wait_for_load_state("networkidle")

            event_cards = page.query_selector_all("li.MuiCardActionArea-root")
            print(f"Found {len(event_cards)} event cards")

            for card in event_cards:
                try:
                    title = (
                        card.query_selector("h3.MuiTypography-header3")
                        .inner_text()
                        .strip()
                    )
                except Exception:
                    title = "N/A"
                    continue

                try:
                    raw_date = (
                        card.query_selector("time[class*='bgcce-ltr']")
                        .inner_text()
                        .strip()
                    )
                    date_str = " ".join(raw_date.split()[1:]) + f" {year}"
                    event_date = (
                        parser.parse(date_str, dayfirst=True).date().isoformat()
                    )
                except Exception:
                    event_date = "N/A"

                try:
                    rel_url = card.query_selector("a.event-ticket-link").get_attribute(
                        "href"
                    )
                    full_url = urljoin(base_url, rel_url)
                except Exception:
                    full_url = "N/A"

                events.append(
                    {"Title": title, "Event Date": event_date, "URL": full_url}
                )

            # ✅ Check if the Next button exists and is visible
            next_button = page.query_selector("button[aria-label='Go to next page']")
            if next_button and next_button.is_visible():
                try:
                    print(f"Navigating to page {page_number + 1}...")
                    next_button.click()
                    time.sleep(2)  # Give time for the new page to load
                    page_number += 1
                except Exception as e:
                    print(f"Error clicking next button: {e}")
                    break
            else:
                print("No more pages or Next button is disabled.")
                break  # Stop pagination

        df = pd.DataFrame(events)
        df.to_csv("data/spark_arena_events.csv", index=False)
        print(f"Successfully saved {len(events)} events")

        browser.close()


if __name__ == "__main__":
    scrape_spark_arena()

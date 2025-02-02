import time
from datetime import date

import pandas as pd
from dateutil import parser
from playwright.sync_api import sync_playwright


def scrape_evvnt():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        base_url = "https://evvnt.com"
        page.goto(f"{base_url}/events")

        # Wait for the initial content to load.
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Set your scroll parameters
        scroll_pause_time = 2
        scroll_limit = 5
        scroll_count = 0

        previous_height = page.evaluate("document.body.scrollHeight")

        while scroll_count < scroll_limit:
            # Scroll down to the bottom of the page
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(scroll_pause_time)

            # Calculate new scroll height and compare with the previous height
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == previous_height:
                print("No new content loaded.")
                break
            previous_height = new_height
            scroll_count += 1
            print(f"Scrolled {scroll_count} time(s), new scroll height: {new_height}")

        # Once scrolling is complete, extract event cards.
        events = []
        event_cards = page.query_selector_all("div.block")
        print(f"Found {len(event_cards)} event cards")

        current_year = date.today().year

        for card in event_cards:
            try:
                title_el = card.query_selector("h3")
                title = title_el.inner_text().strip() if title_el else "N/A"
            except Exception:
                print("Warning: Could not find event title")
                title = "N/A"
                continue

            try:
                date_el = card.query_selector("div.-mt-1 > span")
                raw_date = date_el.inner_text().strip() if date_el else ""
                date_str = " ".join(raw_date.split()[1:]) + f" {current_year}"
                event_date = parser.parse(date_str, dayfirst=True).date().isoformat()
            except Exception as e:
                print(f"Date parsing failed for '{raw_date}': {e}")
                event_date = "N/A"

            events.append({"title": title, "date": event_date})

        df = pd.DataFrame(events)
        df.to_csv("data/evvnt.csv", index=False)
        browser.close()


if __name__ == "__main__":
    scrape_evvnt()

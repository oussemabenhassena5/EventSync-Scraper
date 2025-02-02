import time
from datetime import date
from urllib.parse import urljoin

import pandas as pd
from dateutil import parser
from playwright.sync_api import sync_playwright


def scrape_evvnt():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        base_url = "https://evvnt.com/events"
        page.goto(base_url)

        # Wait for the initial content to load.
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # Set your scroll parameters
        scroll_pause_time = 2
        scroll_limit = 10
        scroll_count = 0

        previous_height = page.evaluate("document.body.scrollHeight")

        while scroll_count < scroll_limit:
            # Scroll down to the bottom of the page.
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(scroll_pause_time)

            # Calculate new scroll height and compare with the previous height.
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
                date_container = card.query_selector("div.ml-0")
                if date_container:
                    # Replace newline characters with spaces.
                    raw_date = date_container.inner_text().replace("\n", " ").strip()
                else:
                    raw_date = ""

                # Normalize the raw date for comparison.
                raw_date_lower = raw_date.lower()

                # If raw_date is empty, default to today's date.
                if not raw_date:
                    event_date = date.today()
                elif "today" in raw_date_lower:
                    # Case: "Today" (in any case)
                    event_date = date.today()
                elif "-" in raw_date:
                    # Case: a date range, e.g. "FEB 2 - 6" or "JAN 30 - MAR 3"
                    # Use the first date in the range.
                    start_date_str = raw_date.split("-")[0].strip()
                    # Append the year if not already present.
                    if any(char.isdigit() for char in start_date_str) is False:
                        start_date_str = f"{start_date_str} {current_year}"
                    event_date = parser.parse(start_date_str, dayfirst=False).date()
                else:
                    # Case: a single date, e.g. "FEB 5"
                    event_date = parser.parse(
                        f"{raw_date} {current_year}", dayfirst=False
                    ).date()

                # print(f"Raw date: '{raw_date}' parsed as: {event_date}")
            except Exception as e:
                print(f"Date parsing failed for '{raw_date}': {e}")
                event_date = "N/A"

            try:
                rel_url = card.query_selector("a").get_attribute("href")
                full_url = urljoin(base_url, rel_url)
            except Exception:
                print("Warning: Could not find event URL")
                full_url = "N/A"
                continue
            try:
                image_url = card.query_selector("img").get_attribute("src")
            except Exception:
                print("Warning: Could not find image URL")
                full_url = "N/A"
                continue
            # Extract time, location, and price from the list.
            try:
                # Locate the ul element with class "font-light" (or any unique identifier)
                ul_element = card.query_selector("ul.font-light")
                if ul_element:
                    # Get all li elements under the ul.
                    li_elements = ul_element.query_selector_all("li")
                    # Default values if any item is missing.
                    event_time = "N/A"
                    location = "N/A"
                    price = "N/A"
                    if len(li_elements) >= 1:
                        event_time = li_elements[0].inner_text().strip()
                    if len(li_elements) >= 2:
                        location = li_elements[1].inner_text().strip()
                    if len(li_elements) >= 3:
                        price = li_elements[2].inner_text().strip()
                else:
                    event_time, location, price = "N/A", "N/A", "N/A"
            except Exception as e:
                print("Error extracting event info:", e)
                event_time, location, price = "N/A", "N/A", "N/A"

            events.append(
                {
                    "Title": title,
                    "Event Date": event_date,
                    "Time": event_time,
                    "Location": location,
                    "Price": price,
                    "URL": full_url,
                    "Image URL": image_url,
                }
            )

        df = pd.DataFrame(events)
        df.to_csv("data/evvnt.csv", index=False)
        browser.close()


if __name__ == "__main__":
    scrape_evvnt()

from playwright.sync_api import sync_playwright
import pandas as pd


def scrape_spark_arena():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(
            headless=False
        )  # Set headless=False to SEE the browser
        page = browser.new_page()
        page.goto("https://www.sparkarena.co.nz/all-events")

        # Let’s PAUSE here and INSPECT the page
        input("Press Enter after inspecting elements in the browser...")

        # (We’ll add scraping logic next)

        browser.close()


if __name__ == "__main__":
    scrape_spark_arena()

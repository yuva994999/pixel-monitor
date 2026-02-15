import time
import os
import logging
import requests

from playwright.sync_api import sync_playwright

# ======================
# TELEGRAM CONFIG
# ======================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

CHAT_IDS = [
    "636892672",
    "276569960",
    "1687855096"
]

# ======================
# WEBSITE
# ======================

URL = "https://www.usedproducts.nl/Google-Pixel-c185273001/"

CHECK_INTERVAL = 1800

TARGET_MODELS = [
    "pixel 10 pro xl",
    "pixel 10 pro",
    "pixel 9 pro xl",
    "pixel 9 pro",
    "pixel 9",
    "pixel 9a"
]

seen = set()

# ======================
# LOGGING
# ======================

logging.basicConfig(level=logging.INFO)

# ======================
# TELEGRAM
# ======================

def send(msg):

    for chat_id in CHAT_IDS:

        try:

            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data={"chat_id": chat_id, "text": msg}
            )

            logging.info(f"Sent alert to {chat_id}")

        except Exception as e:

            logging.error(e)

# ======================
# FILTER
# ======================

def is_target(title):

    title = title.lower()

    return any(model in title for model in TARGET_MODELS)

# ======================
# SCRAPER
# ======================

def scrape(page):

    page.goto(URL)

    page.wait_for_timeout(5000)

    products = page.query_selector_all(".grid-product__wrap-inner")

    logging.info(f"Found {len(products)} products")

    for product in products:

        try:

            title = product.query_selector(
                ".grid-product__title-inner"
            ).inner_text().strip()

            if not is_target(title):
                continue

            price = product.query_selector(
                ".grid-product__price-value"
            ).inner_text().strip()

            link = product.query_selector(
                "a.grid-product__title"
            ).get_attribute("href")

            full_link = f"https://www.usedproducts.nl{link}"

            if full_link in seen:
                continue

            seen.add(full_link)

            logging.info(f"FOUND: {title} {price}")

            send(f"🔥 Pixel Found\n\n{title}\n{price}\n{full_link}")

        except:
            continue

# ======================
# MAIN LOOP
# ======================

def main():

    send("Pixel monitor started")

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page()

        while True:

            scrape(page)

            logging.info("Sleeping...")

            time.sleep(CHECK_INTERVAL)

# ======================

main()

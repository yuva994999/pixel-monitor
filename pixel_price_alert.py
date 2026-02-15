import os
import time
import logging
import requests

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

from webdriver_manager.chrome import ChromeDriverManager

# =====================================
# TELEGRAM CONFIG
# =====================================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

CHAT_IDS = [
    "636892672",
    "276569960",
    "1687855096"
]

# =====================================
# WEBSITE CONFIG
# =====================================

URL = "https://www.usedproducts.nl/Google-Pixel-c185273001/"

TARGET_MIN = 0
TARGET_MAX = 750

CHECK_INTERVAL = 1800

TARGET_MODELS = [
    "pixel 10 pro xl",
    "pixel 10 pro",
    "pixel 10",
    "pixel 9 pro xl",
    "pixel 9 pro",
    "pixel 9",
    "pixel 9a"
]

seen_links = set()

# =====================================
# LOGGING
# =====================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)

# =====================================
# TELEGRAM FUNCTION
# =====================================

def send_telegram(message):

    for chat_id in CHAT_IDS:

        try:

            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                data={"chat_id": chat_id, "text": message},
                timeout=10
            )

            logging.info(f"Alert sent to {chat_id}")

        except Exception as e:

            logging.error(e)

# =====================================
# MODEL FILTER
# =====================================

def is_target_model(title):

    title_lower = title.lower()

    return any(model in title_lower for model in TARGET_MODELS)

# =====================================
# SCRAPER
# =====================================

def scrape(driver):

    logging.info("Loading Pixel category page...")

    driver.get(URL)

    time.sleep(5)

    products = driver.find_elements(
        By.CSS_SELECTOR,
        ".grid-product__wrap-inner"
    )

    logging.info(f"Found {len(products)} products")

    for product in products:

        try:

            title = product.find_element(
                By.CSS_SELECTOR,
                ".grid-product__title-inner"
            ).text.strip()

            if not is_target_model(title):
                continue

            price_text = product.find_element(
                By.CSS_SELECTOR,
                ".grid-product__price-value"
            ).text.strip()

            price = float(
                price_text.replace("€", "").replace(",", ".")
            )

            link = product.find_element(
                By.CSS_SELECTOR,
                "a.grid-product__title"
            ).get_attribute("href")

            # Prevent duplicate alerts
            if link in seen_links:
                continue

            seen_links.add(link)

            logging.info(f"TARGET FOUND: {title} → €{price}")

            if TARGET_MIN <= price <= TARGET_MAX:

                message = (
                    f"🔥 PIXEL DEAL FOUND\n\n"
                    f"{title}\n"
                    f"€{price}\n\n"
                    f"{link}"
                )

                send_telegram(message)

        except Exception as e:

            logging.error(e)

# =====================================
# MAIN LOOP
# =====================================

def main():

    logging.info("Pixel monitor started")

    send_telegram("Pixel monitor started")
    options = Options()

    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")



    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    while True:

        scrape(driver)

        logging.info(f"Sleeping {CHECK_INTERVAL} seconds...\n")

        time.sleep(CHECK_INTERVAL)

# =====================================

if __name__ == "__main__":
    main()

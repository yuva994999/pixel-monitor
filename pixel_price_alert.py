import os
import requests
import time
import logging

# ======================
# CONFIGURATION
# ======================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

CHAT_IDS = [
    "636892672",
    "276569960",
    "1687855096"
]

CHECK_INTERVAL = 300  # seconds

TYPESENSE_URL = "https://search-api.usedproducts.nl/collections/site_687f817e04331_usedproducts/documents/search"

API_KEY = "6XZnCsZKtLKq8PFHAwBVWl7HM1jP4NeX"

TARGET_MODELS = [
    "pixel 10 pro xl",
    "pixel 10 pro",
    "pixel 10",
    "pixel 9 pro xl",
    "pixel 9 pro",
    "pixel 9",
    "pixel 9a"
]

BASE_URL = "https://www.usedproducts.nl"

seen = set()

MAX_PAGES = 10  # optimization (Pixel phones appear in first few pages)

# ======================
# LOGGING
# ======================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ======================
# TELEGRAM ALERT
# ======================

def send_alert(message):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    for chat_id in CHAT_IDS:

        try:

            requests.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": message
                },
                timeout=10
            )

            logging.info(f"Alert sent to {chat_id}")

        except Exception as e:

            logging.error(e)

# ======================
# BUILD CORRECT PRODUCT LINK
# ======================

def build_link(name, product_id):

    slug = name.replace(" ", "-")

    return f"{BASE_URL}/{slug}-p{product_id}"

# ======================
# CHECK TARGET DEVICE
# ======================

def is_target(name):

    name = name.lower()

    return any(model in name for model in TARGET_MODELS)

# ======================
# SCRAPER
# ======================

def scrape():

    logging.info("Checking Pixel category...")

    headers = {
        "X-TYPESENSE-API-KEY": API_KEY
    }

    page = 1
    per_page = 100

    total_found = 0

    while page <= MAX_PAGES:

        params = {
            "q": "Google Pixel",
            "query_by": "name",
            "per_page": per_page,
            "page": page
        }

        try:

            r = requests.get(
                TYPESENSE_URL,
                headers=headers,
                params=params,
                timeout=20
            )

            data = r.json()

        except Exception as e:

            logging.error(e)
            return

        hits = data.get("hits", [])

        if not hits:
            break

        logging.info(f"Page {page}: {len(hits)} products")

        page_found = 0

        for hit in hits:

            doc = hit["document"]

            name = doc.get("name", "")
            price = doc.get("price", "")
            product_id = doc.get("id", "")
            categories = doc.get("categories", [])

            # Only Pixel category
            if not any("Google Pixel" in cat for cat in categories):
                continue

            if not is_target(name):
                continue

            link = build_link(name, product_id)

            if link in seen:
                continue

            seen.add(link)

            total_found += 1
            page_found += 1

            logging.info(f"FOUND: {name} → €{price}")

            message = (
                f"🔥 Pixel Deal Found\n\n"
                f"{name}\n"
                f"€{price}\n"
                f"{link}"
            )

            send_alert(message)

        # Stop early if no results in page
        if page_found == 0 and page > 3:
            break

        page += 1

    logging.info(f"Total new Pixel devices found: {total_found}")

# ======================
# MAIN LOOP
# ======================

def main():

    logging.info("Pixel monitor started")

    send_alert("✅ Pixel monitor started")

    while True:

        scrape()

        logging.info(f"Sleeping {CHECK_INTERVAL} seconds...")

        time.sleep(CHECK_INTERVAL)

# ======================

if __name__ == "__main__":
    main()

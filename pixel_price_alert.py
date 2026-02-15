import os
import requests
import time
import logging

BOT_TOKEN = os.environ.get("BOT_TOKEN")

CHAT_IDS = [
    "636892672",
    "276569960",
    "1687855096"
]

CHECK_INTERVAL = 300

TYPESENSE_URL = "https://search-api.usedproducts.nl/collections/site_687f817e04331_usedproducts/documents/search"

API_KEY = "6XZnCsZKtLKq8PFHAwBVWl7HM1jP4NeX"

TARGET_MODELS = [
    "pixel 10 pro xl",
    "pixel 10 pro",
    "pixel 10"
    "pixel 9 pro xl",
    "pixel 9 pro",
    "pixel 9a",
    "pixel 9"
]

seen = set()

logging.basicConfig(level=logging.INFO)

# ======================
# TELEGRAM ALERT
# ======================

def send_alert(message):

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    for chat_id in CHAT_IDS:

        try:
            requests.post(url, json={"chat_id": chat_id, "text": message})
            logging.info(f"Alert sent to {chat_id}")

        except Exception as e:
            logging.error(e)

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

    # First request to get total count
    params = {
        "q": "Google Pixel",
        "query_by": "name",
        "per_page": per_page,
        "page": 1
    }

    r = requests.get(TYPESENSE_URL, headers=headers, params=params)
    data = r.json()

    total_products = data.get("found", 0)

    max_pages = (total_products // per_page) + 1

    logging.info(f"Total products in database: {total_products}")
    logging.info(f"Total pages: {max_pages}")

    while page <= max_pages:

        params["page"] = page

        r = requests.get(TYPESENSE_URL, headers=headers, params=params)
        data = r.json()

        hits = data.get("hits", [])

        logging.info(f"Page {page}: {len(hits)} products")

        for hit in hits:

            doc = hit["document"]

            name = doc.get("name", "")
            price = doc.get("price", "")
            url = doc.get("url", "")
            categories = doc.get("categories", [])

            # Only Pixel category
            if not any("Google Pixel" in cat for cat in categories):
                continue

            name_lower = name.lower()

            if not any(model in name_lower for model in TARGET_MODELS):
                continue

            link = f"https://www.usedproducts.nl{url}"

            if link in seen:
                continue

            seen.add(link)

            total_found += 1

            logging.info(f"FOUND: {name} → €{price}")

            send_alert(
                f"🔥 Pixel Found\n\n{name}\n€{price}\n{link}"
            )

        page += 1

    logging.info(f"Total Pixel devices found: {total_found}")

# ======================
# MAIN LOOP
# ======================

def main():

    logging.info("Pixel monitor started")

    send_alert("Pixel monitor started")

    while True:

        scrape()

        logging.info("Sleeping...")

        time.sleep(CHECK_INTERVAL)

# ======================

if __name__ == "__main__":
    main()

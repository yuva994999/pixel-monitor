import os
import requests
import time
import logging
from datetime import datetime, timedelta

# ======================
# CONFIGURATION
# ======================

BOT_TOKEN = os.environ.get("BOT_TOKEN")

CHAT_IDS = os.getenv("CHAT_IDS", "").split(",")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not set")

if not CHAT_IDS or CHAT_IDS == [""]:
    raise Exception("CHAT_IDS not set")

CHECK_INTERVAL = 300  # check every 5 minutes
FULL_REPORT_INTERVAL = 43200  # 2 hours

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

MAX_PAGES = 10

# Track seen deals
seen_ever = set()

# Track last full report time
last_full_report = datetime.min

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
# BUILD PRODUCT LINK
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
# GET ALL PIXEL DEALS
# ======================

def get_all_pixel_deals():

    headers = {
        "X-TYPESENSE-API-KEY": API_KEY
    }

    page = 1
    deals = []

    while page <= MAX_PAGES:

        params = {
            "q": "Google Pixel",
            "query_by": "name",
            "per_page": 100,
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
            break

        hits = data.get("hits", [])

        if not hits:
            break

        for hit in hits:

            doc = hit["document"]

            name = doc.get("name", "")
            price = doc.get("price", "")
            product_id = doc.get("id", "")
            categories = doc.get("categories", [])

            if not any("Google Pixel" in cat for cat in categories):
                continue

            if not is_target(name):
                continue

            link = build_link(name, product_id)

            deals.append({
                "name": name,
                "price": price,
                "link": link
            })

        page += 1

    return deals

# ======================
# MAIN SCRAPER LOGIC
# ======================

def scrape():

    global last_full_report

    logging.info("Checking Pixel deals...")

    deals = get_all_pixel_deals()

    now = datetime.now()

    # ======================
    # SEND FULL REPORT EVERY 2 HOURS
    # ======================

    if (now - last_full_report).total_seconds() >= FULL_REPORT_INTERVAL:

        logging.info("Sending FULL REPORT")

        message = "📱 FULL PIXEL DEAL LIST\n\n"

        for deal in deals:

            message += (
                f"{deal['name']}\n"
                f"€{deal['price']}\n"
                f"{deal['link']}\n\n"
            )

        send_alert(message)

        last_full_report = now

    # ======================
    # SEND INSTANT ALERT FOR NEW DEALS
    # ======================

    for deal in deals:

        if deal["link"] not in seen_ever:

            seen_ever.add(deal["link"])

            logging.info(f"NEW DEAL: {deal['name']}")

            message = (
                f"🔥 NEW PIXEL DEAL\n\n"
                f"{deal['name']}\n"
                f"€{deal['price']}\n"
                f"{deal['link']}"
            )

            send_alert(message)

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


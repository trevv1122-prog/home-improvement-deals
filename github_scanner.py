import csv
from datetime import datetime, date
import json
import logging
import os
import sys

from scrapers.home_depot import HomeDepotScraper
from scrapers.lowes import LowesScraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("GitHubScanner")


def run_cloud_scan(output_dir="."):
    today_str = date.today().isoformat()
    now_str = datetime.now().isoformat()
    logger.info(f"Starting GitHub Actions daily deal scan at {now_str}")

    deals_json_path = os.path.join(output_dir, "deals.json")
    prev_deals = {}
    if os.path.exists(deals_json_path):
        try:
            with open(deals_json_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
                for item in raw:
                    key = f"{item['retailer']}:{item['sku']}"
                    prev_deals[key] = item
            logger.info(f"Loaded {len(prev_deals)} previous deal records for diffing.")
        except Exception as e:
            logger.warning(f"Could not parse existing deals.json: {e}")

    all_scraped = []

    try:
        hd = HomeDepotScraper(store_id="6549")
        hd_items = hd.scrape_savings_and_clearance()
        all_scraped.extend(hd_items)
        logger.info(f"Scraped {len(hd_items)} Home Depot items.")
    except Exception as e:
        logger.error(f"Home Depot scraper error: {e}")

    try:
        lowes = LowesScraper(store_id="2498")
        lowes_items = lowes.scrape_savings_and_clearance()
        all_scraped.extend(lowes_items)
        logger.info(f"Scraped {len(lowes_items)} Lowe's items.")
    except Exception as e:
        logger.error(f"Lowe's scraper error: {e}")

    compiled_deals = []
    new_today_count = 0
    price_drops_count = 0

    for idx, item in enumerate(all_scraped, start=1):
        key = f"{item.retailer}:{item.sku}"
        prev = prev_deals.get(key)

        is_new = False
        price_drop = False
        first_spotted = now_str

        if prev:
            first_spotted = prev.get("first_detected", now_str)
            if item.sale_price < prev.get("sale_price", item.sale_price):
                price_drop = True
                price_drops_count += 1
            if first_spotted.startswith(today_str):
                is_new = True
                new_today_count += 1
        else:
            is_new = True
            new_today_count += 1

        deal_dict = {
            "id": idx,
            "retailer": item.retailer,
            "sku": item.sku,
            "title": item.title,
            "brand": item.brand,
            "category": item.category,
            "sub_category": item.sub_category,
            "regular_price": item.regular_price,
            "sale_price": item.sale_price,
            "discount_pct": item.discount_pct,
            "dollar_savings": item.dollar_savings,
            "in_stock": item.in_stock,
            "rating": item.rating,
            "review_count": item.review_count,
            "is_clearance": item.is_clearance,
            "is_new_today": is_new,
            "price_drop": price_drop,
            "url": item.url,
            "image_url": item.image_url,
            "store_id": item.store_id,
            "first_detected": first_spotted,
            "last_updated": now_str,
        }
        compiled_deals.append(deal_dict)

    compiled_deals.sort(key=lambda x: x["discount_pct"], reverse=True)

    with open(deals_json_path, "w", encoding="utf-8") as f:
        json.dump(compiled_deals, f, indent=2)
    logger.info(f"Saved {len(compiled_deals)} deals to {deals_json_path}")

    deals_csv_path = os.path.join(output_dir, "deals.csv")
    if compiled_deals:
        fieldnames = [
            "retailer", "sku", "brand", "title", "category", "sub_category",
            "regular_price", "sale_price", "discount_pct", "dollar_savings",
            "is_clearance", "is_new_today", "rating", "url"
        ]
        with open(deals_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(compiled_deals)
        logger.info(f"Saved CSV export to {deals_csv_path}")

    total_savings = sum(d["dollar_savings"] for d in compiled_deals)
    avg_discount = (sum(d["discount_pct"] for d in compiled_deals) / len(compiled_deals)) if compiled_deals else 0.0
    clearance_count = sum(1 for d in compiled_deals if d["is_clearance"])

    summary = {
        "last_updated": now_str,
        "scan_date": today_str,
        "total_deals": len(compiled_deals),
        "new_deals_today": new_today_count,
        "clearance_count": clearance_count,
        "price_drops_count": price_drops_count,
        "average_discount_pct": round(avg_discount, 1),
        "total_potential_savings": round(total_savings, 2),
    }

    summary_path = os.path.join(output_dir, "deals_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info("Cloud scan completed successfully.")
    return summary


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    run_cloud_scan(out_dir)

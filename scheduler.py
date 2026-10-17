"""
Morning Scan Scheduler Module.
Executes automated morning scans (default 06:00 AM daily), diffs deals against the database,
identifies 'New Today' bargains, and sends optional webhook notifications.
"""

import argparse
from datetime import datetime, time as dtime, timedelta
import json
import logging
import os
import sys
import time
import urllib.request

from scrapers.home_depot import HomeDepotScraper
from scrapers.lowes import LowesScraper
from database import DealDatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("MorningScheduler")


class DealScannerDaemon:
    def __init__(
        self,
        db: DealDatabase,
        scan_time_str: str = "06:00",
        webhook_url: str = None,
        hd_store_id: str = "6549",
        lowes_store_id: str = "2498"
    ):
        self.db = db
        self.scan_time_str = scan_time_str  # "HH:MM" 24hr format
        self.webhook_url = webhook_url
        self.hd_store_id = hd_store_id
        self.lowes_store_id = lowes_store_id

    def run_morning_scan(self) -> dict:
        """
        Execute full morning scan across Home Depot and Lowe's:
        1. Query savings and clearance departments
        2. Deduplicate and categorize items
        3. Match against database to identify new deals and price drops
        4. Record price history
        5. Dispatch notification summary
        """
        logger.info("=====================================================")
        logger.info(f"STARTING MORNING DEAL SCAN: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=====================================================")

        scan_id = self.db.start_scan_log()
        all_deals = []

        try:
            # 1. Scrape Home Depot
            logger.info(f"Scanning Home Depot (Store #{self.hd_store_id})...")
            hd_scraper = HomeDepotScraper(store_id=self.hd_store_id)
            hd_deals = hd_scraper.scrape_savings_and_clearance()
            all_deals.extend(hd_deals)
            logger.info(f"Retrieved {len(hd_deals)} Home Depot clearance and sale deals.")

            # 2. Scrape Lowe's
            logger.info(f"Scanning Lowe's (Store #{self.lowes_store_id})...")
            lowes_scraper = LowesScraper(store_id=self.lowes_store_id)
            lowes_deals = lowes_scraper.scrape_savings_and_clearance()
            all_deals.extend(lowes_deals)
            logger.info(f"Retrieved {len(lowes_deals)} Lowe's clearance and sale deals.")

            # 3. Process deals in Database (diffing and price history)
            logger.info("Synchronizing with database and checking for newly listed deals...")
            sync_stats = self.db.save_scan_results(all_deals)

            summary = {
                "scan_id": scan_id,
                "timestamp": datetime.now().isoformat(),
                "total_items_scraped": len(all_deals),
                "new_deals_today": sync_stats["new_deals"],
                "price_drops_detected": sync_stats["price_drops"],
                "home_depot_count": len(hd_deals),
                "lowes_count": len(lowes_deals),
            }

            self.db.finish_scan_log(
                scan_id=scan_id,
                total_found=len(all_deals),
                new_count=sync_stats["new_deals"],
                drops_count=sync_stats["price_drops"],
                summary=summary
            )

            logger.info("=====================================================")
            logger.info(f"MORNING SCAN COMPLETE: {sync_stats['new_deals']} new deals found, {sync_stats['price_drops']} price drops.")
            logger.info("=====================================================")

            # 4. Send Webhook Notification (Slack/Discord/Generic)
            if self.webhook_url:
                self.send_webhook_alert(summary)

            return summary

        except Exception as e:
            logger.error(f"Fatal error during morning scan: {e}", exc_info=True)
            return {"error": str(e)}

    def send_webhook_alert(self, summary: dict):
        """Send notification webhook to Discord/Slack."""
        try:
            payload = {
                "text": (
                    f"☀️ *Home Improvement Morning Scan Completed!*\n"
                    f"• Total Deals: {summary['total_items_scraped']}\n"
                    f"• 🆕 New Deals Today: {summary['new_deals_today']}\n"
                    f"• 📉 Price Drops: {summary['price_drops_detected']}\n"
                    f"• Home Depot: {summary['home_depot_count']} | Lowe's: {summary['lowes_count']}"
                )
            }
            req = urllib.request.Request(
                self.webhook_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                logger.info(f"Webhook alert dispatched: HTTP {resp.status}")
        except Exception as e:
            logger.warning(f"Failed to deliver webhook notification: {e}")

    def start_daemon(self):
        """Run continuous daemon waiting for morning scan time."""
        target_h, target_m = map(int, self.scan_time_str.split(":"))
        logger.info(f"Morning Scan Daemon started. Configured to run every morning at {self.scan_time_str} local time.")

        while True:
            now = datetime.now()
            # Calculate next target time
            next_run = now.replace(hour=target_h, minute=target_m, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)

            wait_seconds = (next_run - now).total_seconds()
            logger.info(f"Next morning scan scheduled for {next_run.strftime('%Y-%m-%d %H:%M:%S')} (in {round(wait_seconds/3600, 1)} hours).")

            # Sleep until morning target
            time.sleep(wait_seconds)
            self.run_morning_scan()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Morning Deal Scanner Runner")
    parser.add_argument("--run-now", action="store_true", help="Execute scan immediately")
    parser.add_argument("--time", default="06:00", help="Morning scan time in HH:MM format (default: 06:00)")
    parser.add_argument("--webhook", default=None, help="Webhook URL for deal notifications")
    args = parser.parse_args()

    db = DealDatabase()
    daemon = DealScannerDaemon(db=db, scan_time_str=args.time, webhook_url=args.webhook)

    if args.run_now:
        res = daemon.run_morning_scan()
        print("\nScan Result Summary:")
        print(json.dumps(res, indent=2))
    else:
        daemon.start_daemon()

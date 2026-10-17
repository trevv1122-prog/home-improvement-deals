"""
Database Module for Deal Storage and Tracking.
Manages SQLite storage, price drop detection, daily diffing ('New Today' tags),
and export operations.
"""

import csv
import json
import logging
import os
import sqlite3
from datetime import datetime, date
from typing import List, Dict, Any, Optional

from scrapers.base import ScrapedDeal

logger = logging.getLogger("Database")

DEFAULT_DB_PATH = os.environ.get("DEAL_DB_PATH", os.path.join(os.path.dirname(__file__), "deals.db"))


class DealDatabase:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        # Test if the target path's filesystem supports SQLite locking
        try:
            test_conn = sqlite3.connect(self.db_path)
            test_conn.execute("CREATE TABLE IF NOT EXISTS _fs_check (id INT);")
            test_conn.close()
        except sqlite3.OperationalError:
            # Fallback for network/FUSE mounted directories lacking POSIX advisory locks
            self.db_path = "/tmp/home_improvement_deals.db"
            logger.info(f"Target directory lacks SQLite lock support. Using local database path: {self.db_path}")

        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database schema with indexes for fast category and retailer queries."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Main deals table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS deals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    retailer TEXT NOT NULL,
                    sku TEXT NOT NULL,
                    title TEXT NOT NULL,
                    brand TEXT,
                    category TEXT NOT NULL,
                    sub_category TEXT,
                    raw_category TEXT,
                    regular_price REAL,
                    sale_price REAL NOT NULL,
                    discount_pct REAL NOT NULL,
                    dollar_savings REAL NOT NULL,
                    in_stock INTEGER DEFAULT 1,
                    rating REAL DEFAULT 0.0,
                    review_count INTEGER DEFAULT 0,
                    url TEXT NOT NULL,
                    image_url TEXT,
                    is_clearance INTEGER DEFAULT 0,
                    store_id TEXT DEFAULT 'ONLINE',
                    first_detected TEXT NOT NULL,
                    last_updated TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    is_new_today INTEGER DEFAULT 1,
                    UNIQUE(retailer, sku, store_id)
                )
            """)

            # Price history tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS price_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    deal_id INTEGER,
                    retailer TEXT NOT NULL,
                    sku TEXT NOT NULL,
                    price REAL NOT NULL,
                    discount_pct REAL NOT NULL,
                    recorded_at TEXT NOT NULL,
                    FOREIGN KEY(deal_id) REFERENCES deals(id)
                )
            """)

            # Morning scan execution history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scan_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    scan_date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    total_deals_found INTEGER DEFAULT 0,
                    new_deals_count INTEGER DEFAULT 0,
                    price_drops_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'RUNNING',
                    summary_json TEXT
                )
            """)

            # Indexes for instant search & filtering
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_deals_cat ON deals(category);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_deals_retailer ON deals(retailer);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_deals_discount ON deals(discount_pct);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_deals_new ON deals(is_new_today);")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_deals_active ON deals(is_active);")
            conn.commit()

    def start_scan_log(self) -> int:
        """Start a new morning scan log entry."""
        today_str = date.today().isoformat()
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scan_history (scan_date, start_time, status)
                VALUES (?, ?, 'RUNNING')
            """, (today_str, now_str))
            conn.commit()
            return cursor.lastrowid

    def finish_scan_log(self, scan_id: int, total_found: int, new_count: int, drops_count: int, summary: dict):
        """Complete the scan log with performance counts."""
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE scan_history
                SET end_time = ?, total_deals_found = ?, new_deals_count = ?,
                    price_drops_count = ?, status = 'COMPLETED', summary_json = ?
                WHERE id = ?
            """, (now_str, total_found, new_count, drops_count, json.dumps(summary), scan_id))
            conn.commit()

    def save_scan_results(self, deals: List[ScrapedDeal]) -> Dict[str, int]:
        """
        Process scraped items against existing database records:
        - Detect new deals (set is_new_today = 1)
        - Detect price drops compared to previous scan
        - Record price history point
        """
        today_str = date.today().isoformat()
        now_str = datetime.now().isoformat()

        new_deals_count = 0
        price_drops_count = 0
        total_processed = len(deals)

        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Reset previous 'is_new_today' flags from past days
            cursor.execute("""
                UPDATE deals SET is_new_today = 0
                WHERE first_detected < ?
            """, (today_str,))

            # Reset active flags for retailers scanned
            retailers_in_batch = set(d.retailer for d in deals)
            for ret in retailers_in_batch:
                cursor.execute("UPDATE deals SET is_active = 0 WHERE retailer = ?", (ret,))

            for item in deals:
                # Check if item already exists
                cursor.execute("""
                    SELECT id, sale_price, first_detected
                    FROM deals
                    WHERE retailer = ? AND sku = ? AND store_id = ?
                """, (item.retailer, item.sku, item.store_id))
                existing = cursor.fetchone()

                if existing:
                    deal_id = existing["id"]
                    prev_price = existing["sale_price"]
                    first_detected = existing["first_detected"]
                    is_new = 1 if first_detected.startswith(today_str) else 0

                    if item.sale_price < prev_price:
                        price_drops_count += 1
                        cursor.execute("""
                            INSERT INTO price_history (deal_id, retailer, sku, price, discount_pct, recorded_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (deal_id, item.retailer, item.sku, item.sale_price, item.discount_pct, now_str))

                    cursor.execute("""
                        UPDATE deals SET
                            title = ?, brand = ?, category = ?, sub_category = ?, raw_category = ?,
                            regular_price = ?, sale_price = ?, discount_pct = ?, dollar_savings = ?,
                            in_stock = ?, rating = ?, review_count = ?, url = ?, image_url = ?,
                            is_clearance = ?, last_updated = ?, is_active = 1, is_new_today = ?
                        WHERE id = ?
                    """, (
                        item.title, item.brand, item.category, item.sub_category, item.raw_category,
                        item.regular_price, item.sale_price, item.discount_pct, item.dollar_savings,
                        1 if item.in_stock else 0, item.rating, item.review_count, item.url, item.image_url,
                        1 if item.is_clearance else 0, now_str, is_new, deal_id
                    ))
                else:
                    new_deals_count += 1
                    cursor.execute("""
                        INSERT INTO deals (
                            retailer, sku, title, brand, category, sub_category, raw_category,
                            regular_price, sale_price, discount_pct, dollar_savings, in_stock,
                            rating, review_count, url, image_url, is_clearance, store_id,
                            first_detected, last_updated, is_active, is_new_today
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)
                    """, (
                        item.retailer, item.sku, item.title, item.brand, item.category, item.sub_category,
                        item.raw_category, item.regular_price, item.sale_price, item.discount_pct,
                        item.dollar_savings, 1 if item.in_stock else 0, item.rating, item.review_count,
                        item.url, item.image_url, 1 if item.is_clearance else 0, item.store_id,
                        now_str, now_str
                    ))
                    new_deal_id = cursor.lastrowid
                    cursor.execute("""
                        INSERT INTO price_history (deal_id, retailer, sku, price, discount_pct, recorded_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (new_deal_id, item.retailer, item.sku, item.sale_price, item.discount_pct, now_str))

            conn.commit()

        return {
            "total_processed": total_processed,
            "new_deals": new_deals_count,
            "price_drops": price_drops_count
        }

    def get_deals(
        self,
        category: Optional[str] = None,
        retailer: Optional[str] = None,
        min_discount: float = 0.0,
        only_new: bool = False,
        only_clearance: bool = False,
        only_in_stock: bool = False,
        search_query: Optional[str] = None,
        sort_by: str = "discount_desc",
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Query deals with comprehensive filtering."""
        query = "SELECT * FROM deals WHERE is_active = 1"
        params = []

        if category and category != "All":
            query += " AND category = ?"
            params.append(category)

        if retailer and retailer != "All":
            query += " AND retailer = ?"
            params.append(retailer)

        if min_discount > 0:
            query += " AND discount_pct >= ?"
            params.append(min_discount)

        if only_new:
            query += " AND is_new_today = 1"

        if only_clearance:
            query += " AND is_clearance = 1"

        if only_in_stock:
            query += " AND in_stock = 1"

        if search_query:
            query += " AND (title LIKE ? OR brand LIKE ? OR sku LIKE ?)"
            term = f"%{search_query}%"
            params.extend([term, term, term])

        sort_clauses = {
            "discount_desc": "discount_pct DESC",
            "savings_desc": "dollar_savings DESC",
            "price_asc": "sale_price ASC",
            "price_desc": "sale_price DESC",
            "rating_desc": "rating DESC",
            "newest": "id DESC"
        }
        order_clause = sort_clauses.get(sort_by, "discount_pct DESC")
        query += f" ORDER BY {order_clause} LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def get_stats(self) -> Dict[str, Any]:
        """Return analytics summary of tracked deals."""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM deals WHERE is_active = 1")
            total_active = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM deals WHERE is_active = 1 AND is_new_today = 1")
            total_new_today = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM deals WHERE is_active = 1 AND is_clearance = 1")
            total_clearance = cursor.fetchone()[0]

            cursor.execute("SELECT AVG(discount_pct) FROM deals WHERE is_active = 1")
            avg_discount = cursor.fetchone()[0] or 0.0

            cursor.execute("SELECT SUM(dollar_savings) FROM deals WHERE is_active = 1")
            total_savings = cursor.fetchone()[0] or 0.0

            cursor.execute("""
                SELECT category, COUNT(*) as count, AVG(discount_pct) as avg_disc
                FROM deals WHERE is_active = 1
                GROUP BY category ORDER BY count DESC
            """)
            category_counts = [dict(r) for r in cursor.fetchall()]

            cursor.execute("""
                SELECT retailer, COUNT(*) as count, AVG(discount_pct) as avg_disc
                FROM deals WHERE is_active = 1
                GROUP BY retailer
            """)
            retailer_counts = [dict(r) for r in cursor.fetchall()]

            cursor.execute("""
                SELECT * FROM scan_history ORDER BY id DESC LIMIT 1
            """)
            last_scan = cursor.fetchone()

            return {
                "total_active_deals": total_active,
                "total_new_today": total_new_today,
                "total_clearance": total_clearance,
                "average_discount_pct": round(avg_discount, 1),
                "total_potential_savings": round(total_savings, 2),
                "by_category": category_counts,
                "by_retailer": retailer_counts,
                "last_scan": dict(last_scan) if last_scan else None
            }

    def export_csv(self, output_path: str):
        """Export all active deals to CSV."""
        deals = self.get_deals(limit=10000)
        if not deals:
            return
        keys = deals[0].keys()
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(deals)

    def export_json(self, output_path: str):
        """Export all active deals to JSON."""
        deals = self.get_deals(limit=10000)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(deals, f, indent=2)

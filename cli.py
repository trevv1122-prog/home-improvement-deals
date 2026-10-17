"""
Command-Line Interface for Home Improvement Deal Tracker.
Run scans, browse deals by department, view analytics, and export datasets.
"""

import argparse
import json
import sys
from tabulate import tabulate

from database import DealDatabase
from scheduler import DealScannerDaemon


def main():
    parser = argparse.ArgumentParser(description="Home Improvement Deal Scraper CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: scan
    scan_parser = subparsers.add_parser("scan", help="Run deal scan immediately")
    scan_parser.add_argument("--store-hd", default="6549", help="Home Depot Store ID")
    scan_parser.add_argument("--store-lowes", default="2498", help="Lowe's Store ID")

    # Command: list
    list_parser = subparsers.add_parser("list", help="List active deals")
    list_parser.add_argument("--category", default=None, help="Department category filter")
    list_parser.add_argument("--retailer", choices=["All", "Home Depot", "Lowe's"], default="All")
    list_parser.add_argument("--min-discount", type=float, default=0.0, help="Minimum discount percentage")
    list_parser.add_argument("--new-only", action="store_true", help="Only show deals discovered today")
    list_parser.add_argument("--clearance", action="store_true", help="Only show clearance deals")
    list_parser.add_argument("--limit", type=int, default=20, help="Max results to display")

    # Command: stats
    subparsers.add_parser("stats", help="Display morning scan & category statistics")

    # Command: export
    export_parser = subparsers.add_parser("export", help="Export active deals to file")
    export_parser.add_argument("--format", choices=["csv", "json"], default="csv", help="File format")
    export_parser.add_argument("--output", required=True, help="Output destination file path")

    args = parser.parse_args()
    db = DealDatabase()

    if args.command == "scan":
        print(f"Triggering morning scan for Home Depot (Store #{args.store_hd}) and Lowe's (Store #{args.store_lowes})...")
        daemon = DealScannerDaemon(db, hd_store_id=args.store_hd, lowes_store_id=args.store_lowes)
        res = daemon.run_morning_scan()
        print("\nScan completed successfully!")
        print(f"Total deals scanned: {res.get('total_items_scraped')}")
        print(f"New deals added today: {res.get('new_deals_today')}")
        print(f"Price drops recorded: {res.get('price_drops_detected')}")

    elif args.command == "list":
        deals = db.get_deals(
            category=args.category,
            retailer=args.retailer if args.retailer != "All" else None,
            min_discount=args.min_discount,
            only_new=args.new_only,
            only_clearance=args.clearance,
            limit=args.limit
        )

        if not deals:
            print("No matching deals found in database. Run 'python cli.py scan' to refresh.")
            return

        table_rows = []
        for d in deals:
            badge = "🔥 NEW" if d["is_new_today"] else ("🏷️ CLR" if d["is_clearance"] else "")
            table_rows.append([
                d["retailer"],
                badge,
                d["category"],
                d["title"][:45] + ("..." if len(d["title"]) > 45 else ""),
                f"${d['regular_price']:.2f}",
                f"${d['sale_price']:.2f}",
                f"-{d['discount_pct']:.0f}%",
                f"${d['dollar_savings']:.2f}"
            ])

        headers = ["Store", "Tag", "Category", "Item Title", "Reg", "Sale", "Off", "Save"]
        print(tabulate(table_rows, headers=headers, tablefmt="rounded_grid"))
        print(f"\nShowing {len(deals)} items. Run with --limit to see more.")

    elif args.command == "stats":
        stats = db.get_stats()
        print("\n=== HOME IMPROVEMENT DEAL SCANNER ANALYTICS ===")
        print(f"Total Active Deals:      {stats['total_active_deals']}")
        print(f"Discovered Today:        {stats['total_new_today']}")
        print(f"Clearance Items:         {stats['total_clearance']}")
        print(f"Average Discount:        {stats['average_discount_pct']}%")
        print(f"Total Potential Savings: ${stats['total_potential_savings']:,.2f}")

        print("\n--- Breakdown by Department Category ---")
        cat_table = [[c["category"], c["count"], f"{c['avg_disc']:.1f}%"] for c in stats["by_category"]]
        print(tabulate(cat_table, headers=["Category", "Deal Count", "Avg Discount"], tablefmt="simple"))

        print("\n--- Breakdown by Retailer ---")
        ret_table = [[r["retailer"], r["count"], f"{r['avg_disc']:.1f}%"] for r in stats["by_retailer"]]
        print(tabulate(ret_table, headers=["Retailer", "Deal Count", "Avg Discount"], tablefmt="simple"))

    elif args.command == "export":
        if args.format == "csv":
            db.export_csv(args.output)
            print(f"Exported deals to CSV: {args.output}")
        else:
            db.export_json(args.output)
            print(f"Exported deals to JSON: {args.output}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

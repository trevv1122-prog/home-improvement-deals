"""
Lightweight REST API Server and Web Dashboard Host.
Provides JSON endpoints for deals, morning scan triggers, category filtering,
and serves the web application. Zero external dependencies required.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
import os
import urllib.parse
from database import DealDatabase
from scheduler import DealScannerDaemon

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("APIServer")

PORT = 8080
db = DealDatabase()


class DealAPIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Enable CORS
        if path == "/api/deals":
            category = query.get("category", [None])[0]
            retailer = query.get("retailer", [None])[0]
            min_disc = float(query.get("min_discount", [0.0])[0])
            new_only = query.get("new_only", ["false"])[0].lower() == "true"
            clearance = query.get("clearance", ["false"])[0].lower() == "true"
            in_stock = query.get("in_stock", ["false"])[0].lower() == "true"
            search = query.get("q", [None])[0]
            sort_by = query.get("sort", ["discount_desc"])[0]

            deals = db.get_deals(
                category=category,
                retailer=retailer,
                min_discount=min_disc,
                only_new=new_only,
                only_clearance=clearance,
                only_in_stock=in_stock,
                search_query=search,
                sort_by=sort_by,
                limit=200
            )
            self._send_json({"deals": deals, "count": len(deals)})

        elif path == "/api/stats":
            stats = db.get_stats()
            self._send_json(stats)

        elif path == "/api/scan":
            hd_store = query.get("hd_store", ["6549"])[0]
            lowes_store = query.get("lowes_store", ["2498"])[0]
            daemon = DealScannerDaemon(db, hd_store_id=hd_store, lowes_store_id=lowes_store)
            res = daemon.run_morning_scan()
            self._send_json(res)

        elif path == "/api/export":
            fmt = query.get("format", ["json"])[0]
            deals = db.get_deals(limit=5000)
            if fmt == "csv":
                self.send_response(200)
                self.send_header("Content-Type", "text/csv")
                self.send_header("Content-Disposition", "attachment; filename=deals.csv")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                if deals:
                    keys = list(deals[0].keys())
                    self.wfile.write((",".join(keys) + "\n").encode())
                    for d in deals:
                        row = [str(d.get(k, "")).replace(",", " ") for k in keys]
                        self.wfile.write((",".join(row) + "\n").encode())
            else:
                self._send_json(deals)

        else:
            # Serve index.html if exists
            index_file = os.path.join(os.path.dirname(__file__), "index.html")
            if os.path.exists(index_file):
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                with open(index_file, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()

    def _send_json(self, data: dict):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))


def run_server(port=PORT):
    server_address = ("", port)
    httpd = HTTPServer(server_address, DealAPIHandler)
    logger.info(f"Home Improvement Deal Tracker API running at http://localhost:{port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run_server()

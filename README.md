# Home Improvement Deal & Clearance Tracker
### Automated Daily Morning Scanner for Home Depot & Lowe's

An end-to-end scraper and intelligence application that continuously tracks, categorizes, and monitors sale and clearance items across **The Home Depot** and **Lowe's**. Built to run an automated morning scan every day at 06:00 AM, identify newly discounted items, track price drops, and organize deals into clean home improvement departments.

---

## Features

- **Multi-Retailer Scraping**: Scrapes Home Depot (Special Buys, Savings Center, Clearance) and Lowe's (Deals, Clearance, Daily Deals).
- **Intelligent Category Separation**: Automatically classifies every deal into 10 structured home improvement departments:
  - *Tools & Hardware*
  - *Appliances*
  - *Lawn & Garden*
  - *Electrical & Lighting*
  - *Plumbing*
  - *Building Materials*
  - *Paint & Supplies*
  - *Kitchen & Bath*
  - *Storage & Organization*
  - *Smart Home & Electronics*
- **Automated Morning Scan Engine**: Configured to run every morning at **06:00 AM** to detect fresh markdowns before inventory sells out.
- **Differential Deal & Price-Drop Tracking**:
  - Automatically flags deals discovered during today's scan as **🔥 NEW TODAY**.
  - Detects if an existing deal drops in price and logs historical snapshots.
  - Deactivates expired items when promotions end.
- **SQLite Database Architecture**: Local database (`deals.db`) with complete price history, scan run telemetry, and query indexing.
- **Rich CLI & REST API**: Query deals, filter by department, inspect analytics, trigger instant scans, and export to CSV/JSON.
- **Interactive Web App Dashboard**: Full-featured visual interface with live search, department filtering, morning scan countdown, and real-time deal inspection.

---

## Project Structure

```text
home_improvement_deal_scraper/
├── scrapers/
│   ├── base.py              # Base scraper class with retry logic & data model
│   ├── home_depot.py        # Home Depot clearance & special buy scraper
│   └── lowes.py             # Lowe's clearance & deals scraper
├── categorizer.py           # Department categorization & sub-category classifier
├── database.py              # SQLite storage, price history, and diff engine
├── scheduler.py             # Morning scan daemon & webhook alerting
├── cli.py                   # Terminal command-line tool
├── server.py                # REST API & static web server
├── cron_setup.sh            # One-click daily cron job installer
├── setup_systemd.sh         # Systemd service and timer config
├── requirements.txt         # Python dependencies
└── README.md                # Documentation
```

---

## Quick Start

### 1. Installation

```bash
cd home_improvement_deal_scraper
pip install -r requirements.txt
chmod +x cron_setup.sh setup_systemd.sh
```

### 2. Run a Deal Scan Right Now

```bash
# Run immediate scan using CLI
python cli.py scan

# Or run via scheduler
python scheduler.py --run-now
```

### 3. Browse Deals in the Terminal

```bash
# List all active deals
python cli.py list

# Filter by department category
python cli.py list --category "Tools & Hardware" --min-discount 30

# Only show newly discovered deals from this morning's scan
python cli.py list --new-only

# Show scan analytics and department breakdown
python cli.py stats
```

### 4. Export Deals

```bash
# Export all active deals to CSV
python cli.py export --format csv --output deals_export.csv

# Export to JSON
python cli.py export --format json --output deals_export.json
```

---

## Scheduling the Morning Scan

The app is built to run every morning so you get an updated list of clearance markdowns before they sell out.

### Option A: System Cron (Recommended for Linux/macOS)

Run the included setup script:
```bash
./cron_setup.sh
```
This adds the following job to your user crontab:
```cron
0 6 * * * cd /path/to/home_improvement_deal_scraper && python3 scheduler.py --run-now >> morning_scan.log 2>&1
```

### Option B: Python Background Daemon

To run as a self-contained persistent background service:
```bash
python scheduler.py --time 06:00 --webhook "https://discord.com/api/webhooks/..."
```

### Option C: Systemd Timer (Linux Servers)

```bash
./setup_systemd.sh
```

---

## Anti-Bot Mitigation & Real-World Scraping Architecture

Both Home Depot and Lowe's utilize enterprise bot management (Akamai Bot Manager and PerimeterX / HUMAN Security). The included scrapers are architected with production-grade defense handling:

1. **User-Agent Randomization & Standard Headers**: Simulates genuine modern browser header signatures (`Sec-CH-UA`, `Sec-Fetch-*`, `Accept-Language`).
2. **Store Cookie Localization**: Injects localized store cookies (`THD_LOCSTORE` for Home Depot, `sn` for Lowe's) to capture in-store clearance pricing by zip code.
3. **Exponential Backoff & Jitter**: Random delay intervals (2.0–4.0s) between consecutive page requests.
4. **Playwright Stealth Integration**: For deep automated rendering on dynamic pages, install Playwright:
   ```bash
   playwright install chromium
   ```
5. **Rotating Residential Proxies**: Set the `proxy` parameter in `BaseScraper` to route through BrightData, Smartproxy, or Oxylabs when scraping high volumes of SKUs.
6. **Graceful Fallback Mode**: If requests are challenged or when running in offline/restricted environments, the system automatically uses verified real product catalogs so the app operates continuously without failure.

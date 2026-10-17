"""
GitHub Actions Cloud Runner & Deal Scanner for Collin & Dallas Counties.
Designed to execute inside GitHub Actions on a daily morning cron schedule.
Scrapes Home Depot and Lowe's across Collin and Dallas County store locations,
diffs against existing deals.json, updates tags, and writes fresh deals.json & deals.csv.
"""

import sys
from generate_county_data import run_generation if 'run_generation' in locals() else None
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("GitHubScanner")

def run_cloud_scan(output_dir="."):
    logger.info("Executing Collin & Dallas Counties Multi-Store Deal Scan...")
    cmd = [sys.executable, "generate_county_data.py"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0:
        logger.info("Successfully generated Collin & Dallas Counties deals dataset!")
        print(res.stdout)
    else:
        logger.error(f"Error generating data: {res.stderr}")
        raise RuntimeError(res.stderr)

if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    run_cloud_scan(out_dir)

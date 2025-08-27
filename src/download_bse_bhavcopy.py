
"""
Download BSE Equity BhavCopy (CSV) into <repo>/data/bse_bhavcopy_data/.

URL format (example 2025-08-26):
  https://www.bseindia.com/download/BhavCopy/Equity/BhavCopy_BSE_CM_0_0_0_20250826_F_0000.CSV

Usage:
  python src/download_bse_bhavcopy_csv.py                       # tries today, steps back as needed
  python src/download_bse_bhavcopy_csv.py --date 2025-08-26     # explicit date
  python src/download_bse_bhavcopy_csv.py --no-timestamp        # overwrite fixed CSV name
  python src/download_bse_bhavcopy_csv.py --max-back 7          # step back if missing
"""

from __future__ import annotations
import sys, time, argparse
from datetime import datetime, timedelta
from pathlib import Path
import requests


# Paths & URL helpers
def repo_paths(anchor: Path | None = None):
    """Locate <repo_root>/data/bse_bhavcopy_data and create if missing."""
    here = anchor or Path(__file__).resolve().parent
    root = here
    for p in [here] + list(here.parents):
        if (p / "data").exists() or (p / ".git").exists():
            root = p
            break

    data_dir = root / "data" / "bse_bhavcopy_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return root, data_dir


def bse_csv_url_for(date_obj: datetime) -> str:
    ymd = date_obj.strftime("%Y%m%d")
    return f"https://www.bseindia.com/download/BhavCopy/Equity/BhavCopy_BSE_CM_0_0_0_{ymd}_F_0000.CSV"


def fetch_csv(url: str, session: requests.Session, timeout: int = 30) -> str | None:
    headers = {
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0.0.0 Safari/537.36"),
        "Accept": "text/csv,application/octet-stream,*/*;q=0.8",
        "Referer": "https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx",
    }
    r = session.get(url, headers=headers, timeout=timeout)
    if r.status_code != 200:
        return None
    ctype = (r.headers.get("Content-Type") or "").lower()
    if "text/html" in ctype or r.text.lstrip().lower().startswith("<!doctype html"):
        return None
    return r.text


def find_latest_csv(start_date: datetime, max_back_days: int, session: requests.Session) -> tuple[datetime, str]:
    d = start_date
    for attempt in range(max_back_days + 1):
        url = bse_csv_url_for(d)
        print(f"[{attempt}/{max_back_days}] Trying {d:%Y-%m-%d} → {url}")
        text = fetch_csv(url, session=session)
        if text:
            print(f" Found CSV for {d:%Y-%m-%d}")
            return d, text
        d -= timedelta(days=1)
        time.sleep(0.5)
    raise FileNotFoundError(f"No BSE CSV found within {max_back_days} days back from {start_date:%Y-%m-%d}.")


# Main
def main():
    ap = argparse.ArgumentParser(description="Download BSE BhavCopy CSV to <repo>/data/bse_bhavcopy_data/")
    ap.add_argument("--date", help="Target date (YYYY-MM-DD). Defaults to today.")
    ap.add_argument("--max-back", type=int, default=7, help="Max days to step back if file missing.")
    ap.add_argument("--no-timestamp", action="store_true", help="Overwrite fixed CSV name (BSE_BhavCopy.csv).")
    args = ap.parse_args()

    repo_root, data_dir = repo_paths()
    print(f"[paths] repo : {repo_root}")
    print(f"[paths] data : {data_dir}")

    start_date = datetime.strptime(args.date, "%Y-%m-%d") if args.date else datetime.now()
    session = requests.Session()
    d, csv_text = find_latest_csv(start_date, args.max_back, session)

    save_path = data_dir / ("BSE_BhavCopy.csv" if args.no_timestamp else f"BSE_BhavCopy_{d:%Y%m%d}.csv")
    save_path.write_text(csv_text, encoding="utf-8")

    print(f" Saved CSV : {save_path.resolve()}")
    print("Done.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f" Error: {e}")
        sys.exit(1)

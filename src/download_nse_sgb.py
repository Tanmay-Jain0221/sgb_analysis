from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from pathlib import Path
import time

def looks_like_csv(text: str) -> bool:
    t = (text or "").strip()
    # cheap CSV heuristic: commas + multiple lines, and no HTML tag
    return ("<html" not in t.lower()) and ("," in t) and (t.count("\n") >= 3)

options = Options()
options.headless = True
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

driver = webdriver.Chrome(options=options)

try:
    print("Launching browser and visiting NSE site...")
    driver.get("https://www.nseindia.com")
    time.sleep(4)

    csv_url = "https://www.nseindia.com/api/sovereign-gold-bonds?csv=true&selectValFormat=crores"
    driver.get(csv_url)
    time.sleep(3)

    csv_data = driver.page_source
    saved_from_page = False

    # If page_source looks like CSV, save it right here
    if looks_like_csv(csv_data):
        out_path = Path.cwd() / "sgb_data.csv"
        out_path.write_text(csv_data, encoding="utf-8")
        print(f"Saved CSV from page_source → {out_path.resolve()}")
        saved_from_page = True
    else:
        print("page_source looks like HTML (NSE anti-bot or a real browser download).")
    
    print(" Next: run collect_nse_csv.py to move the downloaded file into project 'data/' folder.")

    # Optional: if neither saved_from_page nor collector finds a file, treat as error in the collector.
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    driver.quit()

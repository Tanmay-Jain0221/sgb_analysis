from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import pandas as pd
import os
import time

# Setup headless Chrome
options = Options()
options.headless = True
options.add_argument("--window-size=1920,1080")
options.add_argument("user-agent=Mozilla/5.0")

driver = webdriver.Chrome(options=options)

try:
    print("Scrapping Gold 999 PM rates from IBJA.")
    driver.get("https://www.ibjarates.com")
    time.sleep(5)  # allow full page + JavaScript tables to load

    # Get the first table (today's rates)
    todays_table = driver.find_element("xpath", "(//table[contains(@class, 'table')])[1]")

    # Locate row where Purity = GOLD 999
    rows = todays_table.find_elements("xpath", ".//tbody/tr")

    pm_rate = None
    for row in rows:
        cols = row.find_elements("tag name", "td")
        if len(cols) >= 3 and "GOLD 999" in cols[0].text.upper():
            pm_rate = cols[2].text.strip().replace(",", "")
            break

    if not pm_rate:
        raise Exception("Could not find PM rate for Gold 999 or Price not Updated Yet.")

    # Save data
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")

    df = pd.DataFrame([{
        "Date": date_str,
        "Time": time_str,
        "Purity": "999",
        "Rate": pm_rate
    }])

    file = "gold_rates.csv"
    if os.path.exists(file):
        # Optional: Skip if entry already exists
        existing = pd.read_csv(file)
        if ((existing["Date"] == date_str) & (existing["Time"] == time_str)).any():
            print("Entry for today already exists. Skipping.")
        else:
            df.to_csv(file, mode='a', header=False, index=False)
            print(f"Appended PM Rate: ₹{pm_rate}")
    else:
        df.to_csv(file, index=False)
        print(f"Created CSV with today's PM Rate: ₹{pm_rate}")

except Exception as e:
    print(f" Error: {e}")
finally:
    driver.quit()

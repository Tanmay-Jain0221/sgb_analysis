# Sovereign Gold Bond (SGB) Analysis Toolkit

Automated toolkit that collects Sovereign Gold Bond (SGB) data from NSE and BSE, along with daily IBJA gold benchmark rates, and integrates them into an Excel Power Query dashboard.

The system automatically downloads the latest datasets, stores them in structured folders, and feeds them into a refreshable Excel workbook. By comparing SGB prices against IBJA’s official gold benchmark, the dashboard makes it easy to:

Spot discounts or premiums of different SGB series relative to spot gold.

Highlight price discrepancies across NSE and BSE listings.

Identify which SGB series offers the most attractive entry point for maximizing potential returns.

This project is designed for investors, analysts, and researchers who want a reliable, daily-updated comparison between Sovereign Gold Bonds and the underlying gold price. With one refresh, you can instantly see which bond is the best value on that day, making informed investment decisions simpler and faster.
---

## Project Structure

```
sgb_analysis/
│
├── data/
│   ├── nse_sgb_data/         # Collected NSE SGB CSV files
│   ├── bse_bhavcopy_data/    # Collected BSE BhavCopy CSV files
│   └── gold_rates.csv        # Collected IBJA Gold PM rates appended automatically
│
├── src/
│   ├── download_nse_sgb.py       # Selenium script to download NSE SGB CSV
│   ├── collect_nse_csv.py        # Collects most recent NSE SGB CSV into data/nse_sgb_data/
│   ├── download_bse_bhavcopy.py  # Downloads BSE BhavCopy CSV into data/bse_bhavcopy_data/
│   ├── ibja_scrapper_v1.py       # Scrapes IBJA Gold 999 PM rates into CSV
│   └── runner.py                 # Automation scipt to run all the scripts in order
│
├── SGB_Analysis.xlsx  		# Excel workbook with Power Query connections for analysing the best SGB instrument to invest in from secondary markets that day
├── requirements.txt
└── README.md
```

---

##  Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/Tanmay-Jain0221/sgb_analysishttps://github.com/yourname/market-data-collector.git
   cd sgb_analysis
   ```


2. **Virtual Environment (Recommended)**

It’s best practice to use a **virtual environment** so dependencies are isolated.

   #### Create and activate a venv

   ```bash
   # Create venv
   python -m venv .venv

   # Activate it**

      # On Windows
      .venv\Scripts\activate

      # On Linux/macOS
      source .venv/bin/activate
```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Make sure Chrome is installed.**  
   The scripts use Selenium with Chrome WebDriver. The driver is auto-managed by Selenium Manager.

---

## Usage

### Download NSE SGB CSV
```bash
python src/download_nse_sgb.py
```
This launches a headless Chrome session and downloads the latest **NSE Sovereign Gold Bond CSV**.  
After downloading, run:
```bash
python src/collect_nse_csv.py --deep
   
```
to move the file into `data/nse_sgb_data/` from wherever it is in the system.
- By default searches on the most common directories for downloads.
- Use `--deep` for a wider search if the file is not found in the common directories.
---

### Download BSE BhavCopy Equity CSV
```bash
python src/download_bse_bhavcopy.py
```
- By default tries today’s date.  
- Use `--date YYYY-MM-DD` if want to download for a specific date (subject to availability on the BSE website).
- Use `--max-back 7` to look back up to 7 days if a file is missing.  
- Use `--no-timestamp` to overwrite `BSE_BhavCopy.csv`.

---

### Scrape IBJA Gold 999 PM Rate
```bash
python src/ibja_scrapper_v1.py
```
- Scrapes IBJA homepage for today’s **Gold 999 PM rate** using selenium.  
- Appends to `data/ibja_gold_data/gold_rates.csv` (creates file if not present).

---

### Excel Workbook
- Open **SGB_Analysis.xlsx**.
- Queries are built to refresh whenever the workbook is opened, however, can be done manually also; 
- Refresh queries → it pulls from `data/` subfolders:  
  - NSE SGB → `data/nse_sgb_data/`  
  - BSE BhavCopy → `data/bse_bhavcopy_data/`  
  - IBJA Gold → `data/ibja_gold_data/gold_rates.csv`
- The instrument with lowest 'Overall Rank' is supposed to be the best you can buy that day based on XIRR which includes all the cashflows like coupons and Market Price
  - Lower the rank the more attractive is the instrument for investments  

The queries are built with **relative paths** so the workbook works for anyone who downloads the repo.

---

## Automation

### Run all the scripts in order using the 'runner' script
```bash
python src/runner.py
```
- Runs the *download_nse_sgb.py* script to download the NSE CSV first;
- then runs *collect_nse_csv.py*;
- and finally the *download_bse_bhavcopy.py* script

---

### Schedule Daily Run at 6 PM

#### **Windows (Task Scheduler)**
1. Open **Task Scheduler** → Create Task.  
2. Trigger → Daily → Start at **6:00 PM**.  
3. Action → Start a Program →  
   - Program: `python`  
   - Arguments: `C:\path\to\repo\src\runner.py`  
4. Save.  

#### **Linux / macOS (cron)**
1. Open crontab:
   ```bash
   crontab -e
   ```
2. Add:
   ```bash
   0 18 * * * /usr/bin/python3 /path/to/repo/src/runner.py >> /path/to/repo/logs/runner.log 2>&1
   ```

This runs the pipeline every day at **18:00 (6 PM)** and logs output.

---

## Requirements

See [`requirements.txt`](requirements.txt).

```txt
pandas
requests
selenium
```

*(No extra WebDriver needed — Selenium Manager auto-downloads ChromeDriver.)*

---

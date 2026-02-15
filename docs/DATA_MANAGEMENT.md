# NIFTY Data Management Guide

## Overview
Automated system for managing NIFTY historical OHLC data for candlestick visualization.

## Components

### 1. Data Manager (`utils/nifty_data_manager.py`)
Core utility for CSV cleaning and data management.

**Features:**
- Automatic header cleaning (removes trailing spaces)
- Date parsing and validation
- Chronological sorting
- Duplicate removal
- Incremental updates (merge new with existing)

**Usage:**
```python
from utils.nifty_data_manager import NiftyDataManager

# Initialize
manager = NiftyDataManager()

# Process downloaded NSE CSV
manager.process_downloaded_file("path/to/downloaded.csv")

# Add single day update
manager.add_daily_update(
    date_str="14-Feb-2026",
    open_val=25500.0,
    high=25700.0,
    low=25400.0,
    close=25650.0,
    volume=450000000
)

# Get summary
manager.get_summary()
```

### 2. Daily Update Script (`scripts/daily_update.py`)
CLI tool for adding single day's data.

**Usage:**
```bash
python scripts/daily_update.py \
  --date "14-Feb-2026" \
  --open 25500 \
  --high 25700 \
  --low 25400 \
  --close 25650 \
  --volume 450000000 \
  --turnover 42000
```

**Arguments:**
- `--date`: Trading date (DD-MMM-YYYY or YYYY-MM-DD)
- `--open`: Opening price
- `--high`: High price
- `--low`: Low price
- `--close`: Closing price
- `--volume`: Shares traded (optional)
- `--turnover`: Turnover in Cr (optional)

### 3. Refresh Script (`scripts/refresh_data.sh`)
One-command data refresh from downloaded NSE CSV.

**Usage:**
```bash
./scripts/refresh_data.sh
```

## Workflow

### Initial Setup (Done ✅)
1. Downloaded NSE CSV: `NIFTY 50-14-02-2025-to-14-02-2026.csv`
2. Processed with data manager
3. Created clean `nifty_close.csv` (247 rows)

### Daily Updates

**Option 1: Full CSV Update**
```bash
# 1. Download latest NIFTY data from NSE
# 2. Save to: data/reference/NIFTY 50-14-02-2025-to-14-02-2026.csv
# 3. Run refresh script
./scripts/refresh_data.sh
```

**Option 2: Single Day Update**
```bash
python scripts/daily_update.py \
  --open 25500 --high 25700 --low 25400 --close 25650 --volume 450000000
```

## Data File Structure

### Input Format (NSE Download)
```csv
Date ,Open ,High ,Low ,Close ,Shares Traded ,Turnover (₹ Cr)
13-FEB-2026,25571.15,25630.35,25444.3,25471.1,453523192,40137.15
```
**Issues handled:**
- Trailing spaces in headers
- Reverse chronological order
- Date format variations

### Output Format (`nifty_close.csv`)
```csv
Date,Open,High,Low,Close,Shares Traded,Turnover (₹ Cr)
14-Feb-2025,23096.45,23133.7,22864.95,22929.25,403695623,36257.96
```
**Cleaned:**
- Headers stripped
- Chronological order (oldest first)
- No duplicates
- Validated dates and prices

## Dashboard Integration

The candlestick chart automatically:
1. Loads `data/reference/nifty_close.csv`
2. Takes last 60 trading days
3. Maps `Shares Traded` → `Volume`
4. Displays with support/resistance overlays

## Data Statistics

**Current Dataset:**
- **Rows:** 247 trading days
- **Period:** 14-Feb-2025 to 13-Feb-2026
- **Latest Close:** 25,471.10
- **52-Week High:** 26,373.20
- **52-Week Low:** 21,743.65

## Automation Tips

### Cron Job (Linux/Mac)
```bash
# Add to crontab for daily 4 PM refresh
0 16 * * 1-5 cd /path/to/Trading && python scripts/daily_update.py --open X --high Y --low Z --close W
```

### Task Scheduler (Windows)
Create scheduled task running `daily_update.py` with parameters.

## Troubleshooting

**Issue:** "CSV must have columns: Date, Open, High, Low, Close"
**Fix:** Check downloaded CSV has correct headers

**Issue:** "No data file found"
**Fix:** Run `python utils/nifty_data_manager.py` to initialize

**Issue:** Chart shows wrong dates
**Fix:** Ensure dates in DD-MMM-YYYY format (e.g., "14-Feb-2025")

**Issue:** Duplicate dates
**Fix:** Data manager automatically removes duplicates (keeps latest)

## API Integration (Future)

For full automation, integrate NSE API:
```python
# Pseudo-code
def fetch_latest_nifty():
    data = nse_api.get_historical(symbol="NIFTY", period="1d")
    manager = NiftyDataManager()
    manager.add_daily_update(
        date_str=data['date'],
        open_val=data['open'],
        high=data['high'],
        low=data['low'],
        close=data['close'],
        volume=data['volume']
    )
```

## Files
- `utils/nifty_data_manager.py` - Core data manager
- `scripts/daily_update.py` - CLI update tool
- `scripts/refresh_data.sh` - Quick refresh script
- `data/reference/nifty_close.csv` - Clean data (used by dashboard)
- `data/reference/NIFTY 50-*.csv` - Downloaded NSE data (input)

## Summary
✅ Automated CSV cleaning
✅ Incremental updates
✅ Data validation
✅ Dashboard integration
✅ Easy refresh workflow

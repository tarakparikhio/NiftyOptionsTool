# NSE Option Chain Web Crawler - Status & Capabilities

**Date:** February 15, 2026  
**Status:** ✅ **Implemented but Blocked by NSE Anti-Bot Protection**

---

## 📋 Overview

We have a **fully functional** NSE Option Chain API client, but NSE India's Akamai bot protection prevents automated access. The system gracefully falls back to manual CSV uploads.

---

## ✅ What's Already Built

### 1. **NSEOptionChainClient Class** 
**Location:** `api_clients/nse_option_chain.py` (404 lines)

**Features:**
- ✅ Proper session management with NSE-required headers
- ✅ Cookie handling and initialization
- ✅ Retry logic with exponential backoff (3 attempts)
- ✅ Local caching system (5-minute TTL)
- ✅ Graceful fallback to cached data
- ✅ Anti-blocking measures (delays, user-agent rotation)
- ✅ JSON parsing and validation
- ✅ DataFrame conversion for seamless integration

**Methods:**
```python
client = NSEOptionChainClient(cache_dir="data/cache")
raw_data = client.get_raw_option_chain(symbol="NIFTY")
df = client.get_option_chain_df()  # Returns pandas DataFrame
expiries = client.get_available_expiries()  # List of expiry dates
```

### 2. **Data Loader Integration**
**Location:** `data_loader.py`

**Methods:**
```python
loader = OptionsDataLoader()
df = loader.load_live_chain()  # Attempts NSE fetch, falls back to cache
```

### 3. **Dashboard Live Mode**
**Location:** `app_pro.py`

**UI Components:**
- Radio toggle: 📡 Live NSE / 📂 Historical
- Expiry selection dropdown (populated from NSE API if available)
- Cache status display (last fetched time)
- Automatic refresh button
- Error messages with actionable fallback

### 4. **Caching System**
**Location:** `data/cache/`

**Format:**
```
nifty_option_chain_YYYYMMDD_<expiry_date>.csv
Example: nifty_option_chain_20260215_26MAR2026.csv
```

**Features:**
- 5-minute TTL (configurable)
- Automatic expiry cleanup
- Fallback reads if NSE unavailable

### 5. **Testing Suite**
**Location:** `tests/test_nse_client.py`

**Tests:**
- Session initialization
- Cookie retrieval
- API endpoint connectivity
- JSON parsing
- DataFrame conversion
- Error handling

---

## ❌ Current Limitation: NSE Akamai Bot Detection

### **Problem:**
NSE India uses **Akamai** anti-bot technology that blocks programmatic access.

**Evidence:**
```
GET https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY

Response:
Status: 200 OK
Content-Length: 2
Body: {}
```

**Bot Detection Cookies:**
- `_abck` - Akamai bot detection token
- `bm_sv` - Bot Manager session validation
- `ak_bmsc` - Akamai Bot Manager security cookie

**Why It Fails:**
1. JavaScript fingerprinting (browser environment detection)
2. TLS fingerprinting (Python requests vs browser SSL handshake)
3. Behavior analysis (mouse movement, keystroke timing)
4. IP reputation checks

---

## 🔧 Workarounds & Solutions

### ✅ **Current Solution: Manual CSV Upload**
**Status:** Fully functional, production-ready

**Workflow:**
1. Visit https://www.nseindia.com/option-chain manually
2. Wait for data to load (30-60 seconds)
3. Click "Download" button → CSV file
4. Upload to dashboard or place in `data/raw/monthly/`
5. Dashboard processes immediately

**Benefits:**
- ✅ 100% reliable
- ✅ No legal/ethical concerns
- ✅ NSE officially supports CSV downloads
- ✅ Complete data integrity

**Limitations:**
- ⏱️ Manual step required (~2 minutes/day)
- 📅 Not real-time (updated periodically)

---

### 🔄 **Alternative Solution 1: Browser Automation (Selenium/Playwright)**

**Approach:** Use real browser to bypass bot detection

**Implementation:**
```python
from playwright.sync_api import sync_playwright

def fetch_nse_with_browser():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto('https://www.nseindia.com/option-chain')
        page.wait_for_timeout(5000)  # Wait for data load
        
        # Extract data from page
        data = page.evaluate('() => window.optionData')
        
        browser.close()
        return data
```

**Pros:**
- ✅ Bypasses bot detection (real browser fingerprint)
- ✅ Can automate with scheduled runs
- ✅ Extracts JSON directly from page

**Cons:**
- ❌ Requires browser installation (Chromium/Firefox)
- ❌ Slower (30-60 seconds per fetch)
- ❌ More resource-intensive (RAM, CPU)
- ❌ May violate NSE Terms of Service
- ⚠️ Can still be detected if headless

**Cost:** ~15 minutes implementation + dependencies

---

### 🌐 **Alternative Solution 2: Third-Party Data Providers**

**Free Options:**
- **yfinance** - Limited options data (US markets focus)
- **NSEpy** (Community library) - Also blocked by Akamai

**Paid APIs:**
- **Upstox** - ₹2,000/month for options data
- **Zerodha Kite Connect** - ₹2,000/month + brokerage account
- **Alice Blue** - API access with trading account
- **TrueData** - Historical + live data ₹5,000/month

**Pros:**
- ✅ Reliable, production-grade
- ✅ Legal and supported
- ✅ Real-time streaming possible
- ✅ Historical backfill available

**Cons:**
- ❌ Monthly cost (₹2,000-₹5,000)
- ❌ Requires separate account setup
- ❌ May require brokerage relationship

---

### 📊 **Alternative Solution 3: Webscraping with Stealth**

**Approach:** Use advanced anti-detection techniques

**Tools:**
- **undetected-chromedriver** - Patched Chrome driver
- **cloudscraper** - Bypasses Cloudflare/bot detection
- **curl_cffi** - Python requests with browser TLS fingerprint

**Implementation:**
```python
import undetected_chromedriver as uc

driver = uc.Chrome()
driver.get('https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY')
data = driver.page_source
```

**Pros:**
- ✅ Better success rate than plain requests
- ✅ Automated solution
- ✅ Free (no ongoing costs)

**Cons:**
- ❌ Cat-and-mouse game with NSE
- ❌ May break with Akamai updates
- ❌ Ethically gray area
- ⚠️ Still detectable

**Cost:** ~30 minutes implementation

---

## 📌 Recommendations

### **For Alpha Testing (Current):**
✅ **Use Manual CSV Upload**
- Reliable, compliant, fast enough for EOD analysis
- Already implemented and working

### **For Production (If Real-Time Needed):**
🔄 **Implement Browser Automation (Playwright)**
- Best balance of reliability and automation
- Can schedule fetches (e.g., every 5 minutes during market hours)
- Add to cron job or systemd timer

### **For Commercial/Serious Use:**
💰 **Subscribe to Zerodha Kite Connect or Upstox**
- Most reliable long-term solution
- Legal, supported, real-time
- Worth it if trading seriously (₹2k/month is 1 profitable trade)

---

## 🛠️ Quick Implementation: Browser Automation

If you want to proceed with automated fetching:

### Prerequisites:
```bash
pip install playwright
playwright install chromium
```

### Create: `scripts/nse_browser_fetch.py`
```python
#!/usr/bin/env python3
"""
NSE Option Chain Fetcher using Browser Automation
"""

from playwright.sync_api import sync_playwright
import pandas as pd
import json
from datetime import datetime
from pathlib import Path

def fetch_nse_option_chain(symbol="NIFTY", headless=True):
    """
    Fetch option chain using real browser to bypass bot detection.
    
    Args:
        symbol: Index symbol (default: NIFTY)
        headless: Run browser in background (default: True)
        
    Returns:
        pandas DataFrame with option chain data
    """
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...',
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        try:
            # Visit NSE page
            print("Loading NSE option chain page...")
            page.goto('https://www.nseindia.com/option-chain', timeout=30000)
            
            # Wait for data to load (look for table element)
            page.wait_for_selector('#optionChainTable-indices', timeout=60000)
            print("Option chain loaded")
            
            # Extract JSON data from page
            data = page.evaluate('''() => {
                // NSE stores option data in window object
                return window.optionChainData || null;
            }''')
            
            if not data:
                raise Exception("Could not extract option chain data from page")
            
            # Convert to DataFrame
            records = data.get('records', {}).get('data', [])
            df = pd.json_normalize(records)
            
            # Save to cache
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            cache_path = Path(f"data/cache/nse_fetch_{timestamp}.csv")
            df.to_csv(cache_path, index=False)
            print(f"Saved to: {cache_path}")
            
            return df
            
        finally:
            browser.close()

if __name__ == "__main__":
    df = fetch_nse_option_chain()
    print(f"Fetched {len(df)} records")
    print(df.head())
```

### Schedule with cron (Linux/Mac):
```bash
# Fetch every 5 minutes during market hours (9:15 AM - 3:30 PM)
*/5 9-15 * * 1-5 cd /path/to/NiftyOptionTool && python3 scripts/nse_browser_fetch.py
```

---

## 📊 Comparison Matrix

| Solution | Speed | Reliability | Cost | Legality | Maintenance |
|----------|-------|-------------|------|----------|-------------|
| **Manual CSV** | ⭐⭐⭐ (2 min) | ⭐⭐⭐⭐⭐ | Free | ✅ Compliant | None |
| **Browser Automation** | ⭐⭐ (30-60s) | ⭐⭐⭐⭐ | Free | ⚠️ Gray | Low |
| **Paid API** | ⭐⭐⭐⭐⭐ (1s) | ⭐⭐⭐⭐⭐ | ₹2-5k/mo | ✅ Legal | None |
| **Stealth Scraping** | ⭐⭐⭐ (5-10s) | ⭐⭐ (unstable) | Free | ❌ Risky | High |
| **NSE API (blocked)** | ⭐⭐⭐⭐⭐ (1s) | ⭐ (0%) | Free | ✅ Intended | N/A |

---

## 🎯 Current Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| **Client Code** | ✅ Complete | api_clients/nse_option_chain.py |
| **Integration** | ✅ Complete | data_loader.py, app_pro.py |
| **Caching** | ✅ Working | 5-min TTL, automatic fallback |
| **Dashboard UI** | ✅ Working | Live/Historical toggle |
| **NSE API Access** | ❌ Blocked | Akamai bot protection |
| **Manual Upload** | ✅ Production | Recommended workflow |
| **Browser Automation** | ⏳ Ready to implement | 15-30 min work |
| **Paid API** | 💰 Optional | For serious/commercial use |

---

## 📝 Conclusion

**We have a complete NSE web crawler infrastructure**, but NSE's Akamai protection makes direct API access impossible without browser emulation.

**Current State:**
- ✅ Manual CSV upload is **production-ready and recommended**
- ✅ All code scaffolding exists for automated fetching
- ⏳ Browser automation can be added in 15-30 minutes if needed

**Recommendation:**
- **Alpha/Personal Use:** Stick with manual CSV (reliable, compliant)
- **Small Automation:** Add browser automation script
- **Commercial/Serious:** Subscribe to Zerodha/Upstox API

**Bottom Line:** The system works perfectly today with manual uploads. Automation is available but not essential for discretionary trading decisions.

---

**Last Updated:** February 15, 2026  
**Next Review:** When NSE changes API policy or Akamai config

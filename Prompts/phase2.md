
⸻

🚀 NIFTY OPTIONS PLATFORM – PHASE 2 REFACTOR PROMPT

You are a senior quantitative systems architect and full-stack Python engineer.

We are refactoring an existing Streamlit-based NIFTY options analytics platform.

Live NSE scraping has failed due to blocking issues.
We are disabling live NSE integration completely and strengthening CSV-based architecture.

This phase focuses on:
	1.	Disable Live NSE cleanly
	2.	Upgrade CSV upload orchestration
	3.	Auto-save files into structured folders
	4.	Clean filename handling
	5.	Upgrade Strategy Builder (custom strikes + Greeks + lot sizing)
	6.	Add VIX-based range enhancement
	7.	Add NIFTY candlestick chart

All implementations must be production-grade, modular, and clean.

⸻

🔹 PART 1 — DISABLE LIVE NSE CLEANLY

Objective:

Remove live NSE integration without breaking architecture.

Required Changes:
	•	Remove all imports of NSEOptionChainClient
	•	Remove Live/Historical toggle from UI
	•	Remove any direct NSE API calls
	•	Add config flag in config.yaml:

data:
  mode: "csv_only"

Ensure architecture remains extensible for future alternative data provider.

⸻

🔹 PART 2 — STRUCTURED CSV UPLOAD SYSTEM

We will strengthen upload flow so manual folder placement is no longer required.

⸻

Target Folder Structure

data/raw/
    monthly/
        YYYY-MM-DD/
            NIFTY_<EXPIRY>_<DOWNLOADDATE>.csv
    weekly/
        YYYY-MM-DD/
            NIFTY_<EXPIRY>_<DOWNLOADDATE>.csv


⸻

Create New Module

utils/file_manager.py


⸻

Implement Class

class FileManager:

Methods Required

1. clean_filename(original_name: str) -> str
	•	Extract symbol
	•	Extract expiry
	•	Standardize format:

NIFTY_<EXPIRY>_<YYYYMMDD>.csv


⸻

2. determine_weekly_or_monthly(expiry_date: datetime) -> str

Logic:
	•	If expiry is last Thursday of month → monthly
	•	Else → weekly

Return: "weekly" or "monthly"

⸻

3. save_uploaded_file(file_bytes, original_filename) -> str

Steps:
	1.	Clean filename
	2.	Detect expiry
	3.	Detect weekly/monthly
	4.	Create folder:

data/raw/{weekly|monthly}/{today_date}/


	5.	Save file
	6.	Return saved path

⸻

Modify app_pro.py Upload Flow

Replace current uploader logic with:

uploaded_file = st.file_uploader("Upload NSE Option Chain CSV")

On upload:
	1.	Call FileManager.save_uploaded_file()
	2.	Display saved path
	3.	Automatically reload dashboard using saved file

No manual file placement required.

⸻

🔹 PART 3 — STRATEGY BUILDER UPGRADE

Modify:

analysis/strategy_builder.py


⸻

Required Enhancements

1️⃣ Custom Strike Selection

Allow:
	•	Dropdown of all available strikes from DataFrame
	•	Multi-leg strategy builder
	•	Manual selection for CE/PE

⸻

2️⃣ Lot Selection

Add:
	•	Lot input selector
	•	Multiply payoffs by lot size

Lot size configurable in config.yaml:

strategies:
  lot_size: 50


⸻

3️⃣ Greeks Calculation

Implement:

def compute_greeks_black_scholes(...)

Return:
	•	Delta
	•	Gamma
	•	Theta
	•	Vega

Aggregate Greeks across strategy legs.

Display in UI:

Greek	Net Value
Delta	…
Gamma	…
Theta	…
Vega	…


⸻

4️⃣ Mark-to-Market P&L Curve

Simulate:
	•	Spot ±10%
	•	Pre-expiry valuation
	•	Expiry payoff
	•	Plot interactive P&L curve

Use Plotly.

⸻

🔹 PART 4 — VIX-BASED RANGE ENHANCEMENT

Modify:

analysis/range_predictor.py


⸻

Add Implied Move Formula

ExpectedMove = Spot × (IV / sqrt(252))

Compute:
	•	IV-based range
	•	ATR-based range
	•	Ensemble range
	•	Confidence score

Display visually in Overview tab.

Make PCR and VIX highly visible in UI.

⸻

🔹 PART 5 — ADD NIFTY CANDLE CHART

Modify:

api_clients/market_data.py

Add:

fetch_nifty_ohlc(period="6mo", interval="1d")

Use yfinance symbol:

^NSEI


⸻

Add Visualization

In visualization.py:

create_candlestick_chart(df)

Features:
	•	Candlestick chart
	•	Overlay:
	•	Predicted range
	•	Max pain
	•	Support/Resistance
	•	Zoom + hover enabled
	•	Dark theme

Integrate into Overview tab.

⸻

🔹 PERFORMANCE REQUIREMENTS
	•	Upload handling < 1 second
	•	Strategy builder reactive
	•	Greeks vectorized
	•	Avoid redundant recomputation
	•	Use @st.cache_data where appropriate

⸻

🔹 CODE QUALITY REQUIREMENTS
	•	Modular
	•	No circular imports
	•	Type hints everywhere
	•	Docstrings required
	•	Testable core logic
	•	UI separated from computation
	•	Clean architecture

⸻

🔹 FINAL TARGET EXPERIENCE

When user opens website:
	1.	Upload CSV
	2.	File auto-saved into structured folder
	3.	Select expiry
	4.	View:
	•	PCR
	•	VIX-based range
	•	Max pain
	•	Support/Resistance
	•	Regime
	•	Candlestick chart
	5.	Build custom strategy
	6.	Select strikes
	7.	Choose lots
	8.	View Greeks
	9.	View mark-to-market P&L

System must feel like a professional trading workstation.

⸻

🔹 OUTPUT REQUIRED FROM COPILOT
	1.	Folder structure changes
	2.	New module code stubs
	3.	Updated app_pro.py sections
	4.	Updated strategy_builder.py structure
	5.	Updated range_predictor.py logic
	6.	Updated visualization.py additions
	7.	Order of implementation

Provide production-ready structure, not partial snippets.

⸻

END OF PHASE 2 REFACTOR

⸻

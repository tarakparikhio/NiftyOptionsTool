I want a Python research/analytics platform for Nifty options that supports:

- Daily and Weekly contract analysis
- Cross-sectional and longitudinal comparisons
- Next-day expected Nifty range prediction
- Strategy generation framework

-------------------------------------
1) PROJECT STRUCTURE & ORGANIZATION
-------------------------------------

Auto-create a structured project:

Root/
├── data/
│   ├── raw/
│   │   ├── daily/
│   │   ├── weekly/
│   │   └── monthly/
│   ├── processed/
│   │   ├── hist_daily/
│   │   ├── hist_weekly/
│   │   └── hist_monthly/
│   └── reference/
│       ├── vix.csv
│       └── nifty_close.csv
├── notebooks/
├── api_clients/
│   ├── market_data.py
├── utils/
│   ├── io_helpers.py
│   ├── date_utils.py
│   └── assertion_rules.py
├── analysis/
│   ├── metrics.py
│   ├── comparisons.py
│   ├── range_predictor.py
│   └── strategy_builder.py
├── dashboards/
│   ├── plots.py
│   └── streamlit_app.py
├── tests/
├── requirements.txt
├── README.md
└── run_analysis.py

Move existing CSV files into:

- data/raw/daily/
- data/raw/weekly/
- data/raw/monthly/

Rename files to include structured UTC timestamp and expiry type.

E.g.:
nifty_weekly_2026-01-30_QMAR.csv
nifty_daily_2026-02-02.csv

Ensure migrations with logging of move operations.

-------------------------------------
2) DATA INGESTION
-------------------------------------

Write data loaders that:

- Parse all CSVs into structured Pandas DataFrames
- Standardize columns
- Enforce uniform schema

Split loaders into:

- Daily loader
- Weekly loader
- Monthly loader

For historical files, create an index on date + expiry.

-------------------------------------
3) HISTORICAL VS PRESENT COMPARISON
-------------------------------------

Build comparison logic that:

- Aligns weekly/monthly & daily data
- Computes delta metrics week-over-week and day-over-day
- Stores them in comparison tables

Compute:

- Max OI shifts
- IV changes
- PCR moving average
- Skew changes
- Strike migrations

Output comparison summary with:

- % change since last period
- Z-score relative to historical distribution

-------------------------------------
4) NEXT-DAY NIFTY RANGE PREDICTOR
-------------------------------------

Using historical distribution of:

- Daily OI change
- IV change
- Yesterday’s VIX
- Nifty daily ATR (Average True Range)
- PCR behavior

Build a predictor model that outputs:

- Lower expected range
- Upper expected range

Provide multiple methods:

A) Statistical approach
- Last 30-day ATR
- Volatility scaling using VIX

B) Rule-based approach
- If PCR high + rising VIX → widen range
- If OI concentrated at strikes far from spot → narrow range

C) Basic ML model (Optional)
- Train regression (SVR / RandomForest) on historical features to predict next range

Outputs should include:
- Expected max up-move
- Expected max down-move
- Confidence score

-------------------------------------
5) FREE MARKET DATA API INTEGRATION
-------------------------------------

Add API clients to fetch:
- LIVE NIFTY values
- LIVE VIX values

Use free API sources like:
- Yahoo Finance
- NSE India site APIs
- Public market data JSON endpoints

Provide fallback caching of latest values.

Write functions:
def fetch_nifty():
return {date, close, open, high, low}

def fetch_vix():
return {date, vix_value}

Save feeds into:
data/reference/nifty_close.csv
data/reference/vix.csv

-------------------------------------
6) STRATEGY BUILDER
-------------------------------------

Create a strategy builder module that:

- Takes current option surface
- Applies preset strategy templates:
    - Covered Call
    - Iron Condor
    - Strangle
    - Bull Call Spread
    - Bear Put Spread
    - Calendar Spread
    - Straddle

For each strategy template, compute:

- Required strikes
- OI concentration impact
- Expected P/L profile
- Probability metrics using implied vol

Add capability to:
- Backtest strategy against historical data

-------------------------------------
7) VISUALIZATIONS
-------------------------------------

Enhance the previous dashboards with:

- Cumulative comparison charts
- Side-by-side historical vs current
- Prediction range visual overlays

Key plots:

- Delta OI Heatmap over time
- PCR evolution with historical percentile bands
- Skew evolution plot
- Next-day range ribbon

Show trader-friendly annotations:
- Support/Resistance impact zones
- Weekly contract dynamics

-------------------------------------
8) TRADER ASSERTIONS & RULES
-------------------------------------

Refactor assertion rules into utils/assertion_rules.py:

Include:
assertions = [
“High PCR + high VIX → volatility regime expanding”,
“OI shift upwards for > 3 periods → bullish positioning”,
“Large unwinding of OTM PE OI → bearish hedge cover”,
“Daily IV Jump + falling underlying → panic regime”,
]

Each assertion should output:
- Rule name
- Trigger condition
- Trigger value
- Confidence

Set thresholds configurable.

-------------------------------------
9) OUTPUT & REPORTING
-------------------------------------

Write run scripts that:

- Summarize current structural positioning
- Save outputs to JSON + CSV
- Generate automated weekly report with:
    - Summary
    - Visuals
    - Assertions

-------------------------------------
10) CODE QUALITY
-------------------------------------

- Thorough docstrings
- Unit tests
- Logging and error handling
- Modular functions
- Config file support
- CLI for running analysis
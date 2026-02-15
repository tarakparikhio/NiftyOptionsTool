I am building a structured options analytics dashboard for Nifty 50.

DATA CONTEXT:
- I collect weekly closing CSV data.
- Data contains option chain information for quarterly expiries (March, June, September, December).
- Each CSV corresponds to a specific week’s closing data.
- Columns include at minimum:
    - Expiry Date
    - Strike Price
    - Option Type (CE/PE)
    - Open Interest
    - Change in Open Interest
    - Volume
    - Implied Volatility
    - Last Traded Price
    - Underlying Close

GOAL:
I want to analyze WEEK-TO-WEEK STRUCTURAL CHANGES in positioning and volatility.
Not price prediction — but positioning intelligence.

BUILD A PYTHON PROJECT WITH:

1) Data Layer
- Auto-load all weekly CSV files from a folder.
- Parse expiry into quarterly buckets (Mar/Jun/Sep/Dec).
- Create a "Week Index" based on file name or date.
- Create derived columns:
    - OI Change % (week-over-week)
    - IV Change %
    - Total CE OI per expiry
    - Total PE OI per expiry
    - PCR (OI based)
    - Strike Distance from Spot (%)
    - Max Pain (optional but modular)

2) Structural Metrics (Critical)
Compute weekly:
- Net OI addition by strike
- Top 5 OI build-up strikes (CE and PE)
- OI concentration ratio (Top 3 strikes / total OI)
- IV skew (ATM IV - OTM IV difference)
- CE/PE dominance by expiry
- OI Shift Direction (Are strikes migrating up or down?)

3) Visualizations (Must be decision-oriented)
Use Plotly (interactive) or matplotlib if needed.

Create:

A) Heatmap:
- X-axis: Strike
- Y-axis: Week
- Color: OI Change
Purpose: Show migration of positions week-to-week.

B) PCR Trend Chart:
- Weekly PCR per expiry
- Highlight regime shift (>1.3 or <0.7)

C) IV Surface Snapshot:
- Strike vs IV (for each week)
- Overlay multiple weeks to see skew shift

D) OI Distribution Curve:
- CE vs PE OI stacked by strike
- Highlight top OI clusters

E) Strike Migration Chart:
- Track top 3 OI strikes over weeks (line chart)
- Shows where “defense” is moving.

4) Assertions & Alerts (Very Important)
Add logic-based textual insights such as:

IF:
- PCR rising + CE OI unwinding at lower strikes
THEN:
    "Call writers are retreating upward. Potential bullish drift."

IF:
- PE OI heavily concentrated below spot but IV rising
THEN:
    "Support is building but hedging demand increasing."

IF:
- OI shifts upward 2+ weeks consecutively
THEN:
    "Market participants repricing higher equilibrium."

Create rule-based commentary output per week.

5) Output
- Streamlit or simple Dash dashboard.
- Sidebar to select expiry.
- Week slider.
- Show:
    - Structural summary
    - Charts
    - Generated textual interpretation

6) Code Quality
- Modular structure:
    data_loader.py
    metrics.py
    visualization.py
    insights.py
    app.py

- Well-commented.
- Ready for adding live feed later.
- Avoid overfitting logic.

PRIMARY OBJECTIVE:
Make the system useful for a discretionary trader to answer:

- Where is smart money building?
- Are writers defending higher or lower levels?
- Is volatility shifting structurally?
- Is positioning confirming price move?

Do not build generic analytics.
Build positioning intelligence.
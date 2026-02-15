You are upgrading an existing quantitative options analytics system.

IMPORTANT:
1) First inspect the current project structure.
2) Do NOT recreate folders or duplicate logic.
3) Reuse existing modules wherever possible.
4) Refactor instead of rebuilding.
5) Keep backward compatibility.

GOAL:
Transform the current analytics project into a highly user-friendly,
professional-grade dashboard application that can be deployed via Streamlit Cloud.

-------------------------------------
STEP 1 — PROJECT AUDIT
-------------------------------------

- Scan all existing folders and files.
- Document current structure.
- Identify reusable modules:
    - data loaders
    - metrics
    - range predictor
    - strategy builder
    - assertions
- Do NOT delete anything unless redundant.

-------------------------------------
STEP 2 — UX IMPROVEMENT DESIGN
-------------------------------------

Upgrade dashboard to be:

- Clean layout
- Sidebar controls
- Multi-tab structure
- Clear visual hierarchy
- Minimal clutter
- Trader-focused summary first

Use Streamlit.

-------------------------------------
STEP 3 — DASHBOARD STRUCTURE
-------------------------------------

Create a professional layout:

Main Tabs:

1) Overview
   - Current Nifty close
   - VIX
   - Predicted Next-Day Range (visual band)
   - Structural Summary (bullish / neutral / bearish bias)
   - Key assertions triggered

2) Positioning
   - OI Heatmap (interactive)
   - Strike concentration chart
   - PCR regime chart

3) Volatility
   - IV skew evolution
   - Term structure
   - IV vs Price overlay

4) Historical Comparison
   - Current vs historical percentile
   - Z-score charts
   - OI migration over time

5) Strategy Builder
   - Dropdown: strategy type
   - Auto-suggest strikes
   - Show payoff chart
   - Show probability of profit
   - Show max loss / max gain

-------------------------------------
STEP 4 — USER EXPERIENCE FEATURES
-------------------------------------

Add:

- Date selector
- Expiry selector (Weekly / Monthly)
- Strike filter slider
- Range auto-calculation toggle
- Regime indicator badge:
    Green → bullish bias
    Red → bearish bias
    Yellow → compression regime

Add tooltips explaining:
- PCR
- Skew
- OI concentration
- Range logic

-------------------------------------
STEP 5 — NEXT-DAY RANGE VISUAL
-------------------------------------

On Overview page:

Overlay predicted range on current price chart:

- Show current spot
- Upper bound
- Lower bound
- Historical average move band

Make it visually intuitive.

-------------------------------------
STEP 6 — STRATEGY BUILDER UPGRADE
-------------------------------------

Enhance strategy builder:

- Auto-adjust strikes based on predicted range
- Suggest:
    - Iron Condor in compression
    - Long Straddle in expansion
    - Credit spreads in skew bias
- Add payoff graph
- Add breakeven calculation

-------------------------------------
STEP 7 — STREAMLIT HOSTING READY
-------------------------------------

Prepare for Streamlit Cloud deployment:

- Add requirements.txt
- Add config.toml if needed
- Ensure no local absolute paths
- Add caching using st.cache_data
- Add error handling for missing files

-------------------------------------
STEP 8 — PERFORMANCE
-------------------------------------

- Cache processed data
- Lazy-load heavy charts
- Avoid recomputation on small UI change

-------------------------------------
STEP 9 — CODE QUALITY
-------------------------------------

- Clean modular structure
- Proper separation:
    dashboard/
    components/
    services/
- Keep logic outside Streamlit UI layer

-------------------------------------
FINAL OBJECTIVE:

Turn this from a research tool into a trader-facing application.

The user should answer in under 30 seconds:

- What is the positioning bias?
- Where is support/resistance?
- What is expected tomorrow’s range?
- Which strategy fits current structure?

Do not simplify analytics.
Improve presentation and usability.